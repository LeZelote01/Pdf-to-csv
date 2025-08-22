#!/usr/bin/env python3
"""
Unit tests for PDF Extractor

Tests for the PDF data extraction functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pdf_extractor import PDFExtractor
from src.core.config_manager import ConfigManager

class TestPDFExtractor(unittest.TestCase):
    """Test cases for PDFExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ConfigManager()
        self.extractor = PDFExtractor(self.config)
        
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        
        # Create a simple PDF file (mock)
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF file\nendobj\n%%EOF')
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test PDFExtractor initialization"""
        extractor = PDFExtractor()
        self.assertIsNotNone(extractor)
        self.assertIsNotNone(extractor.logger)
        self.assertIsInstance(extractor.available_methods, dict)
        
        # Test with config
        extractor_with_config = PDFExtractor(self.config)
        self.assertIsNotNone(extractor_with_config.config)
    
    def test_validate_pdf(self):
        """Test PDF validation"""
        # Test valid PDF (basic check)
        result = self.extractor.validate_pdf(self.test_pdf_path)
        self.assertTrue(result)
        
        # Test non-existent file
        result = self.extractor.validate_pdf("nonexistent.pdf")
        self.assertFalse(result)
        
        # Test non-PDF file
        txt_file = os.path.join(self.temp_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("Not a PDF")
        result = self.extractor.validate_pdf(txt_file)
        self.assertFalse(result)
    
    def test_get_pdf_info(self):
        """Test getting PDF information"""
        # Mock PyPDF2.PdfReader
        with patch('src.core.pdf_extractor.PyPDF2.PdfReader') as mock_reader:
            # Mock reader instance
            mock_instance = Mock()
            mock_instance.pages = [Mock(), Mock()]  # 2 pages
            mock_instance.metadata = {'Title': 'Test PDF'}
            mock_reader.return_value = mock_instance
            
            info = self.extractor.get_pdf_info(self.test_pdf_path)
            
            self.assertIsInstance(info, dict)
            self.assertIn('filename', info)
            self.assertIn('total_pages', info)
            self.assertEqual(info['total_pages'], 2)
    
    def test_detect_best_method(self):
        """Test automatic method detection"""
        # Mock available methods
        self.extractor.available_methods = {
            'tabula': True,
            'camelot': True,
            'pdfplumber': True,
            'pypdf2': True
        }
        
        # Mock tabula success
        with patch('tabula.read_pdf') as mock_tabula:
            mock_df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
            mock_tabula.return_value = [mock_df]
            
            method = self.extractor._detect_best_method(Path(self.test_pdf_path))
            self.assertEqual(method, 'tabula')
    
    @patch('src.core.pdf_extractor.tabula')
    def test_extract_with_tabula(self, mock_tabula):
        """Test extraction using tabula"""
        # Mock tabula availability
        mock_tabula.read_pdf.return_value = [
            pd.DataFrame({'Name': ['John', 'Jane'], 'Age': [25, 30]})
        ]
        
        self.extractor.available_methods['tabula'] = True
        
        result = self.extractor._extract_with_tabula(Path(self.test_pdf_path))
        
        self.assertIsInstance(result, dict)
        self.assertIn('tables', result)
        self.assertIn('method', result)
        self.assertEqual(result['method'], 'tabula')
        self.assertGreater(len(result['tables']), 0)
    
    @patch('src.core.pdf_extractor.camelot')
    def test_extract_with_camelot(self, mock_camelot):
        """Test extraction using camelot"""
        # Mock camelot table
        mock_table = Mock()
        mock_table.df = pd.DataFrame({'Product': ['A', 'B'], 'Price': [10, 20]})
        mock_table.accuracy = 95.0
        
        mock_tables = Mock()
        mock_tables.__iter__ = Mock(return_value=iter([mock_table]))
        mock_tables.__len__ = Mock(return_value=1)
        
        mock_camelot.read_pdf.return_value = mock_tables
        
        self.extractor.available_methods['camelot'] = True
        
        result = self.extractor._extract_with_camelot(Path(self.test_pdf_path))
        
        self.assertIsInstance(result, dict)
        self.assertIn('tables', result)
        self.assertIn('method', result)
        self.assertEqual(result['method'], 'camelot')
        self.assertIn('accuracy', result)
    
    @patch('src.core.pdf_extractor.pdfplumber')
    def test_extract_with_pdfplumber(self, mock_pdfplumber):
        """Test extraction using pdfplumber"""
        # Mock pdfplumber PDF
        mock_page = Mock()
        mock_page.extract_tables.return_value = [
            [['Header1', 'Header2'], ['Value1', 'Value2'], ['Value3', 'Value4']]
        ]
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        mock_pdfplumber.open.return_value = mock_pdf
        
        self.extractor.available_methods['pdfplumber'] = True
        
        result = self.extractor._extract_with_pdfplumber(Path(self.test_pdf_path))
        
        self.assertIsInstance(result, dict)
        self.assertIn('tables', result)
        self.assertIn('method', result)
        self.assertEqual(result['method'], 'pdfplumber')
    
    @patch('src.core.pdf_extractor.PyPDF2')
    def test_extract_with_pypdf2(self, mock_pypdf2):
        """Test extraction using PyPDF2 (fallback)"""
        # Mock PyPDF2 reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Name\tAge\nJohn\t25\nJane\t30"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        with patch('builtins.open', unittest.mock.mock_open()):
            result = self.extractor._extract_with_pypdf2(Path(self.test_pdf_path))
        
        self.assertIsInstance(result, dict)
        self.assertIn('method', result)
        self.assertEqual(result['method'], 'pypdf2')
        self.assertIn('raw_text', result)
    
    def test_clean_dataframe(self):
        """Test DataFrame cleaning functionality"""
        # Create a messy DataFrame
        df = pd.DataFrame({
            'Col1': ['  Value1  ', 'Value2', None, ''],
            'Col2': ['Value3', '  Value4  ', 'Value5', None],
            '': [None, None, None, None]  # Empty column
        })
        
        cleaned_df = self.extractor._clean_dataframe(df)
        
        # Check that empty columns are removed
        self.assertNotIn('', cleaned_df.columns)
        
        # Check that values are cleaned
        self.assertEqual(cleaned_df.iloc[0, 0], 'Value1')  # Stripped
        self.assertEqual(cleaned_df.iloc[1, 1], 'Value4')  # Stripped
    
    def test_parse_text_to_table(self):
        """Test parsing text into tabular format"""
        text_content = [
            "Name\tAge\tCity\nJohn\t25\tNew York\nJane\t30\tLondon",
            "Product | Price | Stock\nApple | $1.50 | 100\nBanana | $0.80 | 50"
        ]
        
        tables = self.extractor._parse_text_to_table(text_content)
        
        self.assertIsInstance(tables, list)
        # Should find at least one structured table
        if tables:
            self.assertIsInstance(tables[0], pd.DataFrame)
    
    def test_extract_data_integration(self):
        """Test full extract_data method"""
        # Mock the internal methods
        with patch.object(self.extractor, '_detect_best_method') as mock_detect:
            with patch.object(self.extractor, '_extract_with_pypdf2') as mock_extract:
                mock_detect.return_value = 'pypdf2'
                mock_extract.return_value = {
                    'tables': [pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})],
                    'total_rows': 2,
                    'total_columns': 2,
                    'method': 'pypdf2'
                }
                
                result = self.extractor.extract_data(self.test_pdf_path)
                
                self.assertIsInstance(result, dict)
                self.assertIn('source_file', result)
                self.assertIn('extraction_method', result)
                self.assertIn('tables', result)
    
    def test_extract_data_file_not_found(self):
        """Test extract_data with non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_data("nonexistent.pdf")
    
    def test_extract_data_with_options(self):
        """Test extract_data with various options"""
        with patch.object(self.extractor, '_extract_with_pypdf2') as mock_extract:
            mock_extract.return_value = {
                'tables': [],
                'total_rows': 0,
                'total_columns': 0,
                'method': 'pypdf2'
            }
            
            # Test with page range
            result = self.extractor.extract_data(
                self.test_pdf_path, 
                method='pypdf2',
                pages='1-3',
                pattern='table'
            )
            
            self.assertIsInstance(result, dict)
            mock_extract.assert_called_once()

class TestPDFExtractorEdgeCases(unittest.TestCase):
    """Test edge cases for PDF extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = PDFExtractor()
    
    def test_empty_pdf_handling(self):
        """Test handling of PDFs with no extractable data"""
        with patch.object(self.extractor, '_extract_with_pypdf2') as mock_extract:
            mock_extract.return_value = {
                'tables': [],
                'total_rows': 0,
                'total_columns': 0,
                'method': 'pypdf2'
            }
            
            # This should not raise an error
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(b'%PDF-1.4\n%%EOF')
                tmp_path = tmp.name
            
            try:
                result = self.extractor.extract_data(tmp_path)
                self.assertIsInstance(result, dict)
                self.assertEqual(len(result.get('tables', [])), 0)
            finally:
                os.unlink(tmp_path)
    
    def test_corrupted_pdf_handling(self):
        """Test handling of corrupted PDF files"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'This is not a valid PDF file')
            tmp_path = tmp.name
        
        try:
            # Should handle gracefully
            with patch.object(self.extractor, 'validate_pdf', return_value=False):
                with self.assertRaises(Exception):
                    self.extractor.extract_data(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_large_table_handling(self):
        """Test handling of large tables"""
        # Create a large DataFrame
        large_data = {f'col_{i}': list(range(1000)) for i in range(50)}
        large_df = pd.DataFrame(large_data)
        
        cleaned_df = self.extractor._clean_dataframe(large_df)
        
        # Should handle large DataFrames without issues
        self.assertIsInstance(cleaned_df, pd.DataFrame)
        self.assertEqual(len(cleaned_df), 1000)
        self.assertEqual(len(cleaned_df.columns), 50)

if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.ERROR)  # Reduce noise during tests
    
    # Run tests
    unittest.main(verbosity=2)