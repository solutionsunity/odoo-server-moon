"""
Configuration handling for the Odoo Dev Server Monitoring Tool.
"""
import os
import json
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration path
DEFAULT_CONFIG_PATH = "config/config.json"

# Cache for configuration
_config_cache = None


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict containing the configuration
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        json.JSONDecodeError: If the configuration file contains invalid JSON
    """
    logger.info(f"Loading configuration from {config_path}")
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info("Configuration loaded successfully")
            return config
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def get_config(config_path: str = None) -> Dict[str, Any]:
    """
    Get the application configuration, using cached values if available.
    
    Args:
        config_path: Optional path to the configuration file
        
    Returns:
        Dict containing the configuration
    """
    global _config_cache
    
    if config_path is None:
        config_path = os.environ.get("CONFIG_PATH", DEFAULT_CONFIG_PATH)
    
    if _config_cache is None:
        _config_cache = load_config(config_path)
    
    return _config_cache


def setup_logging():
    """
    Set up logging based on the configuration.
    """
    config = get_config()
    log_level = config["logging"]["level"].upper()
    log_file = config["logging"]["file"]
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set up file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Set log level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(file_handler)
    
    logger.info(f"Logging configured with level {log_level} to {log_file}")
