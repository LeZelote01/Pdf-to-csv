#!/usr/bin/env python3
"""
Integration tests for PDF to CSV Processor

Tests the complete workflow from PDF extraction to CSV output.
"""

import unittest
import tempfile
import os
from pathlib import Path
import pandas as pd
from unittest.mock import patch, Mock
import json

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pdf_extractor import PDFExtractor
from src.core.csv_converter import CSVConverter
from src.core.config_manager import ConfigManager
from src.utils.file_handler import FileHandler

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete PDF processing workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test PDF file
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF file\nendobj\n%%EOF')
        
        # Initialize components
        self.config = ConfigManager()
        self.extractor = PDFExtractor(self.config)
        self.converter = CSVConverter(self.config)
        self.file_handler = FileHandler()
        
        # Sample data for mocking
        self.sample_table = pd.DataFrame({
            'Product': ['Apple', 'Banana', 'Cherry'],
            'Price': [1.50, 0.80, 2.20],
            'Stock': [100, 150, 75]
        })
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """Test complete PDF to CSV workflow"""
        # Mock the extraction to return our sample data
        with patch.object(self.extractor, 'extract_data') as mock_extract:
            mock_extract.return_value = {
                'tables': [self.sample_table],
                'total_rows': 3,
                'total_columns': 3,
                'method': 'test',
                'source_file': self.test_pdf_path
            }
            
            # Step 1: Extract data
            extracted_data = self.extractor.extract_data(self.test_pdf_path)
            
            self.assertIsInstance(extracted_data, dict)
            self.assertIn('tables', extracted_data)
            self.assertEqual(len(extracted_data['tables']), 1)
            
            # Step 2: Convert to CSV
            csv_data = self.converter.convert_to_csv(extracted_data)
            
            self.assertIsInstance(csv_data, str)
            self.assertIn('Product,Price,Stock', csv_data)
            self.assertIn('Apple,1.5,100', csv_data)
            
            # Step 3: Save to file
            output_path = os.path.join(self.temp_dir, "output.csv")
            success = self.file_handler.save_csv(csv_data, output_path)
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            
            # Step 4: Verify saved file
            with open(output_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            
            self.assertEqual(saved_content, csv_data)
    
    def test_batch_processing_workflow(self):
        """Test batch processing of multiple PDFs"""
        # Create multiple test PDF files
        pdf_files = []
        for i in range(3):
            pdf_path = os.path.join(self.temp_dir, f"test_{i}.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Test PDF file\nendobj\n%%EOF')
            pdf_files.append(pdf_path)
        
        # Mock extraction for all files
        with patch.object(self.extractor, 'extract_data') as mock_extract:
            # Return different data for each file
            def mock_extraction(pdf_path, **kwargs):
                file_num = int(Path(pdf_path).stem.split('_')[1])
                return {
                    'tables': [pd.DataFrame({
                        'ID': [file_num * 10 + i for i in range(3)],
                        'Value': [f'Value_{file_num}_{i}' for i in range(3)]
                    })],
                    'total_rows': 3,
                    'total_columns': 2,
                    'method': 'test',
                    'source_file': pdf_path
                }
            
            mock_extract.side_effect = mock_extraction
            
            # Process all files
            output_dir = os.path.join(self.temp_dir, "batch_output")
            os.makedirs(output_dir, exist_ok=True)
            
            results = []
            for pdf_path in pdf_files:
                try:
                    # Extract
                    extracted_data = self.extractor.extract_data(pdf_path)
                    
                    # Convert
                    csv_data = self.converter.convert_to_csv(extracted_data)
                    
                    # Save
                    output_filename = Path(pdf_path).stem + ".csv"
                    output_path = os.path.join(output_dir, output_filename)
                    success = self.file_handler.save_csv(csv_data, output_path)
                    
                    results.append(success)
                    
                except Exception as e:
                    results.append(False)
            
            # Verify all files processed successfully
            self.assertEqual(len(results), 3)
            self.assertTrue(all(results))
            
            # Verify output files exist
            for i in range(3):
                output_file = os.path.join(output_dir, f"test_{i}.csv")
                self.assertTrue(os.path.exists(output_file))
    
    def test_error_handling_workflow(self):
        """Test error handling in complete workflow"""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_data("nonexistent.pdf")
        
        # Test with empty extraction data
        empty_data = {'tables': [], 'total_rows': 0, 'total_columns': 0}
        csv_data = self.converter.convert_to_csv(empty_data)
        self.assertEqual(csv_data, "")
        
        # Test saving empty CSV
        output_path = os.path.join(self.temp_dir, "empty.csv")
        success = self.file_handler.save_csv("", output_path)
        self.assertFalse(success)  # Should fail with empty data
    
    def test_configuration_integration(self):
        """Test integration with different configurations"""
        # Create custom config
        custom_config_data = {
            'extraction_method': 'tabula',
            'output_format': {
                'delimiter': '|',
                'encoding': 'utf-8',
                'header_row': False
            },
            'processing': {
                'clean_data': True,
                'skip_empty_rows': True
            }
        }
        
        config_path = os.path.join(self.temp_dir, "custom_config.json")
        with open(config_path, 'w') as f:
            json.dump(custom_config_data, f)
        
        # Initialize with custom config
        custom_config = ConfigManager(config_path)
        custom_converter = CSVConverter(custom_config)
        
        # Mock extraction
        with patch.object(self.extractor, 'extract_data') as mock_extract:
            mock_extract.return_value = {
                'tables': [self.sample_table],
                'total_rows': 3,
                'total_columns': 3,
                'method': 'tabula'
            }
            
            extracted_data = self.extractor.extract_data(self.test_pdf_path)
            
            # Convert with custom settings
            csv_data = custom_converter.convert_to_csv(
                extracted_data,
                delimiter=custom_config.get('output_format.delimiter'),
                header_row=custom_config.get('output_format.header_row')
            )
            
            # Verify custom delimiter used
            self.assertIn('|', csv_data)
            # Verify no header (based on config)
            self.assertNotIn('Product|Price|Stock', csv_data)
    
    def test_multiple_format_export_integration(self):
        """Test exporting to multiple formats"""
        with patch.object(self.extractor, 'extract_data') as mock_extract:
            mock_extract.return_value = {
                'tables': [self.sample_table],
                'total_rows': 3,
                'total_columns': 3,
                'method': 'test'
            }
            
            extracted_data = self.extractor.extract_data(self.test_pdf_path)
            
            # Export to multiple formats
            output_dir = os.path.join(self.temp_dir, "multi_export")
            results = self.converter.convert_multiple_formats(
                extracted_data,
                output_dir,
                "multi_format_test"
            )
            
            self.assertIsInstance(results, dict)
            self.assertIn('csv', results)
            
            # Verify CSV was created
            csv_path = os.path.join(output_dir, "multi_format_test.csv")
            if results['csv']:
                self.assertTrue(os.path.exists(csv_path))
    
    def test_file_validation_integration(self):
        """Test file validation integration"""
        # Create various test files
        valid_pdf = os.path.join(self.temp_dir, "valid.pdf")
        with open(valid_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF\n%%EOF')
        
        invalid_pdf = os.path.join(self.temp_dir, "invalid.pdf")
        with open(invalid_pdf, 'w') as f:
            f.write("Not a PDF")
        
        txt_file = os.path.join(self.temp_dir, "document.txt")
        with open(txt_file, 'w') as f:
            f.write("Text document")
        
        # Test validation
        self.assertTrue(self.file_handler.validate_pdf(valid_pdf))
        self.assertFalse(self.file_handler.validate_pdf(invalid_pdf))
        self.assertFalse(self.file_handler.validate_pdf(txt_file))
        self.assertFalse(self.file_handler.validate_pdf("nonexistent.pdf"))
    
    def test_preview_integration(self):
        """Test preview functionality integration"""
        with patch.object(self.extractor, 'extract_data') as mock_extract:
            mock_extract.return_value = {
                'tables': [self.sample_table],
                'total_rows': 3,
                'total_columns': 3,
                'method': 'test'
            }
            
            extracted_data = self.extractor.extract_data(self.test_pdf_path)
            
            # Generate preview
            preview = self.converter.preview_csv(extracted_data, preview_rows=2)
            
            self.assertIsInstance(preview, dict)
            self.assertIn('preview', preview)
            self.assertIn('row_count', preview)
            self.assertIn('column_count', preview)
            
            # Verify preview content
            preview_text = preview['preview']
            lines = preview_text.strip().split('\n')
            self.assertEqual(len(lines), 3)  # Header + 2 preview rows
            
            self.assertEqual(preview['row_count'], 3)
            self.assertEqual(preview['column_count'], 3)
    
    def test_large_file_handling_integration(self):
        """Test handling of large files in complete workflow"""
        # Create large sample data
        large_table = pd.DataFrame({
            f'Column_{i}': [f'Value_{i}_{j}' for j in range(1000)]
            for i in range(20)
        })
        
        with patch.object(self.extractor, 'extract_data') as mock_extract:
            mock_extract.return_value = {
                'tables': [large_table],
                'total_rows': 1000,
                'total_columns': 20,
                'method': 'test'
            }
            
            # Should handle large data without issues
            extracted_data = self.extractor.extract_data(self.test_pdf_path)
            csv_data = self.converter.convert_to_csv(extracted_data)
            
            self.assertIsInstance(csv_data, str)
            self.assertGreater(len(csv_data), 100000)  # Should be substantial
            
            # Save large file
            output_path = os.path.join(self.temp_dir, "large_output.csv")
            success = self.file_handler.save_csv(csv_data, output_path)
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            
            # Verify file size
            file_size = os.path.getsize(output_path)
            self.assertGreater(file_size, 100000)

class TestEndToEndScenarios(unittest.TestCase):
    """End-to-end scenario tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_invoice_processing_scenario(self):
        """Test processing an invoice-like PDF"""
        # Mock invoice data
        invoice_table = pd.DataFrame({
            'Item': ['Widget A', 'Widget B', 'Service Fee'],
            'Quantity': [2, 1, 1],
            'Unit Price': [25.00, 35.00, 10.00],
            'Total': [50.00, 35.00, 10.00]
        })
        
        config = ConfigManager()
        extractor = PDFExtractor(config)
        converter = CSVConverter(config)
        file_handler = FileHandler()
        
        with patch.object(extractor, 'extract_data') as mock_extract:
            mock_extract.return_value = {
                'tables': [invoice_table],
                'total_rows': 3,
                'total_columns': 4,
                'method': 'camelot'  # Good for structured tables
            }
            
            # Process invoice
            pdf_path = os.path.join(self.temp_dir, "invoice.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Invoice PDF\n%%EOF')
            
            extracted_data = extractor.extract_data(pdf_path)
            csv_data = converter.convert_to_csv(extracted_data)
            
            # Save and verify
            output_path = os.path.join(self.temp_dir, "invoice.csv")
            success = file_handler.save_csv(csv_data, output_path)
            
            self.assertTrue(success)
            self.assertIn('Item,Quantity,Unit Price,Total', csv_data)
            self.assertIn('Widget A,2,25.0,50.0', csv_data)
    
    def test_report_processing_scenario(self):
        """Test processing a report with multiple tables"""
        # Mock report with multiple tables
        summary_table = pd.DataFrame({
            'Metric': ['Revenue', 'Expenses', 'Profit'],
            'Q1': [100000, 60000, 40000],
            'Q2': [120000, 65000, 55000],
            'Q3': [110000, 62000, 48000]
        })
        
        detail_table = pd.DataFrame({
            'Department': ['Sales', 'Marketing', 'Operations'],
            'Budget': [50000, 30000, 40000],
            'Actual': [52000, 28000, 38000],
            'Variance': [2000, -2000, -2000]
        })
        
        config = ConfigManager()
        extractor = PDFExtractor(config)
        converter = CSVConverter(config)
        
        with patch.object(extractor, 'extract_data') as mock_extract:
            mock_extract.return_value = {
                'tables': [summary_table, detail_table],
                'total_rows': 6,
                'total_columns': 4,
                'method': 'tabula'
            }
            
            pdf_path = os.path.join(self.temp_dir, "report.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Report PDF\n%%EOF')
            
            extracted_data = extractor.extract_data(pdf_path)
            
            # Test merged output
            csv_data = converter.convert_to_csv(extracted_data, merge_tables=True)
            self.assertIsInstance(csv_data, str)
            
            # Test separate outputs
            results = converter.convert_multiple_formats(
                extracted_data,
                self.temp_dir,
                "report"
            )
            
            self.assertTrue(results.get('csv', False))

if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.ERROR)
    
    # Run tests
    unittest.main(verbosity=2)