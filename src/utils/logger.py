"""
Logging utilities for PDF to CSV processor
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import os
from datetime import datetime

def setup_logger(name: str, level: int = logging.INFO, 
                log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logger with consistent formatting
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    return logger

def get_log_file_path(base_name: str = "pdf_processor") -> str:
    """
    Get standard log file path
    
    Args:
        base_name: Base name for log file
        
    Returns:
        Log file path
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    return str(log_dir / f"{base_name}_{timestamp}.log")

class LogCapture:
    """Context manager for capturing log messages"""
    
    def __init__(self, logger_name: str, level: int = logging.INFO):
        self.logger_name = logger_name
        self.level = level
        self.messages = []
        self.handler = None
    
    def __enter__(self):
        # Create custom handler that captures messages
        class ListHandler(logging.Handler):
            def __init__(self, message_list):
                super().__init__()
                self.messages = message_list
            
            def emit(self, record):
                self.messages.append(self.format(record))
        
        self.handler = ListHandler(self.messages)
        self.handler.setLevel(self.level)
        
        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.handler)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            logger = logging.getLogger(self.logger_name)
            logger.removeHandler(self.handler)
    
    def get_messages(self) -> list:
        """Get captured messages"""
        return self.messages.copy()