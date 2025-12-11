"""
Abstract base classes and interfaces for dependency injection and extensibility.
"""
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional, List
from pathlib import Path


class ILogParser(ABC):
    """Interface for log file parsers."""
    
    @abstractmethod
    def parse_gzipped_tsv(self, batch_size: int) -> Iterator[List[Dict[str, Any]]]:
        """Parse gzipped TSV file and yield batches of parsed data."""
        pass
    
    @abstractmethod
    def parse_row(self, row: List[str], line_no: int) -> Optional[Dict[str, Any]]:
        """Parse a single row and return a dictionary or None."""
        pass


class IParquetWriter(ABC):
    """Interface for Parquet file writers."""
    
    @abstractmethod
    def write_all(self, data: List[Dict[str, Any]]) -> bool:
        """Write all data to Parquet file."""
        pass
    
    @abstractmethod
    def write_batch(self, data: List[Dict[str, Any]]) -> bool:
        """Write a batch of data to Parquet file."""
        pass
    
    @abstractmethod
    def finalize(self) -> bool:
        """Finalize writing and close the file."""
        pass


class IParquetReader(ABC):
    """Interface for Parquet file readers."""
    
    @abstractmethod
    def read(self, parquet_path: Path) -> Any:
        """Read a Parquet file and return the data."""
        pass


class IParquetAnalyzer(ABC):
    """Interface for Parquet file analysis."""
    
    @abstractmethod
    def analyze_parquet_files(
        self,
        output_parquet: Path,
        project_level_download_counts: Path,
        file_level_download_counts: Path,
        project_level_yearly_download_counts: Path,
        project_level_top_download_counts: Path,
        all_data: Path
    ) -> None:
        """Analyze parquet files and generate statistics."""
        pass
    
    @abstractmethod
    def merge_parquet_files(self, input_files: Path, output_parquet: Path) -> None:
        """Merge multiple parquet files into one."""
        pass


class IFileUtil(ABC):
    """Interface for file utility operations."""
    
    @abstractmethod
    def get_file_paths(self, root_dir: Path) -> List[str]:
        """Get all file paths from a directory."""
        pass
    
    @abstractmethod
    def process_access_methods(
        self,
        root_directory: str,
        file_paths_list: str,
        protocols: List[str],
        public_list: List[str]
    ) -> str:
        """Process access methods and generate file list."""
        pass
    
    @abstractmethod
    def process_log_file(
        self,
        file_path: str,
        parquet_output_file: str,
        resource_list: List[str],
        completeness_list: List[str],
        batch_size: int,
        accession_pattern_list: List[str]
    ) -> None:
        """Process a log file and convert to Parquet."""
        pass


class ISlackPusher(ABC):
    """Interface for Slack notification service."""
    
    @abstractmethod
    def push_report(self, report_file: str, title: Optional[str] = None) -> bool:
        """Push a report to Slack."""
        pass


class IReportGenerator(ABC):
    """Interface for report generation."""
    
    @abstractmethod
    def generate_report(self, template_path: Path, output: Path) -> None:
        """Generate a report from a template."""
        pass

