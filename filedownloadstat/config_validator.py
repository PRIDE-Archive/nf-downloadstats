"""
Configuration validation module for YAML configuration files.
Validates configuration on startup to catch errors early.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from exceptions import ConfigurationError
from validators import PipelineConfig

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates pipeline configuration files."""
    
    REQUIRED_FIELDS = [
        'root_dir',
        'protocols',
        'public_private',
        'resource_identifiers',
        'completeness',
        'accession_pattern'
    ]
    
    OPTIONAL_FIELDS = [
        'log_file_batch_size',
        'chunk_size',
        'skipped_years',
        'slack_webhook_url',
        'slack_title',
        'report_template',
        'resource_base_url',
        'report_copy_filepath',
        'disable_db_update'
    ]
    
    @staticmethod
    def validate_yaml_config(yaml_path: Path) -> PipelineConfig:
        """
        Validate YAML configuration file.
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            Validated PipelineConfig object
            
        Raises:
            ConfigurationError: If validation fails
        """
        logger.info("Validating configuration file", extra={"yaml_path": str(yaml_path)})
        
        # Check if file exists
        if not yaml_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {yaml_path}",
                config_key="yaml_path"
            )
        
        # Load YAML
        try:
            with open(yaml_path, 'r') as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax in configuration file: {e}",
                config_key="yaml_path"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Error reading configuration file: {e}",
                config_key="yaml_path"
            )
        
        if not config_dict:
            raise ConfigurationError(
                "Configuration file is empty",
                config_key="yaml_path"
            )
        
        # Validate required fields
        missing_fields = []
        for field in ConfigValidator.REQUIRED_FIELDS:
            if field not in config_dict or not config_dict[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ConfigurationError(
                f"Missing required configuration fields: {', '.join(missing_fields)}",
                config_key=",".join(missing_fields)
            )
        
        # Validate field types and values
        ConfigValidator._validate_field_types(config_dict)
        ConfigValidator._validate_field_values(config_dict)
        
        # Convert to PipelineConfig using pydantic validation
        try:
            # Convert root_dir to Path if it's a string
            if 'root_dir' in config_dict and isinstance(config_dict['root_dir'], str):
                config_dict['root_dir'] = Path(config_dict['root_dir'])
            
            config = PipelineConfig(**config_dict)
            logger.info("Configuration validated successfully", extra={"yaml_path": str(yaml_path)})
            return config
        except Exception as e:
            raise ConfigurationError(
                f"Configuration validation failed: {e}",
                config_key="validation"
            )
    
    @staticmethod
    def _validate_field_types(config_dict: Dict[str, Any]) -> None:
        """Validate that fields have correct types."""
        type_checks = {
            'protocols': (list, str),
            'public_private': (list, str),
            'resource_identifiers': (list, str),
            'completeness': (list, str),
            'accession_pattern': (list, str),
            'log_file_batch_size': (int,),
            'chunk_size': (int,),
            'skipped_years': (list, type(None)),
        }
        
        for field, expected_types in type_checks.items():
            if field in config_dict:
                value = config_dict[field]
                if not isinstance(value, expected_types):
                    raise ConfigurationError(
                        f"Field '{field}' has invalid type. Expected {expected_types}, got {type(value)}",
                        config_key=field
                    )
    
    @staticmethod
    def _validate_field_values(config_dict: Dict[str, Any]) -> None:
        """Validate field values."""
        # Validate lists are not empty
        list_fields = ['protocols', 'public_private', 'resource_identifiers', 'completeness', 'accession_pattern']
        for field in list_fields:
            if field in config_dict:
                value = config_dict[field]
                if isinstance(value, list) and len(value) == 0:
                    raise ConfigurationError(
                        f"Field '{field}' cannot be empty",
                        config_key=field
                    )
        
        # Validate batch sizes are positive
        if 'log_file_batch_size' in config_dict:
            if config_dict['log_file_batch_size'] <= 0:
                raise ConfigurationError(
                    "log_file_batch_size must be greater than 0",
                    config_key="log_file_batch_size"
                )
        
        if 'chunk_size' in config_dict:
            if config_dict['chunk_size'] <= 0:
                raise ConfigurationError(
                    "chunk_size must be greater than 0",
                    config_key="chunk_size"
                )
        
        # Validate accession patterns are valid regex
        if 'accession_pattern' in config_dict:
            import re
            patterns = config_dict['accession_pattern']
            if isinstance(patterns, list):
                for pattern in patterns:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        raise ConfigurationError(
                            f"Invalid regex pattern in accession_pattern: {pattern} - {e}",
                            config_key="accession_pattern"
                        )


def validate_config_file(yaml_path: str) -> PipelineConfig:
    """
    Convenience function to validate a configuration file.
    
    Args:
        yaml_path: Path to YAML configuration file
        
    Returns:
        Validated PipelineConfig object
    """
    return ConfigValidator.validate_yaml_config(Path(yaml_path))

