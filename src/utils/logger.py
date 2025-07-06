# src/utils/logger.py
import logging
import logging.handlers
import os
from pathlib import Path
from config.settings import config

def setup_logger():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = Path(config.logging.file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(config.logging.format)
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.logging.level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.logging.level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.logging.file_path,
        maxBytes=config.logging.max_file_size,
        backupCount=config.logging.backup_count
    )
    file_handler.setLevel(getattr(logging, config.logging.level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)
