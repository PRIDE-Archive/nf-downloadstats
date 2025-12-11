"""
Integration tests for critical workflows.
"""
import unittest
import tempfile
import os
import gzip
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import date
from pathlib import Path

from filedownloadstat.log_file_parser import LogFileParser
from filedownloadstat.log_file_util import FileUtil
from filedownloadstat.parquet_writer import ParquetWriter
from filedownloadstat.parquet_analyzer import ParquetAnalyzer
from filedownloadstat.parquet_reader import ParquetReader


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration tests for the complete log file processing workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_log.tsv.gz")
        self.parquet_file = os.path.join(self.temp_dir, "output.parquet")
        self._create_test_log_file()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_log_file(self):
        """Create a test log file with valid data."""
        with gzip.open(self.log_file, 'wt') as f:
            # Write valid log lines
            f.write("2023-01-01T00:00:00.000Z\tuser1_hash\t123\t/pride/data/archive/2023/01/PXD000001/file1.raw\tOUT\thash1\tComplete\tUnited Kingdom\tCambridgeshire\tCambridge\t52.2053,0.1218\thttp\tpublic\n")
            f.write("2023-01-02T00:00:00.000Z\tuser2_hash\t456\t/pride/data/archive/2023/01/PXD000001/file2.raw\tOUT\thash2\tComplete\tUnited States\tCalifornia\tSan Francisco\t37.7749,-122.4194\thttp\tpublic\n")
            f.write("2023-01-03T00:00:00.000Z\tuser1_hash\t789\t/pride/data/archive/2023/01/PXD000002/file3.raw\tOUT\thash3\tComplete\tGermany\tBavaria\tMunich\t48.1351,11.5820\thttp\tpublic\n")

    def test_complete_workflow_log_to_parquet(self):
        """Test complete workflow from log file to parquet."""
        # Step 1: Parse log file
        parser = LogFileParser(
            self.log_file,
            resource_list=["/pride/data/archive"],
            completeness_list=["complete"],
            accession_pattern_list=["^PXD\\d{6}$"]
        )
        
        # Step 2: Write to parquet
        writer = ParquetWriter(self.parquet_file, write_strategy='batch', batch_size=10)
        
        batch_count = 0
        for batch in parser.parse_gzipped_tsv(batch_size=10):
            if batch:
                writer.write_batch(batch)
                batch_count += 1
        
        writer.finalize()
        
        # Step 3: Verify parquet file exists and has data
        self.assertTrue(os.path.exists(self.parquet_file))
        
        # Step 4: Read and verify parquet file
        reader = ParquetReader()
        table = reader.read(self.parquet_file)
        self.assertGreater(len(table), 0)
        
        # Verify schema
        self.assertIn('accession', table.column_names)
        self.assertIn('filename', table.column_names)
        self.assertIn('year', table.column_names)

    def test_workflow_parquet_analysis(self):
        """Test workflow for analyzing parquet files."""
        # First create a parquet file
        parser = LogFileParser(
            self.log_file,
            resource_list=["/pride/data/archive"],
            completeness_list=["complete"],
            accession_pattern_list=["^PXD\\d{6}$"]
        )
        
        writer = ParquetWriter(self.parquet_file, write_strategy='batch', batch_size=10)
        for batch in parser.parse_gzipped_tsv(batch_size=10):
            if batch:
                writer.write_batch(batch)
        writer.finalize()
        
        # Now analyze it
        analyzer = ParquetAnalyzer(batch_size=1000)
        output_dir = os.path.join(self.temp_dir, "analysis_output")
        os.makedirs(output_dir, exist_ok=True)
        
        project_counts = os.path.join(output_dir, "project_counts.json")
        file_counts = os.path.join(output_dir, "file_counts.json")
        yearly_counts = os.path.join(output_dir, "yearly_counts.json")
        top_counts = os.path.join(output_dir, "top_counts.json")
        all_data = os.path.join(output_dir, "all_data.json")
        
        analyzer.analyze_parquet_files(
            self.parquet_file,
            project_counts,
            file_counts,
            yearly_counts,
            top_counts,
            all_data
        )
        
        # Verify all output files exist
        self.assertTrue(os.path.exists(project_counts))
        self.assertTrue(os.path.exists(file_counts))
        self.assertTrue(os.path.exists(yearly_counts))
        self.assertTrue(os.path.exists(top_counts))
        self.assertTrue(os.path.exists(all_data))

    def test_workflow_merge_multiple_parquet_files(self):
        """Test workflow for merging multiple parquet files."""
        # Create multiple parquet files
        parquet_files = []
        for i in range(3):
            parser = LogFileParser(
                self.log_file,
                resource_list=["/pride/data/archive"],
                completeness_list=["complete"],
                accession_pattern_list=["^PXD\\d{6}$"]
            )
            
            parquet_file = os.path.join(self.temp_dir, f"file_{i}.parquet")
            writer = ParquetWriter(parquet_file, write_strategy='batch', batch_size=10)
            
            for batch in parser.parse_gzipped_tsv(batch_size=10):
                if batch:
                    writer.write_batch(batch)
            writer.finalize()
            parquet_files.append(parquet_file)
        
        # Merge them
        file_list_path = os.path.join(self.temp_dir, "file_list.txt")
        with open(file_list_path, 'w') as f:
            for pf in parquet_files:
                f.write(f"{pf}\n")
        
        merged_file = os.path.join(self.temp_dir, "merged.parquet")
        analyzer = ParquetAnalyzer()
        analyzer.merge_parquet_files(file_list_path, merged_file)
        
        # Verify merged file exists and has data
        self.assertTrue(os.path.exists(merged_file))
        reader = ParquetReader()
        table = reader.read(merged_file)
        self.assertGreater(len(table), 0)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling across modules."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_error_propagation_log_to_parquet(self):
        """Test that errors propagate correctly through the workflow."""
        from filedownloadstat.exceptions import LogFileNotFoundError
        
        file_util = FileUtil()
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.tsv.gz")
        output_file = os.path.join(self.temp_dir, "output.parquet")
        
        with self.assertRaises(LogFileNotFoundError):
            file_util.process_log_file(
                nonexistent_file,
                output_file,
                ["/pride/data/archive"],
                ["complete"],
                1000,
                ["^PXD\\d{6}$"]
            )

    def test_recovery_from_corrupted_file(self):
        """Test that corrupted files are handled gracefully."""
        # Create a corrupted gzip file
        corrupted_file = os.path.join(self.temp_dir, "corrupted.tsv.gz")
        with open(corrupted_file, 'wb') as f:
            f.write(b"not a valid gzip file")
        
        parser = LogFileParser(
            corrupted_file,
            resource_list=["/pride/data/archive"],
            completeness_list=["complete"],
            accession_pattern_list=["^PXD\\d{6}$"]
        )
        
        # Should not raise exception, but yield empty batches
        batches = list(parser.parse_gzipped_tsv(batch_size=10))
        # Should handle gracefully without crashing
        self.assertIsInstance(batches, list)


if __name__ == '__main__':
    unittest.main()

