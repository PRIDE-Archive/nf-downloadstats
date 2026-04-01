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
        """Processes Parquet files in a single pass with batch-wise aggregation and JSON export."""
        parquet_file = pq.ParquetFile(output_parquet)

        project_counts = []
        file_counts = []
        yearly_counts = []

        # Single pass: aggregate stats and write all_data JSON simultaneously
        first_batch = True
        all_data_record_count = 0
        with open(all_data, "w") as all_data_f:
            all_data_f.write("[")
            for batch in parquet_file.iter_batches(batch_size=self.batch_size):
                df = batch.to_pandas()

                # Aggregate project-level counts
                project_counts.append(df.groupby("accession").size().reset_index(name="count"))

                # Aggregate file-level counts
                file_counts.append(df.groupby(["accession", "filename"]).size().reset_index(name="count"))

                # Aggregate yearly counts
                yearly_counts.append(df.groupby(["accession", "year"]).size().reset_index(name="count"))

                # Write all_data JSON incrementally
                json_str = df.to_json(orient="records")
                json_str = json_str[1:-1]  # Strip outer [ ]
                if json_str:
                    if not first_batch:
                        all_data_f.write(",")
                    all_data_f.write(json_str)
                    first_batch = False
                all_data_record_count += len(df)

            all_data_f.write("]")
        logger.info("All data saved", extra={"output_file": all_data, "record_count": all_data_record_count})

        # Combine and re-aggregate across batches
        project_df = pd.concat(project_counts, ignore_index=True).groupby("accession")["count"].sum().reset_index()
        file_df = pd.concat(file_counts, ignore_index=True).groupby(["accession", "filename"])["count"].sum().reset_index()
        yearly_df = pd.concat(yearly_counts, ignore_index=True).groupby(["accession", "year"])["count"].sum().reset_index()

        # Persist results
        self.persist_project_level_download_counts(project_df, project_level_download_counts)
        self.persist_file_level_download_counts(file_df, file_level_download_counts)
        self.persist_project_level_yearly_download_counts(yearly_df, project_level_yearly_download_counts)

        # Top downloads derived from already-computed project counts (no extra parquet read)
        top_df = project_df.sort_values("count", ascending=False).head(100)
        top_df.to_json(project_level_top_download_counts, orient="records", lines=False)
        logger.info("Top download counts saved", extra={"output_file": project_level_top_download_counts, "top_count": len(top_df)})

    def persist_project_level_download_counts(self, df: pd.DataFrame, output_file: str) -> None:
        # Calculate percentiles
        df["percentile"] = (rankdata(df["count"], method="average") / len(df) * 100).astype(int)

        # Sort and save
        df.sort_values(by="count", ascending=False).to_json(output_file, orient="records", lines=False)
        logger.info("Project level download counts saved", extra={"output_file": output_file, "record_count": len(df)})

    def persist_file_level_download_counts(self, df: pd.DataFrame, output_file: str) -> None:
        df.to_json(output_file, orient="records", lines=False)
        logger.info("File level download counts saved", extra={"output_file": output_file, "record_count": len(df)})

    def persist_project_level_yearly_download_counts(self, df: pd.DataFrame, output_file: str) -> None:
        # Nest yearly counts under each accession
        nested = (
            df
            .groupby("accession")
            .apply(lambda x: {
                "accession": x["accession"].iloc[0],
                "yearlyDownloads": x[["year", "count"]].to_dict(orient="records")
            })
            .tolist()
        )

        pd.DataFrame(nested).to_json(output_file, orient="records", lines=False)
        logger.info("Project level yearly download counts saved", extra={"output_file": output_file, "record_count": len(nested)})

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
