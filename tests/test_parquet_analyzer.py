"""
Unit tests for ParquetAnalyzer class.
"""
import unittest
import tempfile
import os
import json
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import date
from filedownloadstat.parquet_analyzer import ParquetAnalyzer
from filedownloadstat.exceptions import ParquetMergeError


class TestParquetAnalyzer(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_parquet_path = os.path.join(self.temp_dir, "test.parquet")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        self._create_test_parquet_file()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_parquet_file(self):
        """Create a test parquet file with sample data."""
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
                "user": "user1",
                "accession": "PXD000001",
                "filename": "file1.raw",
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
                "user": "user2",
                "accession": "PXD000001",
                "filename": "file2.raw",
                "completed": "complete",
                "country": "United States",
                "method": "ftp",
                "timestamp": "2023-01-02T00:00:00.000Z",
                "geoip_region_name": "California",
                "geoip_city_name": "San Francisco",
                "geo_location": "37.7749,-122.4194"
            },
            {
                "date": date(2023, 2, 1),
                "year": 2023,
                "month": 2,
                "user": "user1",
                "accession": "PXD000002",
                "filename": "file3.raw",
                "completed": "complete",
                "country": "United Kingdom",
                "method": "http",
                "timestamp": "2023-02-01T00:00:00.000Z",
                "geoip_region_name": "Cambridgeshire",
                "geoip_city_name": "Cambridge",
                "geo_location": "52.2053,0.1218"
            }
        ]
        
        table = pa.Table.from_pylist(data, schema=schema)
        pq.write_table(table, self.test_parquet_path)

    def test_init(self):
        """Test ParquetAnalyzer initialization."""
        analyzer = ParquetAnalyzer()
        self.assertEqual(analyzer.batch_size, 100000)

    def test_init_with_custom_batch_size(self):
        """Test ParquetAnalyzer initialization with custom batch size."""
        analyzer = ParquetAnalyzer(batch_size=50000)
        self.assertEqual(analyzer.batch_size, 50000)

    def test_persist_project_level_download_counts(self):
        """Test persist_project_level_download_counts."""
        analyzer = ParquetAnalyzer()
        df = pd.DataFrame({
            'accession': ['PXD000001', 'PXD000001', 'PXD000002'],
            'count': [1, 1, 1]
        })
        output_file = os.path.join(self.output_dir, "project_counts.json")
        analyzer.persist_project_level_download_counts(df, output_file)
        self.assertTrue(os.path.exists(output_file))
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertTrue(len(data) > 0)

    def test_persist_file_level_download_counts(self):
        """Test persist_file_level_download_counts."""
        analyzer = ParquetAnalyzer()
        df = pd.DataFrame({
            'accession': ['PXD000001', 'PXD000001'],
            'filename': ['file1.raw', 'file2.raw'],
            'count': [1, 1]
        })
        output_file = os.path.join(self.output_dir, "file_counts.json")
        analyzer.persist_file_level_download_counts(df, output_file)
        self.assertTrue(os.path.exists(output_file))

    def test_persist_project_level_yearly_download_counts(self):
        """Test persist_project_level_yearly_download_counts."""
        analyzer = ParquetAnalyzer()
        df = pd.DataFrame({
            'accession': ['PXD000001', 'PXD000001', 'PXD000002'],
            'year': [2023, 2023, 2023],
            'count': [1, 1, 1]
        })
        output_file = os.path.join(self.output_dir, "yearly_counts.json")
        analyzer.persist_project_level_yearly_download_counts(df, output_file)
        self.assertTrue(os.path.exists(output_file))

    def test_persist_top_download_counts(self):
        """Test persist_top_download_counts."""
        analyzer = ParquetAnalyzer()
        output_file = os.path.join(self.output_dir, "top_counts.json")
        analyzer.persist_top_download_counts(self.test_parquet_path, output_file, top_counts=10)
        self.assertTrue(os.path.exists(output_file))

    def test_persist_all_data(self):
        """Test persist_all_data."""
        analyzer = ParquetAnalyzer()
        output_file = os.path.join(self.output_dir, "all_data.json")
        analyzer.persist_all_data(self.test_parquet_path, output_file)
        self.assertTrue(os.path.exists(output_file))

    def test_get_all_parquet_files(self):
        """Test get_all_parquet_files."""
        analyzer = ParquetAnalyzer()
        file_list_path = os.path.join(self.temp_dir, "file_list.txt")
        with open(file_list_path, 'w') as f:
            f.write(f"{self.test_parquet_path}\n")
        
        result = analyzer.get_all_parquet_files(file_list_path)
        self.assertIsInstance(result, list)
        self.assertIn(self.test_parquet_path, result)

    def test_get_all_parquet_files_with_invalid_files(self):
        """Test get_all_parquet_files filters invalid files."""
        analyzer = ParquetAnalyzer()
        file_list_path = os.path.join(self.temp_dir, "file_list.txt")
        with open(file_list_path, 'w') as f:
            f.write(f"{self.test_parquet_path}\n")
            f.write("/nonexistent/file.parquet\n")
            f.write("/nonexistent/file.txt\n")
        
        result = analyzer.get_all_parquet_files(file_list_path)
        self.assertIsInstance(result, list)
        self.assertIn(self.test_parquet_path, result)
        self.assertEqual(len(result), 1)

    def test_merge_parquet_files(self):
        """Test merge_parquet_files."""
        analyzer = ParquetAnalyzer()
        # Create second parquet file
        second_file = os.path.join(self.temp_dir, "test2.parquet")
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
        data = [{
            "date": date(2023, 3, 1),
            "year": 2023,
            "month": 3,
            "user": "user3",
            "accession": "PXD000003",
            "filename": "file4.raw",
            "completed": "complete",
            "country": "Germany",
            "method": "http",
            "timestamp": "2023-03-01T00:00:00.000Z",
            "geoip_region_name": "Bavaria",
            "geoip_city_name": "Munich",
            "geo_location": "48.1351,11.5820"
        }]
        table = pa.Table.from_pylist(data, schema=schema)
        pq.write_table(table, second_file)
        
        file_list_path = os.path.join(self.temp_dir, "file_list.txt")
        with open(file_list_path, 'w') as f:
            f.write(f"{self.test_parquet_path}\n")
            f.write(f"{second_file}\n")
        
        output_file = os.path.join(self.output_dir, "merged.parquet")
        analyzer.merge_parquet_files(file_list_path, output_file)
        self.assertTrue(os.path.exists(output_file))

    def test_merge_parquet_files_with_no_files_raises_error(self):
        """Test merge_parquet_files raises ParquetMergeError when no files found."""
        analyzer = ParquetAnalyzer()
        file_list_path = os.path.join(self.temp_dir, "empty_list.txt")
        with open(file_list_path, 'w') as f:
            f.write("/nonexistent/file.parquet\n")
        
        output_file = os.path.join(self.output_dir, "merged.parquet")
        with self.assertRaises(ParquetMergeError):
            analyzer.merge_parquet_files(file_list_path, output_file)


if __name__ == '__main__':
    unittest.main()

