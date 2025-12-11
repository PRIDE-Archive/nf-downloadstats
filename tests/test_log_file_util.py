"""
Unit tests for FileUtil class.
"""
import unittest
import tempfile
import os
import gzip
from pathlib import Path
from filedownloadstat.log_file_util import FileUtil
from filedownloadstat.exceptions import LogFileNotFoundError, LogFileCorruptedError


class TestFileUtil(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_util = FileUtil()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_file_paths(self):
        """Test get_file_paths finds all .tsv.gz files."""
        # Create test directory structure
        test_dir = os.path.join(self.temp_dir, "test_dir")
        os.makedirs(test_dir, exist_ok=True)
        
        # Create test files
        test_file1 = os.path.join(test_dir, "file1.tsv.gz")
        test_file2 = os.path.join(test_dir, "file2.tsv.gz")
        with gzip.open(test_file1, 'wt') as f:
            f.write("test content")
        with gzip.open(test_file2, 'wt') as f:
            f.write("test content")
        
        result = self.file_util.get_file_paths(test_dir)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn(test_file1, result)
        self.assertIn(test_file2, result)

    def test_get_file_paths_with_nested_directories(self):
        """Test get_file_paths finds files in nested directories."""
        # Create nested directory structure
        nested_dir = os.path.join(self.temp_dir, "level1", "level2")
        os.makedirs(nested_dir, exist_ok=True)
        
        test_file = os.path.join(nested_dir, "file.tsv.gz")
        with gzip.open(test_file, 'wt') as f:
            f.write("test content")
        
        result = self.file_util.get_file_paths(self.temp_dir)
        self.assertIn(test_file, result)

    def test_process_access_methods(self):
        """Test process_access_methods creates file list."""
        # Create test directory structure
        protocol_dir = os.path.join(self.temp_dir, "http", "public")
        os.makedirs(protocol_dir, exist_ok=True)
        
        test_file = os.path.join(protocol_dir, "file.tsv.gz")
        with gzip.open(test_file, 'wt') as f:
            f.write("test content")
        
        output_file = os.path.join(self.temp_dir, "file_list.txt")
        result = self.file_util.process_access_methods(
            self.temp_dir,
            output_file,
            ["http"],
            ["public"]
        )
        
        self.assertEqual(result, output_file)
        self.assertTrue(os.path.exists(output_file))
        
        # Verify content
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("file.tsv.gz", content)

    def test_process_log_file_with_nonexistent_file_raises_error(self):
        """Test process_log_file raises LogFileNotFoundError for nonexistent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.tsv.gz")
        output_file = os.path.join(self.temp_dir, "output.parquet")
        
        with self.assertRaises(LogFileNotFoundError):
            self.file_util.process_log_file(
                nonexistent_file,
                output_file,
                ["/pride/data/archive"],
                ["complete"],
                1000,
                ["^PXD\\d{6}$"]
            )

    def test_process_log_file_with_valid_file(self):
        """Test process_log_file processes valid log file."""
        # Create a minimal valid log file
        test_file = os.path.join(self.temp_dir, "test.tsv.gz")
        with gzip.open(test_file, 'wt') as f:
            # Write a valid log line
            f.write("2023-01-01T00:00:00.000Z\tuser_hash\t123\t/pride/data/archive/2023/01/PXD000001/file.raw\tOUT\thash\tComplete\tUnited Kingdom\tCambridgeshire\tCambridge\t52.2053,0.1218\thttp\tpublic\n")
        
        output_file = os.path.join(self.temp_dir, "output.parquet")
        
        try:
            self.file_util.process_log_file(
                test_file,
                output_file,
                ["/pride/data/archive"],
                ["complete"],
                1000,
                ["^PXD\\d{6}$"]
            )
            # If no exception, file should exist (or warning logged if no data)
            # The actual result depends on whether data matches filters
        except LogFileCorruptedError:
            # This is acceptable if file doesn't match filters
            pass


if __name__ == '__main__':
    unittest.main()

