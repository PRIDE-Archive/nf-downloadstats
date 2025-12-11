import os
import logging
from typing import List
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
from scipy.stats import rankdata

from exceptions import (
    ParquetReadError,
    ParquetMergeError,
    AnalysisError
)
from interfaces import IParquetAnalyzer

logger = logging.getLogger(__name__)


class ParquetAnalyzer(IParquetAnalyzer):
    def __init__(self, batch_size: int = 100000) -> None:
        """Initialize with a batch size for processing."""
        self.batch_size: int = int(batch_size)  # Number of rows to process at a time

    def analyze_parquet_files(
        self,
        output_parquet: str,
        project_level_download_counts: str,
        file_level_download_counts: str,
        project_level_yearly_download_counts: str,
        project_level_top_download_counts: str,
        all_data: str
    ) -> None:
        """Processes Parquet files in batches without using Dask."""
        file_iter = pq.ParquetFile(output_parquet).iter_batches(batch_size=self.batch_size,
                                                                columns=["accession", "filename", "year"])

        project_counts = []
        file_counts = []
        yearly_counts = []

        for batch in file_iter:
            df = batch.to_pandas()

            # Aggregate project-level counts
            project_counts.append(df.groupby("accession")["filename"].count().reset_index(name="count"))

            # Aggregate file-level counts
            file_counts.append(df.groupby(["accession", "filename"]).size().reset_index(name="count"))

            # Aggregate yearly counts
            yearly_counts.append(df.groupby(["accession", "year"]).size().reset_index(name="count"))

        # Combine results
        self.persist_project_level_download_counts(pd.concat(project_counts, ignore_index=True),
                                                   project_level_download_counts)
        self.persist_file_level_download_counts(pd.concat(file_counts, ignore_index=True), file_level_download_counts)
        self.persist_project_level_yearly_download_counts(pd.concat(yearly_counts, ignore_index=True),
                                                          project_level_yearly_download_counts)
        self.persist_top_download_counts(output_parquet, project_level_top_download_counts, top_counts=100)

        # Save full dataset incrementally
        self.persist_all_data(output_parquet, all_data)

    def persist_project_level_download_counts(self, df: pd.DataFrame, output_file: str) -> None:
        # Ensure final total count per accession
        df = df.groupby("accession")["count"].sum().reset_index()

        # Calculate percentiles
        df["percentile"] = (rankdata(df["count"], method="average") / len(df) * 100).astype(int)

        # Sort and save
        df.sort_values(by="count", ascending=False).to_json(output_file, orient="records", lines=False)
        logger.info("Project level download counts saved", extra={"output_file": output_file, "record_count": len(df)})

    def persist_file_level_download_counts(self, df: pd.DataFrame, output_file: str) -> None:
        df.to_json(output_file, orient="records", lines=False)
        logger.info("File level download counts saved", extra={"output_file": output_file, "record_count": len(df)})

    def persist_project_level_yearly_download_counts(self, df: pd.DataFrame, output_file: str) -> None:
        # Group by accession and year and sum the counts
        grouped_df = df.groupby(["accession", "year"])["count"].sum().reset_index()

        # Nest yearly counts under each accession
        nested = (
            grouped_df
            .groupby("accession")
            .apply(lambda x: {
                "accession": x["accession"].iloc[0],
                "yearlyDownloads": x[["year", "count"]].to_dict(orient="records")
            })
            .tolist()
        )

        pd.DataFrame(nested).to_json(output_file, orient="records", lines=False)
        logger.info("Project level yearly download counts saved", extra={"output_file": output_file, "record_count": len(nested)})

    def persist_top_download_counts(self, input_parquet: str, output_file: str, top_counts: int = 100) -> None:
        """Processes Parquet file batch-wise to determine top downloads."""
        file_iter = pq.ParquetFile(input_parquet).iter_batches(batch_size=self.batch_size, columns=["accession"])
        counts = {}

        for batch in file_iter:
            df = batch.to_pandas()
            for acc in df["accession"]:
                counts[acc] = counts.get(acc, 0) + 1

        result = pd.DataFrame(list(counts.items()), columns=["accession", "count"])
        top_count_dataset = result.sort_values("count", ascending=False).head(top_counts)
        top_count_dataset.to_json(output_file, orient="records", lines=False)
        logger.info("Top download counts saved", extra={"output_file": output_file, "top_count": len(top_count_dataset)})

    def persist_all_data(self, input_parquet: str, output_file: str) -> None:
        """Reads and saves all data batch-wise to avoid memory issues."""
        file_iter = pq.ParquetFile(input_parquet).iter_batches(batch_size=self.batch_size)

        record_count = 0
        with open(output_file, "w") as f:
            for batch in file_iter:
                df = batch.to_pandas()
                f.write(df.to_json(orient="records", lines=True))  # **Append JSON records batch-wise**
                record_count += len(df)
        logger.info("All data saved", extra={"output_file": output_file, "record_count": record_count})

    def get_all_parquet_files(self, file_list_path: str) -> List[str]:
        """Reads file paths from a text file and validates them as Parquet files."""
        with open(file_list_path, "r") as f:
            file_paths = [line.strip() for line in f.readlines()]

        all_parquet_files = [p for p in file_paths if os.path.isfile(p) and p.endswith(".parquet")]
        if not all_parquet_files:
            logger.warning("No valid Parquet files found", extra={"file_list_path": file_list_path})
        return all_parquet_files

    def merge_parquet_files(self, input_files: str, output_parquet: str) -> None:
        """Merges Parquet files in batches with schema consistency."""
        try:
            all_files = self.get_all_parquet_files(input_files)
            if not all_files:
                raise ParquetMergeError(
                    "No valid Parquet files found to merge",
                    input_files=input_files
                )

            writer = None
            first_schema = None

            for file in all_files:
                file_iter = pq.ParquetFile(file).iter_batches(batch_size=self.batch_size)
                for batch in file_iter:
                    df = batch.to_pandas()

                    if writer is None:
                        first_schema = pa.Table.from_pandas(df).schema  # Capture schema from first batch
                        writer = pq.ParquetWriter(output_parquet, first_schema)

                    table = pa.Table.from_pandas(df, schema=first_schema)  # Ensure schema consistency
                    writer.write_table(table)

            if writer:
                writer.close()
            logger.info("Merged Parquet dataset saved", extra={"output_file": output_parquet, "input_file_count": len(all_files)})
        except (IOError, OSError, pa.ArrowInvalid) as e:
            error = ParquetMergeError(
                f"Failed to merge Parquet files: {str(e)}",
                input_files=input_files,
                original_error=str(e)
            )
            logger.error("Error merging Parquet files", extra={"input_files": input_files, "error": str(e)}, exc_info=True)
            raise error
        except Exception as e:
            error = ParquetMergeError(
                f"Unexpected error merging Parquet files: {str(e)}",
                input_files=input_files,
                original_error=str(e)
            )
            logger.error("Unexpected error merging Parquet files", extra={"input_files": input_files, "error": str(e)}, exc_info=True)
            raise error
