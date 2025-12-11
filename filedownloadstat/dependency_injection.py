"""
Simple dependency injection container for better testability and flexibility.
"""
from typing import Dict, Type, TypeVar, Callable, Any, Optional
from interfaces import (
    ILogParser,
    IParquetWriter,
    IParquetReader,
    IParquetAnalyzer,
    IFileUtil,
    ISlackPusher,
    IReportGenerator
)

T = TypeVar('T')


class DIContainer:
    """
    Simple dependency injection container.
    Allows registering and resolving dependencies for better testability.
    """
    
    def __init__(self) -> None:
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
    
    def register(self, interface: Type[T], implementation: T) -> None:
        """Register a singleton instance."""
        self._services[interface] = implementation
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for creating instances."""
        self._factories[interface] = factory
    
    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a dependency.
        
        Args:
            interface: The interface/type to resolve
            
        Returns:
            An instance of the requested type
            
        Raises:
            ValueError: If the dependency is not registered
        """
        # Check for singleton
        if interface in self._services:
            return self._services[interface]
        
        # Check for factory
        if interface in self._factories:
            return self._factories[interface]()
        
        raise ValueError(f"Dependency not registered: {interface}")
    
    def register_defaults(self) -> None:
        """Register default implementations."""
        from log_file_parser import LogFileParser
        from parquet_writer import ParquetWriter
        from parquet_reader import ParquetReader
        from parquet_analyzer import ParquetAnalyzer
        from log_file_util import FileUtil
        from slack_pusher import SlackPusher
        from report_util import Report
        
        # Register factories for classes that need parameters
        self.register_factory(ILogParser, lambda: LogFileParser)
        self.register_factory(IParquetWriter, lambda: ParquetWriter)
        self.register_factory(IParquetReader, lambda: ParquetReader)
        self.register_factory(IParquetAnalyzer, lambda: ParquetAnalyzer)
        self.register_factory(IFileUtil, lambda: FileUtil)
        self.register_factory(ISlackPusher, lambda: SlackPusher)
        self.register_factory(IReportGenerator, lambda: Report)


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get or create the global DI container."""
    global _container
    if _container is None:
        _container = DIContainer()
        _container.register_defaults()
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    _container = None

