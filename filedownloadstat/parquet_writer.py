import pyarrow.parquet as pq
import pyarrow as pa


class ParquetWriter:
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

    def __init__(self, parquet_path: str, write_strategy: str = 'all', batch_size: int = 10000):
        """
        Initialize ParquetWriter.

        :param parquet_path: Path to the Parquet file/directory.
        :param write_strategy: Writing strategy ('all' or 'batch').
        :param batch_size: Batch size for batch-wise writing.
        """
        if not parquet_path:
            raise ValueError("parquet_path is required")

        self.parquet_path = parquet_path
        self.write_strategy = write_strategy.lower()
        self.batch_size = batch_size
        self.parquet_writer = None
        self.batch_data = []

    # METHOD 1
    def write_all(self, data):
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
        except Exception as e:
            print(f"Error during write_all: {e}")
            raise

    # METHOD 2
    def write_batch(self, data):
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

        except Exception as e:
            print(f"Error during write_batch: {e}")
            raise

    def _write_current_batch(self):
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

        except Exception as e:
            print(f"Error during _write_current_batch: {e}")
            raise

    def finalize(self):
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
        except Exception as e:
            print(f"Error during finalize: {e}")
            raise