"""
Configuration Manager

Handles loading and management of configuration settings for the PDF processor.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os

from src.utils.logger import setup_logger

class ConfigManager:
    """Manages configuration settings for PDF processing"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Optional path to config file
        """
        self.logger = setup_logger(__name__)
        self.config_data = {}
        
        # Default configuration
        self.default_config = {
            'extraction_method': 'auto',
            'table_detection': True,
            'text_patterns': ['table', 'form', 'structured'],
            'output_format': {
                'delimiter': ',',
                'encoding': 'utf-8',
                'header_row': True
            },
            'processing': {
                'clean_data': True,
                'merge_cells': True,
                'skip_empty_rows': True,
                'ocr_enabled': False
            },
            'advanced': {
                'verbose_logging': False,
                'parallel_processing': True,
                'max_workers': 4,
                'chunk_size': 1000
            }
        }
        
        # Load configuration
        if config_path:
            self.load_config(config_path)
        else:
            self.load_default_config()
    
    def load_config(self, config_path: str) -> bool:
        """
        Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Success status
        """
        try:
            config_path = Path(config_path)
            
            if not config_path.exists():
                self.logger.warning(f"Config file not found: {config_path}")
                self.load_default_config()
                return False
            
            # Determine file format
            suffix = config_path.suffix.lower()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if suffix == '.json':
                    config_data = json.load(f)
                elif suffix in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                else:
                    self.logger.error(f"Unsupported config format: {suffix}")
                    self.load_default_config()
                    return False
            
            # Merge with defaults
            self.config_data = self._merge_config(self.default_config, config_data)
            
            self.logger.info(f"Configuration loaded from: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            self.load_default_config()
            return False
    
    def load_default_config(self):
        """Load default configuration"""
        self.config_data = self.default_config.copy()
        self.logger.info("Using default configuration")
    
    def save_config(self, config_path: str, config_data: Optional[Dict] = None) -> bool:
        """
        Save configuration to file
        
        Args:
            config_path: Path to save config file
            config_data: Optional config data (uses current if None)
            
        Returns:
            Success status
        """
        try:
            config_path = Path(config_path)
            config_data = config_data or self.config_data
            
            # Create directory if needed
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine format from extension
            suffix = config_path.suffix.lower()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if suffix == '.json':
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                elif suffix in ['.yaml', '.yml']:
                    yaml.dump(config_data, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
                else:
                    # Default to JSON
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            
        Returns:
            Success status
        """
        try:
            keys = key.split('.')
            config = self.config_data
            
            # Navigate to parent
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set value
            config[keys[-1]] = value
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set config value {key}: {str(e)}")
            return False
    
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """
        Merge user config with default config
        
        Args:
            default: Default configuration
            user: User configuration
            
        Returns:
            Merged configuration
        """
        try:
            merged = default.copy()
            
            for key, value in user.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = self._merge_config(merged[key], value)
                else:
                    merged[key] = value
            
            return merged
            
        except Exception as e:
            self.logger.error(f"Config merge failed: {str(e)}")
            return default
    
    def get_extraction_config(self) -> Dict[str, Any]:
        """Get extraction-specific configuration"""
        return {
            'method': self.get('extraction_method', 'auto'),
            'table_detection': self.get('table_detection', True),
            'text_patterns': self.get('text_patterns', ['table']),
            'tabula_options': self.get('extraction_methods.tabula', {}),
            'camelot_options': self.get('extraction_methods.camelot', {}),
            'pdfplumber_options': self.get('extraction_methods.pdfplumber', {}),
            'ocr_settings': self.get('ocr_settings', {})
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output-specific configuration"""
        return {
            'delimiter': self.get('output_format.delimiter', ','),
            'encoding': self.get('output_format.encoding', 'utf-8'),
            'header_row': self.get('output_format.header_row', True),
            'clean_data': self.get('processing.clean_data', True),
            'merge_cells': self.get('processing.merge_cells', True),
            'skip_empty_rows': self.get('processing.skip_empty_rows', True)
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing-specific configuration"""
        return {
            'verbose_logging': self.get('advanced.verbose_logging', False),
            'parallel_processing': self.get('advanced.parallel_processing', True),
            'max_workers': self.get('advanced.max_workers', 4),
            'chunk_size': self.get('advanced.chunk_size', 1000),
            'ocr_enabled': self.get('processing.ocr_enabled', False)
        }
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Update multiple settings at once
        
        Args:
            settings: Dictionary of settings to update
            
        Returns:
            Success status
        """
        try:
            for key, value in settings.items():
                self.set(key, value)
            
            self.logger.info("Settings updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update settings: {str(e)}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config_data = self.default_config.copy()
            self.logger.info("Configuration reset to defaults")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset config: {str(e)}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate current configuration
        
        Returns:
            Validation results
        """
        try:
            errors = []
            warnings = []
            
            # Check required fields
            required_fields = [
                'extraction_method',
                'output_format.delimiter',
                'output_format.encoding'
            ]
            
            for field in required_fields:
                if self.get(field) is None:
                    errors.append(f"Missing required field: {field}")
            
            # Check extraction method
            valid_methods = ['auto', 'tabula', 'camelot', 'pdfplumber', 'pypdf2']
            if self.get('extraction_method') not in valid_methods:
                errors.append(f"Invalid extraction method. Must be one of: {valid_methods}")
            
            # Check encoding
            try:
                'test'.encode(self.get('output_format.encoding', 'utf-8'))
            except LookupError:
                errors.append(f"Invalid encoding: {self.get('output_format.encoding')}")
            
            # Check max_workers
            max_workers = self.get('advanced.max_workers', 4)
            if not isinstance(max_workers, int) or max_workers < 1:
                warnings.append("max_workers should be a positive integer")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Config validation failed: {str(e)}"],
                'warnings': []
            }
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings"""
        return self.config_data.copy()
    
    def export_settings(self, export_path: str) -> bool:
        """
        Export current settings to file
        
        Args:
            export_path: Path to export file
            
        Returns:
            Success status
        """
        return self.save_config(export_path, self.config_data)