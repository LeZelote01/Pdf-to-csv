"""
File handling utilities for PDF to CSV processor
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import mimetypes
import hashlib
import pandas as pd

from src.utils.logger import setup_logger

class FileHandler:
    """Handles file operations for PDF processing"""
    
    def __init__(self):
        """Initialize file handler"""
        self.logger = setup_logger(__name__)
        
        # Supported file types
        self.supported_pdf_extensions = ['.pdf']
        self.output_extensions = ['.csv', '.xlsx', '.json', '.txt']
    
    def validate_pdf(self, file_path: str) -> bool:
        """
        Validate if file is a readable PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                self.logger.error(f"File does not exist: {file_path}")
                return False
            
            # Check file extension
            if file_path.suffix.lower() not in self.supported_pdf_extensions:
                self.logger.error(f"Unsupported file extension: {file_path.suffix}")
                return False
            
            # Check file size (not empty, not too large)
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.logger.error("File is empty")
                return False
            
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                self.logger.warning(f"Large file detected: {file_size / (1024*1024):.1f}MB")
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type != 'application/pdf':
                self.logger.warning(f"Unexpected MIME type: {mime_type}")
            
            # Try to read first few bytes
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    self.logger.error("File does not appear to be a valid PDF")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"PDF validation failed: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed file information
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {}
            
            stat = file_path.stat()
            
            info = {
                'filename': file_path.name,
                'full_path': str(file_path.absolute()),
                'size_bytes': stat.st_size,
                'size_human': self._format_file_size(stat.st_size),
                'extension': file_path.suffix.lower(),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK)
            }
            
            # Add file hash for verification
            if stat.st_size < 50 * 1024 * 1024:  # Only for files < 50MB
                info['md5_hash'] = self._calculate_file_hash(file_path)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get file info: {str(e)}")
            return {}
    
    def find_pdf_files(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Find all PDF files in directory
        
        Args:
            directory: Directory to search
            recursive: Search subdirectories
            
        Returns:
            List of PDF file paths
        """
        try:
            directory = Path(directory)
            
            if not directory.exists() or not directory.is_dir():
                self.logger.error(f"Invalid directory: {directory}")
                return []
            
            pdf_files = []
            
            if recursive:
                # Recursive search
                pdf_files = list(directory.rglob("*.pdf"))
            else:
                # Current directory only
                pdf_files = list(directory.glob("*.pdf"))
            
            # Convert to strings and validate
            valid_files = []
            for pdf_file in pdf_files:
                if self.validate_pdf(str(pdf_file)):
                    valid_files.append(str(pdf_file))
            
            self.logger.info(f"Found {len(valid_files)} valid PDF files in {directory}")
            return valid_files
            
        except Exception as e:
            self.logger.error(f"Failed to find PDF files: {str(e)}")
            return []
    
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
            
            # Create directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup existing file
            if output_path.exists():
                backup_path = output_path.with_suffix(f".backup{output_path.suffix}")
                shutil.copy2(output_path, backup_path)
                self.logger.debug(f"Created backup: {backup_path}")
            
            # Write CSV data
            with open(output_path, 'w', encoding=encoding, newline='') as f:
                f.write(csv_data)
            
            # Verify file was written correctly
            if output_path.exists() and output_path.stat().st_size > 0:
                self.logger.info(f"CSV saved successfully: {output_path}")
                return True
            else:
                self.logger.error("File was not written correctly")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {str(e)}")
            return False
    
    def create_output_directory(self, base_path: str, create_timestamp_dir: bool = False) -> str:
        """
        Create output directory structure
        
        Args:
            base_path: Base output path
            create_timestamp_dir: Create timestamped subdirectory
            
        Returns:
            Created directory path
        """
        try:
            base_path = Path(base_path)
            
            if create_timestamp_dir:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = base_path / f"output_{timestamp}"
            else:
                output_dir = base_path
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Output directory created: {output_dir}")
            return str(output_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {str(e)}")
            return str(base_path)
    
    def cleanup_temp_files(self, temp_dir: str) -> bool:
        """
        Clean up temporary files
        
        Args:
            temp_dir: Temporary directory path
            
        Returns:
            Success status
        """
        try:
            temp_path = Path(temp_dir)
            
            if temp_path.exists() and temp_path.is_dir():
                shutil.rmtree(temp_path)
                self.logger.info(f"Cleaned up temporary directory: {temp_path}")
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {str(e)}")
            return False
    
    def backup_file(self, file_path: str, backup_dir: Optional[str] = None) -> Optional[str]:
        """
        Create backup of file
        
        Args:
            file_path: File to backup
            backup_dir: Optional backup directory
            
        Returns:
            Backup file path if successful, None otherwise
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            if backup_dir:
                backup_dir = Path(backup_dir)
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / file_path.name
            else:
                backup_path = file_path.with_suffix(f".backup{file_path.suffix}")
            
            shutil.copy2(file_path, backup_path)
            
            self.logger.debug(f"Created backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {str(e)}")
            return None
    
    def validate_output_path(self, output_path: str, overwrite: bool = False) -> bool:
        """
        Validate output path
        
        Args:
            output_path: Output file path
            overwrite: Allow overwriting existing files
            
        Returns:
            True if path is valid, False otherwise
        """
        try:
            output_path = Path(output_path)
            
            # Check if parent directory exists or can be created
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"Cannot create output directory: {str(e)}")
                return False
            
            # Check if file exists and overwrite policy
            if output_path.exists() and not overwrite:
                self.logger.error(f"File already exists and overwrite not allowed: {output_path}")
                return False
            
            # Check write permissions
            if output_path.exists():
                if not os.access(output_path, os.W_OK):
                    self.logger.error(f"No write permission for file: {output_path}")
                    return False
            else:
                # Check parent directory write permission
                if not os.access(output_path.parent, os.W_OK):
                    self.logger.error(f"No write permission for directory: {output_path.parent}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Output path validation failed: {str(e)}")
            return False
    
    def get_safe_filename(self, filename: str, max_length: int = 255) -> str:
        """
        Generate safe filename by removing invalid characters
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Safe filename
        """
        try:
            # Remove invalid characters
            invalid_chars = '<>:"/\\|?*'
            safe_name = ''.join(c for c in filename if c not in invalid_chars)
            
            # Replace spaces with underscores
            safe_name = safe_name.replace(' ', '_')
            
            # Limit length
            if len(safe_name) > max_length:
                name_part = safe_name[:max_length-10]  # Leave room for extension
                extension = Path(safe_name).suffix
                safe_name = name_part + extension
            
            return safe_name
            
        except Exception as e:
            self.logger.error(f"Failed to generate safe filename: {str(e)}")
            return "output.csv"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        try:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except:
            return f"{size_bytes} B"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate file hash: {str(e)}")
            return ""
    
    def export_dataframe_multiple_formats(self, df: pd.DataFrame, base_path: str, 
                                        formats: List[str] = None) -> Dict[str, bool]:
        """
        Export DataFrame to multiple formats
        
        Args:
            df: DataFrame to export
            base_path: Base file path (without extension)
            formats: List of formats to export (csv, xlsx, json)
            
        Returns:
            Dictionary of export results
        """
        try:
            if formats is None:
                formats = ['csv', 'xlsx', 'json']
            
            base_path = Path(base_path)
            results = {}
            
            for fmt in formats:
                try:
                    output_path = base_path.with_suffix(f'.{fmt}')
                    
                    if fmt == 'csv':
                        df.to_csv(output_path, index=False, encoding='utf-8')
                    elif fmt == 'xlsx':
                        df.to_excel(output_path, index=False)
                    elif fmt == 'json':
                        df.to_json(output_path, orient='records', indent=2)
                    else:
                        results[fmt] = False
                        continue
                    
                    results[fmt] = True
                    self.logger.info(f"Exported to {fmt}: {output_path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to export to {fmt}: {str(e)}")
                    results[fmt] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Multiple format export failed: {str(e)}")
            return {fmt: False for fmt in (formats or [])}