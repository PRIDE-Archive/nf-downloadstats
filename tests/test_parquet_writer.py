"""
Unit tests for ParquetWriter class.
"""
import unittest
import tempfile
import os
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import date
from filedownloadstat.parquet_writer import ParquetWriter
from filedownloadstat.exceptions import ParquetWriteError, ValidationError


class TestParquetWriter(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_parquet_path = os.path.join(self.temp_dir, "test.parquet")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_with_valid_path(self):
        """Test ParquetWriter initialization with valid path."""
        writer = ParquetWriter(self.test_parquet_path)
        self.assertEqual(writer.parquet_path, self.test_parquet_path)
        self.assertEqual(writer.write_strategy, 'all')
        self.assertEqual(writer.batch_size, 10000)

    def test_init_with_invalid_path(self):
        """Test ParquetWriter initialization with empty path raises ValidationError."""
        with self.assertRaises(ValidationError):
            ParquetWriter("")

    def test_init_with_custom_strategy(self):
        """Test ParquetWriter initialization with custom strategy."""
        writer = ParquetWriter(self.test_parquet_path, write_strategy='batch', batch_size=5000)
        self.assertEqual(writer.write_strategy, 'batch')
        self.assertEqual(writer.batch_size, 5000)

    def test_write_all_with_valid_data(self):
        """Test write_all with valid data."""
        writer = ParquetWriter(self.test_parquet_path)
        test_data = [
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
        result = writer.write_all(test_data)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_parquet_path))

    def test_write_all_with_empty_data(self):
        """Test write_all with empty data returns False."""
        writer = ParquetWriter(self.test_parquet_path)
        result = writer.write_all([])
        self.assertFalse(result)

    def test_write_batch(self):
        """Test write_batch method."""
        writer = ParquetWriter(self.test_parquet_path, write_strategy='batch', batch_size=2)
        test_data = [
            {
                "date": date(2023, 1, 1),
                "year": 2023,
                "month": 1,
                "user": "test_user1",
                "accession": "PXD000001",
                "filename": "test1.raw",
                "completed": "complete",
                "country": "United Kingdom",
                "method": "http",
                "timestamp": "2023-01-01T00:00:00.000Z",
                "geoip_region_name": "Cambridgeshire",
                "geoip_city_name": "Cambridge",
                "geo_location": "52.2053,0.1218"
            },
            {
                "date": date(2023, 1, 2),
                "year": 2023,
                "month": 1,
                "user": "test_user2",
                "accession": "PXD000002",
                "filename": "test2.raw",
                "completed": "complete",
                "country": "United States",
                "method": "ftp",
                "timestamp": "2023-01-02T00:00:00.000Z",
                "geoip_region_name": "California",
                "geoip_city_name": "San Francisco",
                "geo_location": "37.7749,-122.4194"
            }
        ]
        result = writer.write_batch(test_data)
        self.assertTrue(result)
        # Finalize to write remaining data
        writer.finalize()
        self.assertTrue(os.path.exists(self.test_parquet_path))

    def test_finalize(self):
        """Test finalize method."""
        writer = ParquetWriter(self.test_parquet_path, write_strategy='batch', batch_size=10)
        test_data = [
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
        writer.write_batch(test_data)
        result = writer.finalize()
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_parquet_path))

    def test_write_all_raises_on_invalid_directory(self):
        """Test write_all raises ParquetWriteError on invalid directory."""
        writer = ParquetWriter("/invalid/path/test.parquet")
        test_data = [
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
        with self.assertRaises(ParquetWriteError):
            writer.write_all(test_data)


if __name__ == '__main__':
    unittest.main()

