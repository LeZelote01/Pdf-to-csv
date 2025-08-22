#!/usr/bin/env python3
"""
PDF to CSV Data Processor
========================

Main command-line interface for extracting data from PDF files and converting to CSV format.

Author: PDF Data Processor Team
Version: 1.0.0
License: MIT
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from src.core.pdf_extractor import PDFExtractor
from src.core.csv_converter import CSVConverter
from src.core.config_manager import ConfigManager
from src.utils.file_handler import FileHandler
from src.utils.logger import setup_logger

# Initialize console for rich output
console = Console()

class PDFProcessor:
    """Main PDF processing class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize PDF processor with optional config file"""
        self.config = ConfigManager(config_path)
        self.extractor = PDFExtractor(self.config)
        self.converter = CSVConverter(self.config)
        self.file_handler = FileHandler()
        self.logger = setup_logger(__name__)
    
    def process_single_pdf(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Process a single PDF file and convert to CSV
        
        Args:
            input_path: Path to input PDF file
            output_path: Path to output CSV file
            **kwargs: Additional processing options
            
        Returns:
            bool: Success status
        """
        try:
            console.print(f"📄 Processing PDF: {input_path}")
            
            # Validate input file
            if not self.file_handler.validate_pdf(input_path):
                console.print(f"❌ Invalid PDF file: {input_path}", style="red")
                return False
            
            # Extract data from PDF
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("Extracting PDF data...", total=100)
                
                # Step 1: Extract raw data
                progress.update(task, advance=25, description="Reading PDF structure...")
                extracted_data = self.extractor.extract_data(input_path, **kwargs)
                
                progress.update(task, advance=25, description="Processing tables...")
                if not extracted_data:
                    console.print("❌ No data extracted from PDF", style="red")
                    return False
                
                # Step 2: Convert to CSV format
                progress.update(task, advance=25, description="Converting to CSV...")
                csv_data = self.converter.convert_to_csv(extracted_data, **kwargs)
                
                # Step 3: Save to file
                progress.update(task, advance=25, description="Saving CSV file...")
                success = self.file_handler.save_csv(csv_data, output_path)
                
                progress.update(task, completed=100, description="✅ Processing complete!")
            
            if success:
                # Display results
                self._display_results(input_path, output_path, extracted_data)
                return True
            else:
                console.print("❌ Failed to save CSV file", style="red")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing PDF {input_path}: {str(e)}")
            console.print(f"❌ Error: {str(e)}", style="red")
            return False
    
    def process_batch(self, input_dir: str, output_dir: str, **kwargs) -> dict:
        """
        Process multiple PDF files in a directory
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save CSV files
            **kwargs: Additional processing options
            
        Returns:
            dict: Processing results summary
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all PDF files
        pdf_files = list(input_path.glob("*.pdf"))
        
        if not pdf_files:
            console.print(f"❌ No PDF files found in {input_dir}", style="red")
            return {"success": 0, "failed": 0, "total": 0}
        
        console.print(f"📁 Found {len(pdf_files)} PDF files to process")
        
        results = {"success": 0, "failed": 0, "total": len(pdf_files)}
        failed_files = []
        
        # Process each PDF file
        with Progress(console=console) as progress:
            batch_task = progress.add_task("Processing PDFs...", total=len(pdf_files))
            
            for pdf_file in pdf_files:
                progress.update(batch_task, description=f"Processing {pdf_file.name}")
                
                # Generate output filename
                csv_filename = pdf_file.stem + ".csv"
                csv_path = output_path / csv_filename
                
                # Process the file
                success = self.process_single_pdf(str(pdf_file), str(csv_path), **kwargs)
                
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    failed_files.append(pdf_file.name)
                
                progress.update(batch_task, advance=1)
        
        # Display batch results
        self._display_batch_results(results, failed_files)
        return results
    
    def _display_results(self, input_path: str, output_path: str, extracted_data: dict):
        """Display processing results in a formatted table"""
        
        table = Table(title="Processing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Add results to table
        table.add_row("Input PDF", Path(input_path).name)
        table.add_row("Output CSV", Path(output_path).name)
        table.add_row("Tables Extracted", str(len(extracted_data.get('tables', []))))
        table.add_row("Total Rows", str(extracted_data.get('total_rows', 0)))
        table.add_row("Total Columns", str(extracted_data.get('total_columns', 0)))
        table.add_row("Processing Method", extracted_data.get('method', 'auto'))
        
        console.print(table)
        console.print(f"\n✅ CSV file saved: {output_path}")
    
    def _display_batch_results(self, results: dict, failed_files: List[str]):
        """Display batch processing results"""
        
        panel_content = f"""
        Total Files: {results['total']}
        ✅ Success: {results['success']}
        ❌ Failed: {results['failed']}
        Success Rate: {(results['success']/results['total']*100):.1f}%
        """
        
        console.print(Panel(panel_content, title="Batch Processing Results", border_style="green"))
        
        if failed_files:
            console.print("\n❌ Failed Files:", style="red")
            for file in failed_files:
                console.print(f"  - {file}", style="red")


@click.command()
@click.option('--input', '-i', help='Input PDF file path')
@click.option('--output', '-o', help='Output CSV file path')
@click.option('--input-dir', help='Directory containing PDF files (batch mode)')
@click.option('--output-dir', help='Output directory for CSV files (batch mode)')
@click.option('--config', '-c', help='Configuration file path')
@click.option('--method', default='auto', help='Extraction method (auto/tabula/camelot/pdfplumber)')
@click.option('--pages', help='Page range to process (e.g., 1-3 or 1,3,5)')
@click.option('--template', help='Custom extraction template file')
@click.option('--pattern', default='table', help='Data pattern to extract (table/form/text)')
@click.option('--encoding', default='utf-8', help='Output file encoding')
@click.option('--delimiter', default=',', help='CSV delimiter')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--preview', is_flag=True, help='Preview extraction without saving')
def main(input, output, input_dir, output_dir, config, method, pages, template, 
         pattern, encoding, delimiter, verbose, preview):
    """
    PDF to CSV Data Processor
    
    Extract data from PDF files and convert to CSV format.
    Supports batch processing and various PDF data formats.
    """
    
    # Setup logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Display welcome message
    console.print(Panel(
        "🔄 PDF to CSV Data Processor v1.0.0\n"
        "Extract and convert PDF data to CSV format",
        title="Welcome",
        border_style="blue"
    ))
    
    # Initialize processor
    try:
        processor = PDFProcessor(config)
    except Exception as e:
        console.print(f"❌ Failed to initialize processor: {str(e)}", style="red")
        sys.exit(1)
    
    # Prepare processing options
    processing_options = {
        'method': method,
        'pages': pages,
        'template': template,
        'pattern': pattern,
        'encoding': encoding,
        'delimiter': delimiter,
        'preview_only': preview
    }
    
    # Process files
    try:
        if input_dir and output_dir:
            # Batch processing mode
            console.print("🔄 Starting batch processing...")
            results = processor.process_batch(input_dir, output_dir, **processing_options)
            
            if results['success'] == 0:
                sys.exit(1)
                
        elif input and output:
            # Single file processing mode
            console.print("🔄 Starting single file processing...")
            success = processor.process_single_pdf(input, output, **processing_options)
            
            if not success:
                sys.exit(1)
                
        else:
            console.print("❌ Please specify either --input/--output or --input-dir/--output-dir", style="red")
            console.print("Use --help for usage information")
            sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n🛑 Processing interrupted by user", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Unexpected error: {str(e)}", style="red")
        sys.exit(1)
    
    console.print("\n🎉 Processing completed successfully!", style="green bold")


if __name__ == "__main__":
    main()