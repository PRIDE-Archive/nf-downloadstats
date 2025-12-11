import gzip
import os
import sys
import logging
from typing import List, Optional, Callable
from pathlib import Path

from log_file_parser import LogFileParser
from parquet_writer import ParquetWriter
from exceptions import (
    LogFileNotFoundError,
    ParquetWriteError,
    LogFileCorruptedError
)
from interfaces import IFileUtil

logger = logging.getLogger(__name__)


class FileUtil(IFileUtil):
    """
    File utility class for processing log files.
    Supports dependency injection for better testability.
    """

    def __init__(
        self,
        parser_factory: Optional[Callable] = None,
        writer_factory: Optional[Callable] = None
    ) -> None:
        """
        Initialize FileUtil.
        
        Args:
            parser_factory: Optional factory function for creating LogFileParser instances
            writer_factory: Optional factory function for creating ParquetWriter instances
        """
        self._parser_factory = parser_factory or LogFileParser
        self._writer_factory = writer_factory or ParquetWriter

    def get_file_paths(self, root_dir: str) -> List[str]:
        """
        Traverse the directory tree and retrieve all file paths.
        Handles variable folder depth safely using pathlib.
        :param root_dir: Root directory to start traversal.
        :return: List of file paths.
        """
        root_path = Path(root_dir)
        return [str(file) for file in root_path.rglob("*.tsv.gz")]


    def process_access_methods(
        self,
        root_directory: str,
        file_paths_list: str,
        protocols: List[str],
        public_list: List[str]
    ) -> str:
        """
        Process logs and generate Parquet files for each file in the specified access method directories.
        """

        file_metadata = []

        for protocol in protocols:
            for public_private in public_list:
                method_directory = Path(root_directory) / protocol.strip() / public_private.strip()
                files = self.get_file_paths(str(method_directory))

                for file_path in files:
                    file_path_obj = Path(file_path)

                    # Retrieve file size
                    file_size = file_path_obj.stat().st_size

                    # Count number of lines in the gzipped file
                    # line_count = self.count_lines_in_gz(file_path)

                    file_info = {
                        "path": file_path,
                        "filename": file_path_obj.name,
                        "size": file_size,
                        "protocol": protocol,
                    }
                    file_metadata.append(file_info)

            # Write metadata to the output file
        with open(file_paths_list, "w") as f:
            for metadata in file_metadata:
                f.write(
                    f"{metadata['path']}\t{metadata['filename']}\t{metadata['size']}\t{metadata['protocol']}\n"
                )

        logger.info("File metadata written", extra={"output_file": file_paths_list, "file_count": len(file_metadata)})
        return file_paths_list

    def process_log_file(
        self,
        file_path: str,
        parquet_output_file: str,
        resource_list: List[str],
        completeness_list: List[str],
        batch_size: int,
        accession_pattern_list: List[str]
    ) -> None:
        data_written = False
        try:
            logger.info("Parsing log file started", extra={"file_path": file_path, "output_file": parquet_output_file})

            if not os.path.exists(file_path):
                raise LogFileNotFoundError(
                    f"Input file does not exist: {file_path}",
                    file_path=file_path
                )

            lp = self._parser_factory(file_path, resource_list, completeness_list, accession_pattern_list)
            writer = self._writer_factory(parquet_path=parquet_output_file, write_strategy='batch', batch_size=batch_size)

            for batch in lp.parse_gzipped_tsv(batch_size):
                if writer.write_batch(batch):
                    data_written = True

            # Finalize and check if any data was written
            if writer.finalize():
                data_written = True

            if data_written:
                logger.info("Parquet file written successfully", extra={"file_path": file_path, "output_file": parquet_output_file})
            else:
                logger.warning("No data found to write", extra={"file_path": file_path})
        except LogFileNotFoundError:
            # Re-raise as-is - this is a fatal error
            raise
        except (LogFileCorruptedError, ParquetWriteError) as e:
            # Re-raise specific errors
            logger.error("Error while processing file", extra={"file_path": file_path, "error": str(e)}, exc_info=True)
            raise
        except Exception as e:
            # Wrap unexpected errors
            error = LogFileCorruptedError(
                f"Unexpected error processing file: {file_path}",
                file_path=file_path,
                original_error=str(e)
            )
            logger.error("Error while processing file", extra={"file_path": file_path, "error": str(e)}, exc_info=True)
            raise error
