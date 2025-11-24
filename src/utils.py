"""
Utility functions for the GTA VI LLM Dataset Project.

This module provides shared utilities for configuration loading,
logging setup, file I/O, and common helper functions.
"""

import os
import yaml
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration settings
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def load_env_vars() -> None:
    """Load environment variables from .env file."""
    load_dotenv()


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        log_format: Optional custom log format
        
    Returns:
        Configured logger instance
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )
    
    return logging.getLogger(__name__)


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Generate hash of a string for privacy protection.
    
    Args:
        text: String to hash
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


def ensure_dir(directory: str) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent


def format_number(num: int) -> str:
    """
    Format large numbers with commas.
    
    Args:
        num: Number to format
        
    Returns:
        Formatted string
    """
    return f"{num:,}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def save_progress(data: Dict[str, Any], filename: str) -> None:
    """
    Save progress data to JSON file.
    
    Args:
        data: Progress data dictionary
        filename: Output filename
    """
    import json
    
    ensure_dir(Path(filename).parent)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def load_progress(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load progress data from JSON file.
    
    Args:
        filename: Progress file path
        
    Returns:
        Progress data dictionary or None if file doesn't exist
    """
    import json
    
    if not Path(filename).exists():
        return None
    
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


class ProgressTracker:
    """Track and display progress for long-running operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            total: Total number of items
            description: Description of the operation
        """
        from tqdm import tqdm
        self.pbar = tqdm(total=total, desc=description)
        self.current = 0
    
    def update(self, n: int = 1) -> None:
        """Update progress by n items."""
        self.pbar.update(n)
        self.current += n
    
    def close(self) -> None:
        """Close the progress bar."""
        self.pbar.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate that API key is present and not a placeholder.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False
    
    placeholders = ["your_api_key", "your_youtube_api_key", "placeholder"]
    return not any(placeholder in api_key.lower() for placeholder in placeholders)


if __name__ == "__main__":
    # Test utilities
    config = load_config()
    print("Configuration loaded successfully")
    print(f"Video ID: {config['video']['video_id']}")
    
    logger = setup_logging()
    logger.info("Logging configured successfully")
    
    # Test hashing
    test_string = "test_user_123"
    hashed = hash_string(test_string)
    print(f"Hash of '{test_string}': {hashed}")
