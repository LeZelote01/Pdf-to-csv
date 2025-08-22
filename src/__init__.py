"""
PDF to CSV Data Processor

A comprehensive Python package for extracting data from PDF files 
and converting it to CSV format with support for various data patterns.
"""

__version__ = "1.0.0"
__author__ = "PDF Data Processor Team"
__license__ = "MIT"

from src.core.pdf_extractor import PDFExtractor
from src.core.csv_converter import CSVConverter
from src.core.config_manager import ConfigManager

__all__ = [
    'PDFExtractor',
    'CSVConverter', 
    'ConfigManager'
]