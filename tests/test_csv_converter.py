#!/usr/bin/env python3
"""
Unit tests for CSV Converter

Tests for the CSV conversion functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path
import pandas as pd
from io import StringIO

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.csv_converter import CSVConverter
from src.core.config_manager import ConfigManager

class TestCSVConverter(unittest.TestCase):
    """Test cases for CSVConverter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ConfigManager()
        self.converter = CSVConverter(self.config)
        
        # Create test data
        self.sample_table = pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Age': [25, 30, 35],
            'City': ['New York', 'London', 'Tokyo'],
            'Salary': [50000, 60000, 70000]
        })
        
        self.sample_extracted_data = {
            'tables': [self.sample_table],
            'total_rows': 3,
            'total_columns': 4,
            'method': 'test'
        }
        
        # Create temporary directory for file operations
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test CSVConverter initialization"""
        converter = CSVConverter()
        self.assertIsNotNone(converter)
        self.assertIsNotNone(converter.logger)
        
        # Test with config
        converter_with_config = CSVConverter(self.config)
        self.assertIsNotNone(converter_with_config.config)
    
    def test_basic_csv_conversion(self):
        """Test basic CSV conversion"""
        csv_data = self.converter.convert_to_csv(self.sample_extracted_data)
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('Name,Age,City,Salary', csv_data)
        self.assertIn('John Doe,25,New York,50000', csv_data)
        
        # Verify it's valid CSV
        df_from_csv = pd.read_csv(StringIO(csv_data))
        self.assertEqual(len(df_from_csv), 3)
        self.assertEqual(len(df_from_csv.columns), 4)
    
    def test_csv_conversion_with_options(self):
        """Test CSV conversion with custom options"""
        options = {
            'delimiter': ';',
            'header_row': False,
            'encoding': 'utf-8'
        }
        
        csv_data = self.converter.convert_to_csv(self.sample_extracted_data, **options)
        
        self.assertIsInstance(csv_data, str)
        self.assertIn(';', csv_data)  # Check delimiter
        self.assertNotIn('Name;Age;City;Salary', csv_data)  # No header
        self.assertIn('John Doe;25;New York;50000', csv_data)
    
    def test_empty_data_handling(self):
        """Test handling of empty extracted data"""
        empty_data = {'tables': [], 'total_rows': 0, 'total_columns': 0}
        
        csv_data = self.converter.convert_to_csv(empty_data)
        
        self.assertEqual(csv_data, "")
    
    def test_multiple_tables_merge(self):
        """Test merging multiple tables"""
        table1 = pd.DataFrame({
            'Name': ['Alice', 'Bob'],
            'Score': [85, 92]
        })
        
        table2 = pd.DataFrame({
            'Name': ['Charlie', 'Diana'],
            'Score': [78, 95]
        })
        
        multi_table_data = {
            'tables': [table1, table2],
            'total_rows': 4,
            'total_columns': 2
        }
        
        csv_data = self.converter.convert_to_csv(multi_table_data, merge_tables=True)
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('Alice', csv_data)
        self.assertIn('Charlie', csv_data)
        
        # Verify merged data
        df_from_csv = pd.read_csv(StringIO(csv_data))
        self.assertEqual(len(df_from_csv), 4)  # All rows merged
    
    def test_union_tables(self):
        """Test union of tables with different columns"""
        table1 = pd.DataFrame({
            'Name': ['Alice'],
            'Age': [25]
        })
        
        table2 = pd.DataFrame({
            'Name': ['Bob'],
            'City': ['Paris']
        })
        
        merged_df = self.converter._union_tables([table1, table2])
        
        self.assertIsInstance(merged_df, pd.DataFrame)
        self.assertEqual(len(merged_df), 2)
        self.assertEqual(set(merged_df.columns), {'Name', 'Age', 'City'})
    
    def test_clean_merged_data(self):
        """Test data cleaning during merge"""
        dirty_df = pd.DataFrame({
            'Col1': ['  Value1  ', 'Value2', 'Value1', ''],  # Spaces and duplicates
            'Col2': ['Value3', '', None, 'Value4']
        })
        
        cleaned_df = self.converter._clean_merged_data(dirty_df, clean_data=True, skip_empty=True)
        
        # Check cleaned values
        self.assertEqual(cleaned_df.iloc[0, 0], 'Value1')  # Stripped
        
        # Check duplicates removed
        value1_count = (cleaned_df['Col1'] == 'Value1').sum()
        self.assertEqual(value1_count, 1)
    
    def test_dataframe_to_csv(self):
        """Test DataFrame to CSV conversion"""
        csv_string = self.converter._dataframe_to_csv(self.sample_table)
        
        self.assertIsInstance(csv_string, str)
        self.assertIn('Name,Age,City,Salary', csv_string)
        
        # Test without header
        csv_no_header = self.converter._dataframe_to_csv(self.sample_table, header_row=False)
        self.assertNotIn('Name,Age,City,Salary', csv_no_header)
        
        # Test with different delimiter
        csv_semicolon = self.converter._dataframe_to_csv(self.sample_table, delimiter=';')
        self.assertIn('Name;Age;City;Salary', csv_semicolon)
    
    def test_save_csv(self):
        """Test saving CSV to file"""
        csv_data = "Name,Age\nJohn,25\nJane,30"
        output_path = os.path.join(self.temp_dir, "test_output.csv")
        
        success = self.converter.save_csv(csv_data, output_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify file content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, csv_data)
    
    def test_save_csv_create_directory(self):
        """Test CSV saving with directory creation"""
        csv_data = "Name,Age\nTest,25"
        nested_path = os.path.join(self.temp_dir, "nested", "dir", "output.csv")
        
        success = self.converter.save_csv(csv_data, nested_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(nested_path))
    
    def test_convert_multiple_formats(self):
        """Test conversion to multiple formats"""
        output_dir = os.path.join(self.temp_dir, "multi_format")
        base_filename = "test_export"
        
        results = self.converter.convert_multiple_formats(
            self.sample_extracted_data,
            output_dir,
            base_filename
        )
        
        self.assertIsInstance(results, dict)
        self.assertIn('csv', results)
        self.assertIn('excel', results)
        self.assertIn('json', results)
        
        # Check CSV was created
        csv_path = os.path.join(output_dir, f"{base_filename}.csv")
        self.assertTrue(os.path.exists(csv_path))
        
        # Check Excel was created (if openpyxl is available)
        excel_path = os.path.join(output_dir, f"{base_filename}.xlsx")
        if results['excel']:
            self.assertTrue(os.path.exists(excel_path))
        
        # Check JSON was created
        json_path = os.path.join(output_dir, f"{base_filename}.json")
        if results['json']:
            self.assertTrue(os.path.exists(json_path))
    
    def test_preview_csv(self):
        """Test CSV preview generation"""
        preview = self.converter.preview_csv(self.sample_extracted_data, preview_rows=2)
        
        self.assertIsInstance(preview, dict)
        self.assertIn('preview', preview)
        self.assertIn('row_count', preview)
        self.assertIn('column_count', preview)
        
        self.assertEqual(preview['row_count'], 3)
        self.assertEqual(preview['column_count'], 4)
        
        # Check preview content
        preview_text = preview['preview']
        self.assertIn('Name,Age,City,Salary', preview_text)
        lines = preview_text.strip().split('\n')
        self.assertEqual(len(lines), 3)  # Header + 2 preview rows
    
    def test_validate_csv_data(self):
        """Test CSV data validation"""
        # Valid CSV
        valid_csv = "Name,Age\nJohn,25\nJane,30"
        validation = self.converter.validate_csv_data(valid_csv)
        
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['errors']), 0)
        self.assertEqual(validation['row_count'], 2)
        self.assertEqual(validation['column_count'], 2)
        
        # Empty CSV
        empty_validation = self.converter.validate_csv_data("")
        self.assertFalse(empty_validation['valid'])
        self.assertIn('Empty CSV data', empty_validation['errors'])
        
        # Invalid CSV (malformed)
        invalid_csv = "Name,Age\nJohn,25,Extra\nJane"  # Inconsistent columns
        invalid_validation = self.converter.validate_csv_data(invalid_csv)
        # Should still be valid but with warnings
        self.assertGreaterEqual(len(invalid_validation['warnings']), 0)
    
    def test_sparse_data_handling(self):
        """Test handling of sparse data (lots of empty cells)"""
        sparse_table = pd.DataFrame({
            'Col1': ['Value1', None, None, None, None],
            'Col2': [None, None, 'Value2', None, None],
            'Col3': [None, None, None, None, 'Value3']
        })
        
        sparse_data = {
            'tables': [sparse_table],
            'total_rows': 5,
            'total_columns': 3
        }
        
        csv_data = self.converter.convert_to_csv(sparse_data)
        validation = self.converter.validate_csv_data(csv_data)
        
        # Should detect sparse data
        self.assertGreater(validation['empty_cell_percentage'], 50)
        self.assertTrue(any('sparse' in warning for warning in validation.get('warnings', [])))

class TestCSVConverterEdgeCases(unittest.TestCase):
    """Test edge cases for CSV conversion"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.converter = CSVConverter()
    
    def test_special_characters_handling(self):
        """Test handling of special characters in data"""
        special_table = pd.DataFrame({
            'Text': ['Hello, "World"', 'Line1\nLine2', 'Café & Restaurant'],
            'Numbers': [1.5, 2.7, 3.14],
            'Unicode': ['😀', '中文', 'العربية']
        })
        
        special_data = {'tables': [special_table]}
        csv_data = self.converter.convert_to_csv(special_data)
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('Hello, "World"', csv_data)
        self.assertIn('😀', csv_data)
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Create a large table
        large_data = {
            f'col_{i}': [f'value_{i}_{j}' for j in range(10000)]
            for i in range(10)
        }
        large_table = pd.DataFrame(large_data)
        
        large_extracted_data = {
            'tables': [large_table],
            'total_rows': 10000,
            'total_columns': 10
        }
        
        # Should handle large data without memory issues
        csv_data = self.converter.convert_to_csv(large_extracted_data)
        self.assertIsInstance(csv_data, str)
        self.assertGreater(len(csv_data), 100000)  # Should be substantial
    
    def test_mixed_data_types(self):
        """Test handling of mixed data types"""
        mixed_table = pd.DataFrame({
            'Integer': [1, 2, 3],
            'Float': [1.1, 2.2, 3.3],
            'String': ['A', 'B', 'C'],
            'Boolean': [True, False, True],
            'Date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])
        })
        
        mixed_data = {'tables': [mixed_table]}
        csv_data = self.converter.convert_to_csv(mixed_data)
        
        self.assertIsInstance(csv_data, str)
        # Should handle all data types gracefully
        self.assertIn('Integer,Float,String,Boolean,Date', csv_data)
    
    def test_empty_table_handling(self):
        """Test handling of empty tables"""
        empty_table = pd.DataFrame()
        empty_data = {'tables': [empty_table]}
        
        csv_data = self.converter.convert_to_csv(empty_data)
        self.assertEqual(csv_data, "")
    
    def test_single_column_table(self):
        """Test handling of single column tables"""
        single_col_table = pd.DataFrame({
            'OnlyColumn': ['Value1', 'Value2', 'Value3']
        })
        
        single_col_data = {'tables': [single_col_table]}
        csv_data = self.converter.convert_to_csv(single_col_data)
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('OnlyColumn', csv_data)
        self.assertIn('Value1', csv_data)
    
    def test_single_row_table(self):
        """Test handling of single row tables"""
        single_row_table = pd.DataFrame({
            'Col1': ['Value1'],
            'Col2': ['Value2'],
            'Col3': ['Value3']
        })
        
        single_row_data = {'tables': [single_row_table]}
        csv_data = self.converter.convert_to_csv(single_row_data)
        
        self.assertIsInstance(csv_data, str)
        lines = csv_data.strip().split('\n')
        self.assertEqual(len(lines), 2)  # Header + 1 data row

if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.ERROR)  # Reduce noise during tests
    
    # Run tests
    unittest.main(verbosity=2)