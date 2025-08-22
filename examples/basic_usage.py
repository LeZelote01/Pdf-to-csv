#!/usr/bin/env python3
"""
Basic Usage Examples for PDF to CSV Processor

This file demonstrates basic usage patterns for the PDF to CSV data processor.
Run these examples to understand how to use the library programmatically.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pdf_extractor import PDFExtractor
from src.core.csv_converter import CSVConverter
from src.core.config_manager import ConfigManager
from src.utils.file_handler import FileHandler
from src.utils.logger import setup_logger

def basic_pdf_to_csv_conversion():
    """Example 1: Basic PDF to CSV conversion"""
    print("="*60)
    print("Example 1: Basic PDF to CSV Conversion")
    print("="*60)
    
    # Initialize components
    config = ConfigManager()
    extractor = PDFExtractor(config)
    converter = CSVConverter(config)
    file_handler = FileHandler()
    
    # Example PDF file path (replace with your PDF)
    pdf_path = "sample_data.pdf"
    output_path = "output_data.csv"
    
    try:
        # Step 1: Validate PDF
        if not file_handler.validate_pdf(pdf_path):
            print(f"❌ Invalid PDF file: {pdf_path}")
            print("Please ensure you have a valid PDF file to process.")
            return
        
        # Step 2: Extract data from PDF
        print(f"📄 Processing PDF: {pdf_path}")
        extracted_data = extractor.extract_data(pdf_path)
        
        if not extracted_data or not extracted_data.get('tables'):
            print("❌ No data extracted from PDF")
            return
        
        print(f"✅ Extracted {len(extracted_data['tables'])} tables")
        print(f"   Total rows: {extracted_data.get('total_rows', 0)}")
        print(f"   Total columns: {extracted_data.get('total_columns', 0)}")
        
        # Step 3: Convert to CSV
        print("🔄 Converting to CSV...")
        csv_data = converter.convert_to_csv(extracted_data)
        
        # Step 4: Save CSV file
        success = file_handler.save_csv(csv_data, output_path)
        
        if success:
            print(f"✅ CSV saved successfully: {output_path}")
        else:
            print("❌ Failed to save CSV file")
    
    except FileNotFoundError:
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please create a sample PDF file or modify the path.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def advanced_extraction_with_options():
    """Example 2: Advanced extraction with custom options"""
    print("="*60)
    print("Example 2: Advanced Extraction with Options")
    print("="*60)
    
    # Load custom configuration
    config = ConfigManager("examples/sample_config.json")
    extractor = PDFExtractor(config)
    converter = CSVConverter(config)
    
    pdf_path = "sample_report.pdf"
    
    try:
        # Extract with specific options
        extraction_options = {
            'method': 'tabula',  # Force specific method
            'pages': '1-3',      # Only process first 3 pages
            'pattern': 'table',  # Look for table patterns
            'lattice': True      # Use lattice detection
        }
        
        print(f"📄 Processing PDF with custom options: {pdf_path}")
        extracted_data = extractor.extract_data(pdf_path, **extraction_options)
        
        if extracted_data and extracted_data.get('tables'):
            print(f"✅ Extraction successful!")
            print(f"   Method used: {extracted_data.get('method', 'unknown')}")
            print(f"   Pages processed: {extracted_data.get('pages', 'all')}")
            print(f"   Tables found: {len(extracted_data['tables'])}")
            
            # Convert with custom CSV options
            csv_options = {
                'delimiter': ';',      # Use semicolon delimiter
                'encoding': 'utf-8',   # Specify encoding
                'header_row': True,    # Include headers
                'clean_data': True     # Clean the data
            }
            
            csv_data = converter.convert_to_csv(extracted_data, **csv_options)
            
            # Save with custom filename
            output_path = f"advanced_output_{extraction_options['method']}.csv"
            FileHandler().save_csv(csv_data, output_path)
            print(f"✅ Advanced CSV saved: {output_path}")
        
        else:
            print("❌ No data extracted")
    
    except FileNotFoundError:
        print(f"❌ PDF file not found: {pdf_path}")
        print("This is expected if you don't have the sample file.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def batch_processing_example():
    """Example 3: Batch processing multiple PDFs"""
    print("="*60)
    print("Example 3: Batch Processing Multiple PDFs")
    print("="*60)
    
    config = ConfigManager()
    extractor = PDFExtractor(config)
    converter = CSVConverter(config)
    file_handler = FileHandler()
    
    # Directory containing PDF files
    input_dir = "sample_pdfs"
    output_dir = "batch_output"
    
    try:
        # Find all PDF files
        pdf_files = file_handler.find_pdf_files(input_dir, recursive=True)
        
        if not pdf_files:
            print(f"❌ No PDF files found in: {input_dir}")
            print("Please create a directory with sample PDF files.")
            return
        
        print(f"📁 Found {len(pdf_files)} PDF files to process")
        
        # Create output directory
        output_path = file_handler.create_output_directory(output_dir, create_timestamp_dir=True)
        
        success_count = 0
        
        for i, pdf_path in enumerate(pdf_files, 1):
            try:
                print(f"\n🔄 Processing {i}/{len(pdf_files)}: {Path(pdf_path).name}")
                
                # Extract data
                extracted_data = extractor.extract_data(pdf_path)
                
                if extracted_data and extracted_data.get('tables'):
                    # Convert to CSV
                    csv_data = converter.convert_to_csv(extracted_data)
                    
                    # Generate output filename
                    pdf_name = Path(pdf_path).stem
                    csv_filename = file_handler.get_safe_filename(f"{pdf_name}.csv")
                    csv_path = Path(output_path) / csv_filename
                    
                    # Save CSV
                    if file_handler.save_csv(csv_data, str(csv_path)):
                        success_count += 1
                        print(f"   ✅ Success: {csv_filename}")
                    else:
                        print(f"   ❌ Failed to save: {csv_filename}")
                else:
                    print(f"   ⚠️  No data extracted")
            
            except Exception as e:
                print(f"   ❌ Error processing {Path(pdf_path).name}: {str(e)}")
        
        print(f"\n📊 Batch processing complete:")
        print(f"   Total files: {len(pdf_files)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {len(pdf_files) - success_count}")
        print(f"   Output directory: {output_path}")
    
    except Exception as e:
        print(f"❌ Batch processing error: {str(e)}")

def preview_extraction_example():
    """Example 4: Preview extraction before saving"""
    print("="*60)
    print("Example 4: Preview Extraction Before Saving")
    print("="*60)
    
    config = ConfigManager()
    extractor = PDFExtractor(config)
    converter = CSVConverter(config)
    
    pdf_path = "sample_preview.pdf"
    
    try:
        print(f"📄 Previewing extraction from: {pdf_path}")
        
        # Extract data for preview
        extracted_data = extractor.extract_data(pdf_path, preview_only=True)
        
        if extracted_data and extracted_data.get('tables'):
            print(f"✅ Preview successful!")
            print(f"   Tables found: {len(extracted_data['tables'])}")
            print(f"   Total rows: {extracted_data.get('total_rows', 0)}")
            print(f"   Method used: {extracted_data.get('method', 'auto')}")
            
            # Generate CSV preview
            preview_info = converter.preview_csv(extracted_data, preview_rows=5)
            
            print(f"\n📋 CSV Preview (first 5 rows):")
            print("-" * 50)
            print(preview_info.get('preview', 'No preview available'))
            print("-" * 50)
            print(f"Total columns: {preview_info.get('column_count', 0)}")
            print(f"Column names: {preview_info.get('columns', [])}")
            
            # Ask user if they want to save
            response = input("\n💾 Save full CSV? (y/n): ").lower().strip()
            if response == 'y':
                csv_data = converter.convert_to_csv(extracted_data)
                output_path = "previewed_output.csv"
                if FileHandler().save_csv(csv_data, output_path):
                    print(f"✅ Full CSV saved: {output_path}")
                else:
                    print("❌ Failed to save CSV")
            else:
                print("📝 Preview only - no file saved")
        
        else:
            print("❌ No data found for preview")
    
    except FileNotFoundError:
        print(f"❌ PDF file not found: {pdf_path}")
        print("This is expected if you don't have the sample file.")
    except Exception as e:
        print(f"❌ Preview error: {str(e)}")

def configuration_examples():
    """Example 5: Working with different configurations"""
    print("="*60)
    print("Example 5: Configuration Examples")
    print("="*60)
    
    # Example 1: Default configuration
    print("🔧 Default Configuration:")
    default_config = ConfigManager()
    print(f"   Extraction method: {default_config.get('extraction_method')}")
    print(f"   Output delimiter: {default_config.get('output_format.delimiter')}")
    print(f"   Clean data: {default_config.get('processing.clean_data')}")
    
    # Example 2: Custom configuration
    print("\n🔧 Custom Configuration:")
    custom_settings = {
        'extraction_method': 'camelot',
        'output_format': {
            'delimiter': '|',
            'encoding': 'utf-8',
            'header_row': False
        },
        'processing': {
            'clean_data': False,
            'skip_empty_rows': False
        }
    }
    
    custom_config = ConfigManager()
    custom_config.update_settings(custom_settings)
    
    print(f"   Extraction method: {custom_config.get('extraction_method')}")
    print(f"   Output delimiter: {custom_config.get('output_format.delimiter')}")
    print(f"   Clean data: {custom_config.get('processing.clean_data')}")
    
    # Save custom configuration
    custom_config.save_config("examples/custom_config.json")
    print("   ✅ Custom configuration saved to examples/custom_config.json")
    
    # Validate configuration
    validation = custom_config.validate_config()
    print(f"   Configuration valid: {validation['valid']}")
    if validation['errors']:
        print(f"   Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"   Warnings: {validation['warnings']}")

def file_info_example():
    """Example 6: Getting file information"""
    print("="*60)
    print("Example 6: File Information and Validation")
    print("="*60)
    
    file_handler = FileHandler()
    extractor = PDFExtractor()
    
    # Example files to check
    example_files = [
        "sample_data.pdf",
        "test_document.pdf",
        "nonexistent.pdf"
    ]
    
    for pdf_path in example_files:
        print(f"\n📄 Checking file: {pdf_path}")
        
        # Get file info
        file_info = file_handler.get_file_info(pdf_path)
        
        if file_info:
            print(f"   ✅ File exists")
            print(f"   Size: {file_info.get('size_human', 'Unknown')}")
            print(f"   Extension: {file_info.get('extension', 'Unknown')}")
            print(f"   MIME type: {file_info.get('mime_type', 'Unknown')}")
            print(f"   Readable: {file_info.get('is_readable', False)}")
            
            # Validate as PDF
            is_valid = file_handler.validate_pdf(pdf_path)
            print(f"   Valid PDF: {is_valid}")
            
            if is_valid:
                # Get PDF-specific info
                pdf_info = extractor.get_pdf_info(pdf_path)
                if pdf_info:
                    print(f"   Pages: {pdf_info.get('total_pages', 'Unknown')}")
                    print(f"   Metadata: {bool(pdf_info.get('metadata'))}")
        else:
            print(f"   ❌ File not found or inaccessible")

def main():
    """Run all examples"""
    print("🚀 PDF to CSV Processor - Basic Usage Examples")
    print("=" * 60)
    
    logger = setup_logger(__name__)
    logger.info("Starting basic usage examples")
    
    try:
        # Run examples
        basic_pdf_to_csv_conversion()
        advanced_extraction_with_options()
        batch_processing_example()
        preview_extraction_example()
        configuration_examples()
        file_info_example()
        
        print("\n🎉 All examples completed!")
        print("\nNote: Some examples may show errors if sample PDF files are not present.")
        print("This is expected behavior for demonstration purposes.")
        
    except KeyboardInterrupt:
        print("\n🛑 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Examples failed: {str(e)}")
        logger.error(f"Examples failed: {str(e)}")

if __name__ == "__main__":
    main()