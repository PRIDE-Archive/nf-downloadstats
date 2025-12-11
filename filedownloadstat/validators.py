"""
Input validation module using Pydantic for type-safe data validation.
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from exceptions import ValidationError, ConfigurationError


class LogFileConfig(BaseModel):
    """Configuration for log file processing."""
    file_path: Path = Field(..., description="Path to the log file")
    resource_list: List[str] = Field(..., min_items=1, description="List of resource identifiers")
    completeness_list: List[str] = Field(..., min_items=1, description="List of completeness statuses")
    batch_size: int = Field(..., gt=0, description="Batch size for processing")
    accession_pattern_list: List[str] = Field(..., min_items=1, description="List of accession patterns")

    @validator('file_path')
    def file_path_must_exist(cls, v):
        if not v.exists():
            raise ValidationError(f"File does not exist: {v}", field="file_path", value=str(v))
        return v

    @validator('accession_pattern_list')
    def validate_regex_patterns(cls, v):
        import re
        for pattern in v:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValidationError(
                    f"Invalid regex pattern: {pattern}",
                    field="accession_pattern_list",
                    value=pattern
                )
        return v


class ParquetConfig(BaseModel):
    """Configuration for Parquet operations."""
    parquet_path: Path = Field(..., description="Path to Parquet file")
    write_strategy: str = Field(default='all', description="Write strategy: 'all' or 'batch'")
    batch_size: int = Field(default=10000, gt=0, description="Batch size for batch writing")

    @validator('write_strategy')
    def validate_strategy(cls, v):
        if v.lower() not in ['all', 'batch']:
            raise ValidationError(
                f"write_strategy must be 'all' or 'batch', got: {v}",
                field="write_strategy",
                value=v
            )
        return v.lower()


class SlackConfig(BaseModel):
    """Configuration for Slack integration."""
    webhook_url: str = Field(..., description="Slack webhook URL")
    title: Optional[str] = Field(default=None, description="Optional title for messages")
    report_file: Optional[Path] = Field(default=None, description="Path to report file")

    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if not v.startswith('http'):
            raise ValidationError(
                "webhook_url must be a valid HTTP/HTTPS URL",
                field="webhook_url",
                value=v
            )
        return v


class PipelineConfig(BaseModel):
    """Main pipeline configuration."""
    root_dir: Path = Field(..., description="Root directory for log files")
    protocols: List[str] = Field(..., min_items=1, description="List of protocols")
    public_private: List[str] = Field(..., min_items=1, description="List of access types")
    resource_identifiers: List[str] = Field(..., min_items=1, description="Resource identifiers")
    completeness: List[str] = Field(..., min_items=1, description="Completeness statuses")
    accession_pattern: List[str] = Field(..., min_items=1, description="Accession patterns")
    log_file_batch_size: int = Field(default=1000, gt=0, description="Log file batch size")
    chunk_size: int = Field(default=1000, gt=0, description="Chunk size for file operations")
    skipped_years: Optional[List[int]] = Field(default=None, description="Years to skip")
    slack_webhook_url: Optional[str] = Field(default=None, description="Slack webhook URL")
    slack_title: Optional[str] = Field(default=None, description="Slack message title")

    @validator('root_dir')
    def root_dir_must_exist(cls, v):
        if not v.exists():
            raise ConfigurationError(
                f"Root directory does not exist: {v}",
                config_key="root_dir"
            )
        return v

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'PipelineConfig':
        """Load configuration from YAML file."""
        import yaml
        try:
            with open(yaml_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return cls(**config_dict)
        except FileNotFoundError:
            raise ConfigurationError(
                f"Configuration file not found: {yaml_path}",
                config_key="yaml_path"
            )
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in configuration file: {e}",
                config_key="yaml_path"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Error loading configuration: {e}",
                config_key="yaml_path"
            )


def validate_log_file_config(**kwargs) -> LogFileConfig:
    """Validate and return LogFileConfig."""
    try:
        return LogFileConfig(**kwargs)
    except Exception as e:
        if isinstance(e, (ValidationError, ConfigurationError)):
            raise
        raise ValidationError(f"Invalid log file configuration: {e}", **kwargs)


def validate_parquet_config(**kwargs) -> ParquetConfig:
    """Validate and return ParquetConfig."""
    try:
        return ParquetConfig(**kwargs)
    except Exception as e:
        if isinstance(e, (ValidationError, ConfigurationError)):
            raise
        raise ValidationError(f"Invalid parquet configuration: {e}", **kwargs)


def validate_slack_config(**kwargs) -> SlackConfig:
    """Validate and return SlackConfig."""
    try:
        return SlackConfig(**kwargs)
    except Exception as e:
        if isinstance(e, (ValidationError, ConfigurationError)):
            raise
        raise ValidationError(f"Invalid slack configuration: {e}", **kwargs)

