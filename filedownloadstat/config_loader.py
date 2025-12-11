"""
Configuration loader with validation.
Loads and validates YAML configuration files on startup.
"""
import logging
from pathlib import Path
from typing import Optional

from config_validator import ConfigValidator
from exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def load_and_validate_config(config_path: Optional[str] = None) -> Optional[dict]:
    """
    Load and validate configuration from YAML file.
    
    Args:
        config_path: Optional path to config file. If None, tries default locations.
        
    Returns:
        Validated configuration dictionary or None if validation disabled
        
    Raises:
        ConfigurationError: If validation fails
    """
    if config_path is None:
        # Try default locations
        default_paths = [
            Path("params.config"),
            Path(".params.config"),
            Path("params/pride-local-params.yml"),
        ]
        
        for path in default_paths:
            if path.exists():
                config_path = str(path)
                logger.info("Found configuration file", extra={"path": config_path})
                break
        
        if config_path is None:
            logger.warning("No configuration file found in default locations")
            return None
    
    try:
        config = ConfigValidator.validate_yaml_config(Path(config_path))
        # Convert Pydantic model to dict for compatibility
        return config.dict()
    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(
            f"Unexpected error loading configuration: {e}",
            config_key="config_loader"
        )

