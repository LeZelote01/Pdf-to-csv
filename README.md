# PDF to CSV Data Processor

A Python script for extracting data from PDF files and converting it to CSV format. This tool handles various PDF data formats including tables, forms, and structured text data.

## Features

- **PDF Data Extraction**: Extract tables, text data, and structured information from PDF files
- **Multiple Output Formats**: Convert to CSV with customizable formatting options
- **Table Detection**: Automatically detect and extract tabular data from PDFs
- **Form Data Processing**: Handle PDF forms and extract field data
- **Text Pattern Recognition**: Extract data using custom patterns and templates
- **Batch Processing**: Process multiple PDF files at once
- **Error Handling**: Robust error handling for various PDF formats

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd pdf-to-csv-processor
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Extract data from a single PDF file
python pdf_processor.py --input data.pdf --output data.csv

# Process multiple PDFs in a directory
python pdf_processor.py --input-dir ./pdfs/ --output-dir ./csvs/

# Use custom extraction template
python pdf_processor.py --input data.pdf --output data.csv --template custom_template.json
```

### Advanced Usage

```bash
# Extract specific pages only
python pdf_processor.py --input data.pdf --output data.csv --pages 1-5

# Use custom column mapping
python pdf_processor.py --input data.pdf --output data.csv --mapping column_mapping.json

# Extract with specific data patterns
python pdf_processor.py --input data.pdf --output data.csv --pattern "table" --format "structured"
```

### Interactive Mode

```bash
# Launch interactive GUI
python gui_processor.py
```

## Configuration

Create a `config.json` file to customize the extraction process:

```json
{
  "extraction_method": "auto",
  "table_detection": true,
  "text_patterns": ["table", "form", "structured"],
  "output_format": {
    "delimiter": ",",
    "encoding": "utf-8",
    "header_row": true
  },
  "processing": {
    "clean_data": true,
    "merge_cells": true,
    "skip_empty_rows": true
  }
}
```

## Supported PDF Formats

- **Tabular Data**: PDF files containing tables with rows and columns
- **Form Data**: Interactive PDF forms with fillable fields
- **Structured Text**: Organized text data with consistent formatting
- **Mixed Content**: PDFs containing combination of tables and text
- **Scanned PDFs**: OCR processing for image-based PDFs (with tesseract)

## Examples

See the `examples/` directory for sample PDF files and their corresponding CSV outputs.

## Requirements

- Python 3.7+
- See `requirements.txt` for full list of dependencies

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For questions and support, please create an issue in the GitHub repository.