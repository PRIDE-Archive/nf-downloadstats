"""
Unit tests for custom exception classes.
"""
import unittest
from filedownloadstat.exceptions import (
    FileDownloadStatError,
    LogFileError,
    LogFileParseError,
    LogFileCorruptedError,
    LogFileNotFoundError,
    ParquetError,
    ParquetWriteError,
    ParquetReadError,
    ParquetMergeError,
    SlackPushError,
    ValidationError,
    ConfigurationError
)


class TestExceptions(unittest.TestCase):

    def test_file_download_stat_error(self):
        """Test FileDownloadStatError base exception."""
        error = FileDownloadStatError("Test error")
        self.assertEqual(str(error), "Test error")
        self.assertIsInstance(error, Exception)

    def test_log_file_error_inheritance(self):
        """Test LogFileError inheritance."""
        error = LogFileError("Test error")
        self.assertIsInstance(error, FileDownloadStatError)

    def test_log_file_parse_error(self):
        """Test LogFileParseError with context."""
        error = LogFileParseError(
            "Parse error",
            file_path="/test/file.log",
            line_no=42,
            row_data=["col1", "col2"]
        )
        self.assertEqual(error.file_path, "/test/file.log")
        self.assertEqual(error.line_no, 42)
        self.assertEqual(error.row_data, ["col1", "col2"])

    def test_log_file_corrupted_error(self):
        """Test LogFileCorruptedError with context."""
        error = LogFileCorruptedError(
            "Corrupted file",
            file_path="/test/file.log",
            original_error="IOError"
        )
        self.assertEqual(error.file_path, "/test/file.log")
        self.assertEqual(error.context["original_error"], "IOError")

    def test_log_file_not_found_error(self):
        """Test LogFileNotFoundError with context."""
        error = LogFileNotFoundError(
            "File not found",
            file_path="/test/file.log"
        )
        self.assertEqual(error.file_path, "/test/file.log")

    def test_parquet_error_inheritance(self):
        """Test ParquetError inheritance."""
        error = ParquetError("Test error")
        self.assertIsInstance(error, FileDownloadStatError)

    def test_parquet_write_error(self):
        """Test ParquetWriteError with context."""
        error = ParquetWriteError(
            "Write error",
            parquet_path="/test/file.parquet",
            original_error="IOError"
        )
        self.assertEqual(error.parquet_path, "/test/file.parquet")
        self.assertEqual(error.context["original_error"], "IOError")

    def test_parquet_read_error(self):
        """Test ParquetReadError with context."""
        error = ParquetReadError(
            "Read error",
            parquet_path="/test/file.parquet"
        )
        self.assertEqual(error.parquet_path, "/test/file.parquet")

    def test_parquet_merge_error(self):
        """Test ParquetMergeError with context."""
        error = ParquetMergeError(
            "Merge error",
            input_files=["/test/file1.parquet", "/test/file2.parquet"]
        )
        self.assertEqual(len(error.input_files), 2)

    def test_slack_push_error(self):
        """Test SlackPushError with context."""
        error = SlackPushError(
            "Push error",
            report_file="/test/report.html",
            status_code=400
        )
        self.assertEqual(error.report_file, "/test/report.html")
        self.assertEqual(error.status_code, 400)

    def test_validation_error(self):
        """Test ValidationError with context."""
        error = ValidationError(
            "Validation error",
            field="parquet_path",
            value=None
        )
        self.assertEqual(error.field, "parquet_path")
        self.assertEqual(error.value, None)

    def test_configuration_error(self):
        """Test ConfigurationError with context."""
        error = ConfigurationError(
            "Config error",
            config_key="webhook_url"
        )
        self.assertEqual(error.config_key, "webhook_url")


if __name__ == '__main__':
    unittest.main()

