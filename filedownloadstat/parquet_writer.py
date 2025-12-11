import logging
from typing import List, Dict, Any, Optional
import pyarrow.parquet as pq
import pyarrow as pa

from exceptions import (
    ParquetWriteError,
    ValidationError
)
from interfaces import IParquetWriter

logger = logging.getLogger(__name__)


class ParquetWriter(IParquetWriter):
    """
    Write parquet file
    """
    # Define schema with metadata
    schema = pa.schema([
        pa.field('date', pa.date64(), metadata={'description': 'Date that the dataset was downloaded'}),
        pa.field('year', pa.int16(), metadata={'description': 'Year that the dataset was downloaded'}),
        pa.field('month', pa.int8(), metadata={'description': 'Month that the dataset was downloaded'}),
        pa.field('user', pa.string(), metadata={'description': 'Hash representing the user'}),
        pa.field('accession', pa.string(), metadata={'description': 'PRIDE accession started with PXD'}),
        pa.field('filename', pa.string(), metadata={'description': 'Filename of the file downloaded'}),
        pa.field('completed', pa.string(), metadata={'description': 'Check if the file download was completed'}),
        pa.field('country', pa.string(), metadata={'description': 'Country of the file downloaded'}),
        pa.field('method', pa.string(), metadata={'description': 'Download method such as FTP/Aspera/Globus'}),
        pa.field('timestamp', pa.string(), metadata={'description': 'Original timestamp string from the log file'}),
        pa.field('geoip_region_name', pa.string(), metadata={'description': 'GeoIP region name (e.g., state, province)'}),
        pa.field('geoip_city_name', pa.string(), metadata={'description': 'GeoIP city name'}),
        pa.field('geo_location', pa.string(), metadata={'description': 'Geographic location coordinates (latitude,longitude)'}),
    ])

    COMPRESSION = 'snappy'

    def __init__(self, parquet_path: str, write_strategy: str = 'all', batch_size: int = 10000) -> None:
        """
        Initialize ParquetWriter.

        :param parquet_path: Path to the Parquet file/directory.
        :param write_strategy: Writing strategy ('all' or 'batch').
        :param batch_size: Batch size for batch-wise writing.
        """
        if not parquet_path:
            raise ValidationError("parquet_path is required", field="parquet_path")

        self.parquet_path: str = parquet_path
        self.write_strategy: str = write_strategy.lower()
        self.batch_size: int = batch_size
        self.parquet_writer: Optional[pq.ParquetWriter] = None
        self.batch_data: List[Dict[str, Any]] = []

    # METHOD 1
    def write_all(self, data: List[Dict[str, Any]]) -> bool:
        """
        Write parquet file with schema
        :param data: array of data to write
        :return:
        """
        try:
            # Convert data to PyArrow Table
            table = pa.Table.from_pylist(data, schema=self.schema)
            if len(table) > 0:
                # Write to Parquet
                pq.write_to_dataset(
                    table,
                    root_path=self.parquet_path,
                    compression=self.COMPRESSION
                )
                return True
            return False
        except (pa.ArrowInvalid, IOError, OSError) as e:
            error = ParquetWriteError(
                f"Failed to write Parquet file: {self.parquet_path}",
                parquet_path=self.parquet_path,
                original_error=str(e)
            )
            logger.error("Error during write_all", extra={"parquet_path": self.parquet_path, "error": str(e)}, exc_info=True)
            raise error
        except Exception as e:
            error = ParquetWriteError(
                f"Unexpected error writing Parquet file: {self.parquet_path}",
                parquet_path=self.parquet_path,
                original_error=str(e)
            )
            logger.error("Error during write_all", extra={"parquet_path": self.parquet_path, "error": str(e)}, exc_info=True)
            raise error

    # METHOD 2
    def write_batch(self, data: List[Dict[str, Any]]) -> bool:
        """
        Write data in batches to a Parquet file.

        :param data: List of dictionaries representing the data.
        """

        try:
            # Add new data to the current batch
            self.batch_data.extend(data)
            data_written = False

            # If batch size is reached, write the batch
            while len(self.batch_data) >= self.batch_size:
                self._write_current_batch()
                data_written = True
            return data_written

        except (pa.ArrowInvalid, IOError, OSError) as e:
            error = ParquetWriteError(
                f"Failed to write batch to Parquet file: {self.parquet_path}",
                parquet_path=self.parquet_path,
                original_error=str(e)
            )
            logger.error("Error during write_batch", extra={"parquet_path": self.parquet_path, "error": str(e)}, exc_info=True)
            raise error
        except Exception as e:
            error = ParquetWriteError(
                f"Unexpected error writing batch: {self.parquet_path}",
                parquet_path=self.parquet_path,
                original_error=str(e)
            )
            logger.error("Error during write_batch", extra={"parquet_path": self.parquet_path, "error": str(e)}, exc_info=True)
            raise error

    def _write_current_batch(self) -> None:
        """
        Write the current batch to the Parquet file.
        """
        try:
            # Create a RecordBatch from the current batch data
            batch = pa.RecordBatch.from_pylist(self.batch_data[:self.batch_size], schema=self.schema)

            # Initialize the writer lazily
            if self.parquet_writer is None:
                self.parquet_writer = pq.ParquetWriter(self.parquet_path, schema=self.schema,
                                                       compression=self.COMPRESSION)

            # Write the batch
            self.parquet_writer.write_batch(batch)

            # Remove written data from the batch
            self.batch_data = self.batch_data[self.batch_size:]

        except (pa.ArrowInvalid, IOError, OSError) as e:
            error = ParquetWriteError(
                f"Failed to write current batch: {self.parquet_path}",
                parquet_path=self.parquet_path,
                batch_size=len(self.batch_data[:self.batch_size]),
                original_error=str(e)
            )
            logger.error("Error during _write_current_batch", extra={"parquet_path": self.parquet_path, "batch_size": len(self.batch_data[:self.batch_size]), "error": str(e)}, exc_info=True)
            raise error
        except Exception as e:
            error = ParquetWriteError(
                f"Unexpected error writing current batch: {self.parquet_path}",
                parquet_path=self.parquet_path,
                original_error=str(e)
            )
            logger.error("Error during _write_current_batch", extra={"parquet_path": self.parquet_path, "batch_size": len(self.batch_data[:self.batch_size]), "error": str(e)}, exc_info=True)
            raise error

    def finalize(self) -> bool:
        """
        Finalize the writing process.
        Writes any remaining data and closes the writer.
        """
        data_written = False
        try:
            # Write remaining data if any
            if self.batch_data and self.write_strategy == 'batch':
                self._write_current_batch()
                data_written = True

            # Close the writer
            if self.parquet_writer:
                self.parquet_writer.close()
            return data_written
        except (pa.ArrowInvalid, IOError, OSError) as e:
            error = ParquetWriteError(
                f"Failed to finalize Parquet file: {self.parquet_path}",
                parquet_path=self.parquet_path,
                original_error=str(e)
            )
            logger.error("Error during finalize", extra={"parquet_path": self.parquet_path, "error": str(e)}, exc_info=True)
            raise error
        except Exception as e:
            error = ParquetWriteError(
                f"Unexpected error finalizing Parquet file: {self.parquet_path}",
                parquet_path=self.parquet_path,
                original_error=str(e)
            )
            logger.error("Error during finalize", extra={"parquet_path": self.parquet_path, "error": str(e)}, exc_info=True)
            raise error