#!/usr/bin/env python3
"""
Setup script for PDF to CSV Data Processor

Installation script for the PDF to CSV data processing package.
"""

import os
import sys
from pathlib import Path
from setuptools import setup, find_packages

# Read README file
def read_readme():
    """Read README.md file"""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "PDF to CSV Data Processor - Extract data from PDF files and convert to CSV format"

# Read requirements
def read_requirements():
    """Read requirements.txt file"""
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "PyPDF2>=3.0.1",
            "pdfplumber>=0.9.0",
            "tabula-py>=2.8.2",
            "camelot-py[cv]>=0.11.0",
            "pandas>=1.5.0",
            "click>=8.1.0",
            "rich>=13.0.0"
        ]

# Get version
def get_version():
    """Get version from package"""
    try:
        import src
        return getattr(src, '__version__', '1.0.0')
    except:
        return '1.0.0'

setup(
    name="pdf-to-csv-processor",
    version=get_version(),
    author="PDF Data Processor Team",
    author_email="developer@pdfprocessor.com",
    description="Extract data from PDF files and convert to CSV format",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/pdf-processor/pdf-to-csv",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Text Processing",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0"
        ],
        "ocr": [
            "pytesseract>=0.3.10",
            "Pillow>=9.5.0"
        ],
        "all": [
            "pytest>=7.3.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
            "pytesseract>=0.3.10",
            "Pillow>=9.5.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "pdf-processor=pdf_processor:main",
            "pdf-to-csv=pdf_processor:main",
            "pdf-gui=gui_processor:main"
        ]
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.md", "*.txt"]
    },
    zip_safe=False,
    keywords=[
        "pdf", "csv", "data-extraction", "table-extraction", 
        "pdf-processing", "data-conversion", "document-processing"
    ],
    project_urls={
        "Documentation": "https://github.com/pdf-processor/pdf-to-csv/docs",
        "Source": "https://github.com/pdf-processor/pdf-to-csv",
        "Tracker": "https://github.com/pdf-processor/pdf-to-csv/issues"
    }
)