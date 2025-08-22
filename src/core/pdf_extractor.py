"""
PDF Data Extractor

Handles extraction of data from PDF files using multiple methods:
- Tabula-py for table extraction
- Camelot for advanced table detection
- PyPDF2 for text extraction
- PDFplumber for complex layouts
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import warnings

# PDF processing libraries
try:
    import tabula
except ImportError:
    tabula = None

try:
    import camelot
except ImportError:
    camelot = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

import PyPDF2
from src.utils.logger import setup_logger

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

class PDFExtractor:
    """Main PDF data extraction class"""
    
    def __init__(self, config_manager=None):
        """Initialize PDF extractor with configuration"""
        self.config = config_manager
        self.logger = setup_logger(__name__)
        
        # Available extraction methods
        self.available_methods = {
            'tabula': tabula is not None,
            'camelot': camelot is not None,
            'pdfplumber': pdfplumber is not None,
            'pypdf2': True  # Always available
        }
        
        self.logger.info(f"PDF Extractor initialized. Available methods: {list(k for k, v in self.available_methods.items() if v)}")
    
    def extract_data(self, pdf_path: str, **kwargs) -> Dict[str, Any]:
        """
        Extract data from PDF file using specified or auto-detected method
        
        Args:
            pdf_path: Path to PDF file
            **kwargs: Extraction options (method, pages, pattern, etc.)
            
        Returns:
            Dictionary containing extracted data and metadata
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            self.logger.info(f"Starting extraction from: {pdf_path.name}")
            
            # Get extraction method
            method = kwargs.get('method', 'auto')
            if method == 'auto':
                method = self._detect_best_method(pdf_path)
            
            # Extract data based on method
            if method == 'tabula' and self.available_methods['tabula']:
                extracted_data = self._extract_with_tabula(pdf_path, **kwargs)
            elif method == 'camelot' and self.available_methods['camelot']:
                extracted_data = self._extract_with_camelot(pdf_path, **kwargs)
            elif method == 'pdfplumber' and self.available_methods['pdfplumber']:
                extracted_data = self._extract_with_pdfplumber(pdf_path, **kwargs)
            else:
                # Fallback to PyPDF2
                extracted_data = self._extract_with_pypdf2(pdf_path, **kwargs)
            
            # Add metadata
            extracted_data.update({
                'source_file': str(pdf_path),
                'extraction_method': method,
                'pages_processed': extracted_data.get('pages', 'all')
            })
            
            self.logger.info(f"Extraction completed. Tables found: {len(extracted_data.get('tables', []))}")
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {str(e)}")
            raise
    
    def _detect_best_method(self, pdf_path: Path) -> str:
        """
        Auto-detect the best extraction method for the PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Best method name
        """
        try:
            # Try to detect tables first
            if self.available_methods['tabula']:
                # Quick test with tabula
                try:
                    test_tables = tabula.read_pdf(str(pdf_path), pages=1, silent=True, lattice=True)
                    if test_tables and len(test_tables) > 0 and not test_tables[0].empty:
                        return 'tabula'
                except:
                    pass
            
            if self.available_methods['camelot']:
                # Test with camelot
                try:
                    test_tables = camelot.read_pdf(str(pdf_path), pages='1')
                    if test_tables and len(test_tables) > 0:
                        return 'camelot'
                except:
                    pass
            
            if self.available_methods['pdfplumber']:
                return 'pdfplumber'
            
            # Fallback to PyPDF2
            return 'pypdf2'
            
        except Exception as e:
            self.logger.warning(f"Method detection failed, using PyPDF2: {str(e)}")
            return 'pypdf2'
    
    def _extract_with_tabula(self, pdf_path: Path, **kwargs) -> Dict[str, Any]:
        """Extract data using tabula-py"""
        try:
            pages = kwargs.get('pages', 'all')
            lattice = kwargs.get('lattice', True)
            
            self.logger.debug(f"Using tabula extraction on pages: {pages}")
            
            # Extract tables
            dfs = tabula.read_pdf(
                str(pdf_path),
                pages=pages,
                lattice=lattice,
                stream=not lattice,
                guess=True,
                silent=True
            )
            
            if not dfs:
                return {'tables': [], 'total_rows': 0, 'total_columns': 0, 'method': 'tabula'}
            
            # Process extracted dataframes
            tables = []
            total_rows = 0
            max_columns = 0
            
            for i, df in enumerate(dfs):
                if df is not None and not df.empty:
                    # Clean the dataframe
                    df = self._clean_dataframe(df)
                    tables.append(df)
                    total_rows += len(df)
                    max_columns = max(max_columns, len(df.columns))
            
            return {
                'tables': tables,
                'total_rows': total_rows,
                'total_columns': max_columns,
                'method': 'tabula',
                'pages': pages
            }
            
        except Exception as e:
            self.logger.error(f"Tabula extraction failed: {str(e)}")
            raise
    
    def _extract_with_camelot(self, pdf_path: Path, **kwargs) -> Dict[str, Any]:
        """Extract data using camelot-py"""
        try:
            pages = kwargs.get('pages', '1-end')
            flavor = kwargs.get('flavor', 'lattice')
            
            self.logger.debug(f"Using camelot extraction with flavor: {flavor}")
            
            # Extract tables
            tables_obj = camelot.read_pdf(
                str(pdf_path),
                pages=pages,
                flavor=flavor
            )
            
            if not tables_obj:
                return {'tables': [], 'total_rows': 0, 'total_columns': 0, 'method': 'camelot'}
            
            # Process extracted tables
            tables = []
            total_rows = 0
            max_columns = 0
            
            for table in tables_obj:
                df = table.df
                if df is not None and not df.empty:
                    # Clean the dataframe
                    df = self._clean_dataframe(df)
                    tables.append(df)
                    total_rows += len(df)
                    max_columns = max(max_columns, len(df.columns))
            
            return {
                'tables': tables,
                'total_rows': total_rows,
                'total_columns': max_columns,
                'method': 'camelot',
                'pages': pages,
                'accuracy': sum(table.accuracy for table in tables_obj) / len(tables_obj) if tables_obj else 0
            }
            
        except Exception as e:
            self.logger.error(f"Camelot extraction failed: {str(e)}")
            raise
    
    def _extract_with_pdfplumber(self, pdf_path: Path, **kwargs) -> Dict[str, Any]:
        """Extract data using pdfplumber"""
        try:
            pages_range = kwargs.get('pages')
            
            self.logger.debug("Using pdfplumber extraction")
            
            tables = []
            total_rows = 0
            max_columns = 0
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                pages_to_process = pdf.pages
                
                # Handle page range
                if pages_range:
                    if isinstance(pages_range, str):
                        if '-' in pages_range:
                            start, end = pages_range.split('-')
                            start = int(start) - 1 if start else 0
                            end = int(end) if end != 'end' else len(pdf.pages)
                            pages_to_process = pdf.pages[start:end]
                        else:
                            page_nums = [int(p) - 1 for p in pages_range.split(',')]
                            pages_to_process = [pdf.pages[i] for i in page_nums if i < len(pdf.pages)]
                
                for page in pages_to_process:
                    # Extract tables from page
                    page_tables = page.extract_tables()
                    
                    for table_data in page_tables:
                        if table_data:
                            # Convert to DataFrame
                            df = pd.DataFrame(table_data[1:], columns=table_data[0])
                            df = self._clean_dataframe(df)
                            
                            if not df.empty:
                                tables.append(df)
                                total_rows += len(df)
                                max_columns = max(max_columns, len(df.columns))
            
            return {
                'tables': tables,
                'total_rows': total_rows,
                'total_columns': max_columns,
                'method': 'pdfplumber',
                'pages': pages_range or 'all'
            }
            
        except Exception as e:
            self.logger.error(f"PDFplumber extraction failed: {str(e)}")
            raise
    
    def _extract_with_pypdf2(self, pdf_path: Path, **kwargs) -> Dict[str, Any]:
        """Extract text data using PyPDF2 (fallback method)"""
        try:
            self.logger.debug("Using PyPDF2 text extraction (fallback method)")
            
            text_content = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                pages_range = kwargs.get('pages')
                pages_to_process = range(len(pdf_reader.pages))
                
                # Handle page range
                if pages_range:
                    if isinstance(pages_range, str):
                        if '-' in pages_range:
                            start, end = pages_range.split('-')
                            start = int(start) - 1 if start else 0
                            end = int(end) if end != 'end' else len(pdf_reader.pages)
                            pages_to_process = range(start, min(end, len(pdf_reader.pages)))
                        else:
                            page_nums = [int(p) - 1 for p in pages_range.split(',')]
                            pages_to_process = [i for i in page_nums if i < len(pdf_reader.pages)]
                
                for page_num in pages_to_process:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)
            
            # Try to parse text into structured data
            parsed_data = self._parse_text_to_table(text_content)
            
            return {
                'tables': parsed_data,
                'total_rows': sum(len(table) for table in parsed_data),
                'total_columns': max((len(table.columns) for table in parsed_data), default=0),
                'method': 'pypdf2',
                'raw_text': text_content
            }
            
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction failed: {str(e)}")
            raise
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize DataFrame"""
        try:
            # Remove completely empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Clean cell values
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace('nan', '')
            
            # Reset index
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.warning(f"DataFrame cleaning failed: {str(e)}")
            return df
    
    def _parse_text_to_table(self, text_content: List[str]) -> List[pd.DataFrame]:
        """Try to parse raw text into tabular data"""
        try:
            tables = []
            
            for text in text_content:
                lines = text.split('\n')
                
                # Look for patterns that might be tabular
                potential_rows = []
                for line in lines:
                    line = line.strip()
                    if line and ('\t' in line or '  ' in line or '|' in line):
                        # Split by common delimiters
                        if '\t' in line:
                            cells = line.split('\t')
                        elif '|' in line:
                            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                        else:
                            # Split by multiple spaces
                            cells = [cell.strip() for cell in line.split('  ') if cell.strip()]
                        
                        if len(cells) > 1:
                            potential_rows.append(cells)
                
                if potential_rows:
                    # Find consistent column count
                    max_cols = max(len(row) for row in potential_rows)
                    consistent_rows = [row for row in potential_rows if len(row) >= max_cols // 2]
                    
                    if consistent_rows:
                        # Pad rows to same length
                        padded_rows = []
                        for row in consistent_rows:
                            padded_row = row + [''] * (max_cols - len(row))
                            padded_rows.append(padded_row[:max_cols])
                        
                        # Create DataFrame
                        if len(padded_rows) > 1:
                            df = pd.DataFrame(padded_rows[1:], columns=padded_rows[0])
                            df = self._clean_dataframe(df)
                            if not df.empty:
                                tables.append(df)
            
            return tables
            
        except Exception as e:
            self.logger.warning(f"Text parsing failed: {str(e)}")
            return []
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """Get basic information about the PDF file"""
        try:
            pdf_path = Path(pdf_path)
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                info = {
                    'filename': pdf_path.name,
                    'total_pages': len(pdf_reader.pages),
                    'file_size': pdf_path.stat().st_size,
                    'metadata': pdf_reader.metadata if pdf_reader.metadata else {}
                }
                
                return info
                
        except Exception as e:
            self.logger.error(f"Failed to get PDF info: {str(e)}")
            return {}
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """Validate if file is a readable PDF"""
        try:
            pdf_path = Path(pdf_path)
            
            if not pdf_path.exists():
                return False
            
            if pdf_path.suffix.lower() != '.pdf':
                return False
            
            # Try to open with PyPDF2
            with open(pdf_path, 'rb') as file:
                PyPDF2.PdfReader(file)
            
            return True
            
        except Exception as e:
            self.logger.error(f"PDF validation failed: {str(e)}")
            return False