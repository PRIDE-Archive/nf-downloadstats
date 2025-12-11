"""
Custom exception classes for the file download statistics pipeline.

This module provides structured error types for better error handling
and recovery strategies across the application.
"""


class FileDownloadStatError(Exception):
    """Base exception for all file download statistics errors."""
    pass


class LogFileError(FileDownloadStatError):
    """Base exception for log file processing errors."""
    pass


class LogFileParseError(LogFileError):
    """Raised when log file parsing fails."""
    
    def __init__(self, message: str, file_path: str = None, line_no: int = None, **kwargs):
        super().__init__(message)
        self.file_path = file_path
        self.line_no = line_no
        self.context = kwargs


class LogFileCorruptedError(LogFileError):
    """Raised when a log file is corrupted or unreadable."""
    
    def __init__(self, message: str, file_path: str = None, **kwargs):
        super().__init__(message)
        self.file_path = file_path
        self.context = kwargs


class LogFileNotFoundError(LogFileError):
    """Raised when a log file cannot be found."""
    
    def __init__(self, message: str, file_path: str = None, **kwargs):
        super().__init__(message)
        self.file_path = file_path
        self.context = kwargs


class ParquetError(FileDownloadStatError):
    """Base exception for Parquet file operations."""
    pass


class ParquetWriteError(ParquetError):
    """Raised when writing to Parquet file fails."""
    
    def __init__(self, message: str, parquet_path: str = None, **kwargs):
        super().__init__(message)
        self.parquet_path = parquet_path
        self.context = kwargs


class ParquetReadError(ParquetError):
    """Raised when reading from Parquet file fails."""
    
    def __init__(self, message: str, parquet_path: str = None, **kwargs):
        super().__init__(message)
        self.parquet_path = parquet_path
        self.context = kwargs


class ParquetSchemaError(ParquetError):
    """Raised when Parquet schema validation fails."""
    
    def __init__(self, message: str, expected_schema: str = None, actual_schema: str = None, **kwargs):
        super().__init__(message)
        self.expected_schema = expected_schema
        self.actual_schema = actual_schema
        self.context = kwargs


class ParquetMergeError(ParquetError):
    """Raised when merging Parquet files fails."""
    
    def __init__(self, message: str, input_files: list = None, **kwargs):
        super().__init__(message)
        self.input_files = input_files
        self.context = kwargs


class AnalysisError(FileDownloadStatError):
    """Base exception for data analysis errors."""
    pass


class ReportGenerationError(FileDownloadStatError):
    """Raised when report generation fails."""
    
    def __init__(self, message: str, template_path: str = None, output_path: str = None, **kwargs):
        super().__init__(message)
        self.template_path = template_path
        self.output_path = output_path
        self.context = kwargs


class SlackPushError(FileDownloadStatError):
    """Raised when pushing to Slack fails."""
    
    def __init__(self, message: str, report_file: str = None, status_code: int = None, **kwargs):
        super().__init__(message)
        self.report_file = report_file
        self.status_code = status_code
        self.context = kwargs


class ConfigurationError(FileDownloadStatError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message)
        self.config_key = config_key
        self.context = kwargs


class ValidationError(FileDownloadStatError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: any = None, **kwargs):
        super().__init__(message)
        self.field = field
        self.value = value
        self.context = kwargs

