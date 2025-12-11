"""
Unit tests for ParquetReader class.
"""
import unittest
import tempfile
import os
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import date
from filedownloadstat.parquet_reader import ParquetReader
from filedownloadstat.exceptions import ParquetReadError, ValidationError


class TestParquetReader(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_parquet_path = os.path.join(self.temp_dir, "test.parquet")
        self._create_test_parquet_file()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_parquet_file(self):
        """Create a test parquet file."""
        schema = pa.schema([
            pa.field('date', pa.date64()),
            pa.field('year', pa.int16()),
            pa.field('month', pa.int8()),
            pa.field('user', pa.string()),
            pa.field('accession', pa.string()),
            pa.field('filename', pa.string()),
            pa.field('completed', pa.string()),
            pa.field('country', pa.string()),
            pa.field('method', pa.string()),
            pa.field('timestamp', pa.string()),
            pa.field('geoip_region_name', pa.string()),
            pa.field('geoip_city_name', pa.string()),
            pa.field('geo_location', pa.string()),
        ])
        
        data = [
            {
                "date": date(2023, 1, 1),
                "year": 2023,
                "month": 1,
                "user": "test_user",
                "accession": "PXD000001",
                "filename": "test.raw",
                "completed": "complete",
                "country": "United Kingdom",
                "method": "http",
                "timestamp": "2023-01-01T00:00:00.000Z",
                "geoip_region_name": "Cambridgeshire",
                "geoip_city_name": "Cambridge",
                "geo_location": "52.2053,0.1218"
            }
        ]
        
        table = pa.Table.from_pylist(data, schema=schema)
        pq.write_table(table, self.test_parquet_path)

    def test_init(self):
        """Test ParquetReader initialization."""
        reader = ParquetReader(self.test_parquet_path)
        self.assertEqual(reader.parquet_path, self.test_parquet_path)

    def test_read_valid_file(self):
        """Test reading a valid parquet file."""
        reader = ParquetReader(self.test_parquet_path)
        result = reader.read(self.test_parquet_path)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, pa.Table)
        self.assertEqual(len(result), 1)

    def test_read_none_path_raises_validation_error(self):
        """Test read with None path raises ValidationError."""
        reader = ParquetReader()
        with self.assertRaises(ValidationError):
            reader.read(None)

    def test_read_nonexistent_file_raises_parquet_read_error(self):
        """Test read with nonexistent file raises ParquetReadError."""
        reader = ParquetReader()
        with self.assertRaises(ParquetReadError):
            reader.read("/nonexistent/path/file.parquet")


if __name__ == '__main__':
    unittest.main()

