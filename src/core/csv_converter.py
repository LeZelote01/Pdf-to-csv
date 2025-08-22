"""
CSV Converter

Handles conversion of extracted PDF data to CSV format with various options.
"""

import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import csv
from io import StringIO

from src.utils.logger import setup_logger

class CSVConverter:
    """Converts extracted PDF data to CSV format"""
    
    def __init__(self, config_manager=None):
        """Initialize CSV converter with configuration"""
        self.config = config_manager
        self.logger = setup_logger(__name__)
    
    def convert_to_csv(self, extracted_data: Dict[str, Any], **kwargs) -> str:
        """
        Convert extracted data to CSV format
        
        Args:
            extracted_data: Data extracted from PDF
            **kwargs: Conversion options
            
        Returns:
            CSV data as string
        """
        try:
            tables = extracted_data.get('tables', [])
            
            if not tables:
                self.logger.warning("No tables found in extracted data")
                return ""
            
            # Get conversion options
            delimiter = kwargs.get('delimiter', ',')
            encoding = kwargs.get('encoding', 'utf-8')
            header_row = kwargs.get('header_row', True)
            merge_tables = kwargs.get('merge_tables', len(tables) > 1)
            
            if merge_tables and len(tables) > 1:
                # Merge multiple tables
                merged_df = self._merge_tables(tables, **kwargs)
                csv_data = self._dataframe_to_csv(merged_df, delimiter, header_row)
            else:
                # Convert first table or handle single table
                main_table = tables[0] if tables else pd.DataFrame()
                csv_data = self._dataframe_to_csv(main_table, delimiter, header_row)
            
            self.logger.info(f"Successfully converted to CSV format")
            return csv_data
            
        except Exception as e:
            self.logger.error(f"CSV conversion failed: {str(e)}")
            raise
    
    def _merge_tables(self, tables: List[pd.DataFrame], **kwargs) -> pd.DataFrame:
        """
        Merge multiple tables into a single DataFrame
        
        Args:
            tables: List of DataFrames to merge
            **kwargs: Merge options
            
        Returns:
            Merged DataFrame
        """
        try:
            merge_method = kwargs.get('merge_method', 'concat')
            
            if merge_method == 'concat':
                # Simple concatenation
                merged_df = pd.concat(tables, ignore_index=True, sort=False)
            
            elif merge_method == 'union':
                # Union by columns (align columns)
                merged_df = self._union_tables(tables)
            
            else:
                # Default to concatenation
                merged_df = pd.concat(tables, ignore_index=True, sort=False)
            
            # Clean merged data
            merged_df = self._clean_merged_data(merged_df, **kwargs)
            
            self.logger.debug(f"Merged {len(tables)} tables into single DataFrame")
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Table merging failed: {str(e)}")
            # Return first table as fallback
            return tables[0] if tables else pd.DataFrame()
    
    def _union_tables(self, tables: List[pd.DataFrame]) -> pd.DataFrame:
        """Union tables by aligning columns"""
        try:
            if not tables:
                return pd.DataFrame()
            
            # Get all unique columns
            all_columns = set()
            for table in tables:
                all_columns.update(table.columns)
            
            all_columns = sorted(list(all_columns))
            
            # Align all tables to have same columns
            aligned_tables = []
            for table in tables:
                aligned_table = table.reindex(columns=all_columns, fill_value='')
                aligned_tables.append(aligned_table)
            
            # Concatenate aligned tables
            merged_df = pd.concat(aligned_tables, ignore_index=True)
            
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Table union failed: {str(e)}")
            return pd.concat(tables, ignore_index=True, sort=False)
    
    def _clean_merged_data(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """Clean merged DataFrame"""
        try:
            clean_data = kwargs.get('clean_data', True)
            skip_empty = kwargs.get('skip_empty', True)
            
            if clean_data:
                # Remove duplicates
                df = df.drop_duplicates()
                
                # Clean text data
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace('nan', '')
                    df[col] = df[col].replace('', pd.NA)
            
            if skip_empty:
                # Remove rows that are completely empty
                df = df.dropna(how='all')
            
            # Reset index
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Data cleaning failed: {str(e)}")
            return df
    
    def _dataframe_to_csv(self, df: pd.DataFrame, delimiter: str = ',', 
                         header_row: bool = True) -> str:
        """Convert DataFrame to CSV string"""
        try:
            if df.empty:
                return ""
            
            # Create CSV string
            output = StringIO()
            df.to_csv(
                output,
                sep=delimiter,
                index=False,
                header=header_row,
                na_rep='',
                quoting=csv.QUOTE_MINIMAL
            )
            
            csv_data = output.getvalue()
            output.close()
            
            return csv_data
            
        except Exception as e:
            self.logger.error(f"DataFrame to CSV conversion failed: {str(e)}")
            raise
    
    def save_csv(self, csv_data: str, output_path: str, encoding: str = 'utf-8') -> bool:
        """
        Save CSV data to file
        
        Args:
            csv_data: CSV data as string
            output_path: Output file path
            encoding: File encoding
            
        Returns:
            Success status
        """
        try:
            if not csv_data:
                self.logger.warning("No CSV data to save")
                return False
            
            output_path = Path(output_path)
            
            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write CSV data
            with open(output_path, 'w', encoding=encoding, newline='') as f:
                f.write(csv_data)
            
            self.logger.info(f"CSV saved successfully: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {str(e)}")
            return False
    
    def convert_multiple_formats(self, extracted_data: Dict[str, Any], 
                                output_dir: str, base_filename: str, 
                                **kwargs) -> Dict[str, bool]:
        """
        Convert extracted data to multiple formats
        
        Args:
            extracted_data: Extracted PDF data
            output_dir: Output directory
            base_filename: Base filename without extension
            **kwargs: Conversion options
            
        Returns:
            Dictionary of format success status
        """
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            results = {}
            tables = extracted_data.get('tables', [])
            
            if not tables:
                return {'csv': False, 'excel': False, 'json': False}
            
            main_table = tables[0] if len(tables) == 1 else self._merge_tables(tables, **kwargs)
            
            # CSV format
            try:
                csv_data = self._dataframe_to_csv(main_table, **kwargs)
                csv_path = output_dir / f"{base_filename}.csv"
                results['csv'] = self.save_csv(csv_data, str(csv_path), kwargs.get('encoding', 'utf-8'))
            except Exception as e:
                self.logger.error(f"CSV export failed: {str(e)}")
                results['csv'] = False
            
            # Excel format
            try:
                excel_path = output_dir / f"{base_filename}.xlsx"
                main_table.to_excel(str(excel_path), index=False)
                results['excel'] = True
                self.logger.info(f"Excel saved: {excel_path}")
            except Exception as e:
                self.logger.error(f"Excel export failed: {str(e)}")
                results['excel'] = False
            
            # JSON format
            try:
                json_path = output_dir / f"{base_filename}.json"
                main_table.to_json(str(json_path), orient='records', indent=2)
                results['json'] = True
                self.logger.info(f"JSON saved: {json_path}")
            except Exception as e:
                self.logger.error(f"JSON export failed: {str(e)}")
                results['json'] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Multiple format conversion failed: {str(e)}")
            return {'csv': False, 'excel': False, 'json': False}
    
    def preview_csv(self, extracted_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Generate preview of CSV conversion
        
        Args:
            extracted_data: Extracted PDF data
            **kwargs: Preview options
            
        Returns:
            Preview information
        """
        try:
            tables = extracted_data.get('tables', [])
            
            if not tables:
                return {'preview': '', 'row_count': 0, 'column_count': 0}
            
            # Use first table for preview
            main_table = tables[0]
            
            # Limit preview rows
            preview_rows = kwargs.get('preview_rows', 10)
            preview_table = main_table.head(preview_rows)
            
            # Generate CSV preview
            csv_preview = self._dataframe_to_csv(preview_table, **kwargs)
            
            # Get statistics
            stats = {
                'preview': csv_preview,
                'row_count': len(main_table),
                'column_count': len(main_table.columns),
                'columns': list(main_table.columns),
                'total_tables': len(tables)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"CSV preview failed: {str(e)}")
            return {'preview': '', 'row_count': 0, 'column_count': 0}
    
    def validate_csv_data(self, csv_data: str) -> Dict[str, Any]:
        """
        Validate CSV data quality
        
        Args:
            csv_data: CSV data string
            
        Returns:
            Validation results
        """
        try:
            if not csv_data:
                return {'valid': False, 'errors': ['Empty CSV data']}
            
            # Try to parse CSV
            df = pd.read_csv(StringIO(csv_data))
            
            errors = []
            warnings = []
            
            # Check for empty DataFrame
            if df.empty:
                errors.append("CSV contains no data rows")
            
            # Check for completely empty columns
            empty_cols = df.columns[df.isnull().all()].tolist()
            if empty_cols:
                warnings.append(f"Empty columns found: {empty_cols}")
            
            # Check for very sparse data
            total_cells = df.size
            empty_cells = df.isnull().sum().sum()
            if total_cells > 0 and (empty_cells / total_cells) > 0.8:
                warnings.append("Data appears to be very sparse (>80% empty cells)")
            
            # Check for inconsistent row lengths
            lines = csv_data.strip().split('\n')
            if len(lines) > 1:
                first_row_cols = len(lines[0].split(','))
                inconsistent_rows = [i for i, line in enumerate(lines[1:], 1) 
                                   if len(line.split(',')) != first_row_cols]
                if inconsistent_rows:
                    warnings.append(f"Inconsistent column count in rows: {inconsistent_rows[:5]}")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'row_count': len(df),
                'column_count': len(df.columns),
                'empty_cell_percentage': (empty_cells / total_cells * 100) if total_cells > 0 else 0
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"CSV validation failed: {str(e)}"],
                'warnings': []
            }