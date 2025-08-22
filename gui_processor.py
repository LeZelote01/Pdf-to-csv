#!/usr/bin/env python3
"""
PDF to CSV GUI Processor
========================

Graphical user interface for the PDF to CSV data processor.
Provides an easy-to-use interface for non-technical users.

Author: PDF Data Processor Team
Version: 1.0.0
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
from typing import Optional

from src.core.pdf_extractor import PDFExtractor
from src.core.csv_converter import CSVConverter
from src.core.config_manager import ConfigManager
from src.utils.file_handler import FileHandler
from src.utils.logger import setup_logger


class PDFProcessorGUI:
    """GUI Application for PDF to CSV processing"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to CSV Data Processor v1.0.0")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Initialize components
        self.config = ConfigManager()
        self.extractor = PDFExtractor(self.config)
        self.converter = CSVConverter(self.config)
        self.file_handler = FileHandler()
        self.logger = setup_logger(__name__)
        
        # Variables
        self.input_file_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.processing_method_var = tk.StringVar(value="auto")
        self.data_pattern_var = tk.StringVar(value="table")
        self.pages_var = tk.StringVar()
        self.delimiter_var = tk.StringVar(value=",")
        self.encoding_var = tk.StringVar(value="utf-8")
        
        # Processing state
        self.processing = False
        
        # Setup GUI
        self.create_widgets()
        self.center_window()
    
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Single file processing tab
        self.single_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.single_frame, text="Single File")
        self.create_single_file_tab()
        
        # Batch processing tab
        self.batch_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_frame, text="Batch Processing")
        self.create_batch_processing_tab()
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        self.create_settings_tab()
        
        # Log tab
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Processing Log")
        self.create_log_tab()
    
    def create_single_file_tab(self):
        """Create single file processing interface"""
        
        # Main container
        main_frame = ttk.Frame(self.single_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input file selection
        input_frame = ttk.LabelFrame(main_frame, text="Input PDF File", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(input_frame, textvariable=self.input_file_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="Browse...", command=self.browse_input_file).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Output file selection
        output_frame = ttk.LabelFrame(main_frame, text="Output CSV File", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(output_frame, textvariable=self.output_file_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output_file).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Processing options
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Method selection
        ttk.Label(options_frame, text="Extraction Method:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        method_combo = ttk.Combobox(options_frame, textvariable=self.processing_method_var, 
                                   values=["auto", "tabula", "camelot", "pdfplumber"], state="readonly")
        method_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Data pattern
        ttk.Label(options_frame, text="Data Pattern:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        pattern_combo = ttk.Combobox(options_frame, textvariable=self.data_pattern_var,
                                   values=["table", "form", "text", "mixed"], state="readonly")
        pattern_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Pages selection
        ttk.Label(options_frame, text="Pages (optional):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        ttk.Entry(options_frame, textvariable=self.pages_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        # Help label for pages
        ttk.Label(options_frame, text="(e.g., 1-3 or 1,3,5)", font=("", 8)).grid(row=2, column=1, sticky=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.process_button = ttk.Button(button_frame, text="🔄 Process PDF", command=self.process_single_file)
        self.process_button.pack(side=tk.LEFT)
        
        ttk.Button(button_frame, text="📋 Preview", command=self.preview_file).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="🗑️ Clear", command=self.clear_single_form).pack(side=tk.LEFT, padx=(10, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack(pady=(5, 0))
    
    def create_batch_processing_tab(self):
        """Create batch processing interface"""
        
        main_frame = ttk.Frame(self.batch_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input directory
        input_frame = ttk.LabelFrame(main_frame, text="Input Directory (PDF Files)", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(input_frame, textvariable=self.input_dir_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="Browse...", command=self.browse_input_dir).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Output directory
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory (CSV Files)", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output_dir).pack(side=tk.RIGHT, padx=(10, 0))
        
        # File list
        list_frame = ttk.LabelFrame(main_frame, text="Files to Process", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for file list
        self.file_tree = ttk.Treeview(list_frame, columns=("size", "status"), show="tree headings")
        self.file_tree.heading("#0", text="Filename")
        self.file_tree.heading("size", text="Size")
        self.file_tree.heading("status", text="Status")
        self.file_tree.column("#0", width=300)
        self.file_tree.column("size", width=100)
        self.file_tree.column("status", width=100)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Batch action buttons
        batch_button_frame = ttk.Frame(main_frame)
        batch_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(batch_button_frame, text="🔍 Scan Directory", command=self.scan_directory).pack(side=tk.LEFT)
        self.batch_process_button = ttk.Button(batch_button_frame, text="🔄 Process All", command=self.process_batch)
        self.batch_process_button.pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(batch_button_frame, text="🗑️ Clear List", command=self.clear_file_list).pack(side=tk.LEFT, padx=(10, 0))
        
        # Batch progress
        self.batch_progress_var = tk.DoubleVar()
        self.batch_progress_bar = ttk.Progressbar(main_frame, variable=self.batch_progress_var, mode='determinate')
        self.batch_progress_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.batch_status_var = tk.StringVar(value="Ready for batch processing")
        self.batch_status_label = ttk.Label(main_frame, textvariable=self.batch_status_var)
        self.batch_status_label.pack(pady=(5, 0))
    
    def create_settings_tab(self):
        """Create settings configuration interface"""
        
        main_frame = ttk.Frame(self.settings_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Output settings
        output_settings = ttk.LabelFrame(main_frame, text="Output Settings", padding=10)
        output_settings.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_settings, text="CSV Delimiter:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        delimiter_combo = ttk.Combobox(output_settings, textvariable=self.delimiter_var,
                                     values=[",", ";", "\t", "|"], width=10)
        delimiter_combo.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(output_settings, text="File Encoding:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        encoding_combo = ttk.Combobox(output_settings, textvariable=self.encoding_var,
                                    values=["utf-8", "latin-1", "cp1252"], width=15)
        encoding_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Processing settings
        process_settings = ttk.LabelFrame(main_frame, text="Processing Settings", padding=10)
        process_settings.pack(fill=tk.X, pady=(0, 10))
        
        # Checkboxes for various options
        self.clean_data_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(process_settings, text="Clean extracted data", variable=self.clean_data_var).pack(anchor=tk.W)
        
        self.merge_cells_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(process_settings, text="Merge split cells", variable=self.merge_cells_var).pack(anchor=tk.W)
        
        self.skip_empty_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(process_settings, text="Skip empty rows", variable=self.skip_empty_var).pack(anchor=tk.W)
        
        self.header_row_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(process_settings, text="Include header row", variable=self.header_row_var).pack(anchor=tk.W)
        
        # Advanced settings
        advanced_settings = ttk.LabelFrame(main_frame, text="Advanced Settings", padding=10)
        advanced_settings.pack(fill=tk.X, pady=(0, 10))
        
        self.ocr_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_settings, text="Enable OCR for scanned PDFs", variable=self.ocr_enabled_var).pack(anchor=tk.W)
        
        self.verbose_logging_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_settings, text="Enable verbose logging", variable=self.verbose_logging_var).pack(anchor=tk.W)
        
        # Settings buttons
        settings_buttons = ttk.Frame(main_frame)
        settings_buttons.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(settings_buttons, text="💾 Save Settings", command=self.save_settings).pack(side=tk.LEFT)
        ttk.Button(settings_buttons, text="🔄 Reset to Defaults", command=self.reset_settings).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(settings_buttons, text="📁 Load Config", command=self.load_config).pack(side=tk.LEFT, padx=(10, 0))
    
    def create_log_tab(self):
        """Create processing log interface"""
        
        main_frame = ttk.Frame(self.log_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Log controls
        log_controls = ttk.Frame(main_frame)
        log_controls.pack(fill=tk.X)
        
        ttk.Button(log_controls, text="🗑️ Clear Log", command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="💾 Save Log", command=self.save_log).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(log_controls, text="🔄 Refresh", command=self.refresh_log).pack(side=tk.LEFT, padx=(10, 0))
    
    # File selection methods
    def browse_input_file(self):
        """Browse for input PDF file"""
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if filename:
            self.input_file_var.set(filename)
            # Auto-suggest output filename
            if not self.output_file_var.get():
                output_path = Path(filename).with_suffix('.csv')
                self.output_file_var.set(str(output_path))
    
    def browse_output_file(self):
        """Browse for output CSV file"""
        filename = filedialog.asksaveasfilename(
            title="Save CSV As",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if filename:
            self.output_file_var.set(filename)
    
    def browse_input_dir(self):
        """Browse for input directory"""
        dirname = filedialog.askdirectory(title="Select Directory with PDF Files")
        if dirname:
            self.input_dir_var.set(dirname)
    
    def browse_output_dir(self):
        """Browse for output directory"""
        dirname = filedialog.askdirectory(title="Select Output Directory for CSV Files")
        if dirname:
            self.output_dir_var.set(dirname)
    
    # Processing methods
    def process_single_file(self):
        """Process single PDF file"""
        if self.processing:
            return
        
        input_file = self.input_file_var.get()
        output_file = self.output_file_var.get()
        
        if not input_file or not output_file:
            messagebox.showerror("Error", "Please select both input and output files")
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("Error", "Input file does not exist")
            return
        
        # Start processing in separate thread
        self.processing = True
        self.process_button.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._process_single_thread, args=(input_file, output_file))
        thread.start()
    
    def _process_single_thread(self, input_file, output_file):
        """Process single file in separate thread"""
        try:
            self.status_var.set("Processing PDF...")
            self.progress_var.set(0)
            
            # Get processing options
            options = self._get_processing_options()
            
            # Extract data
            self.progress_var.set(25)
            self.status_var.set("Extracting data...")
            extracted_data = self.extractor.extract_data(input_file, **options)
            
            if not extracted_data:
                self.log_message("❌ No data extracted from PDF")
                messagebox.showerror("Error", "No data could be extracted from the PDF")
                return
            
            # Convert to CSV
            self.progress_var.set(50)
            self.status_var.set("Converting to CSV...")
            csv_data = self.converter.convert_to_csv(extracted_data, **options)
            
            # Save file
            self.progress_var.set(75)
            self.status_var.set("Saving CSV file...")
            success = self.file_handler.save_csv(csv_data, output_file)
            
            self.progress_var.set(100)
            
            if success:
                self.status_var.set("✅ Processing completed successfully!")
                self.log_message(f"✅ Successfully processed: {Path(input_file).name}")
                self.log_message(f"📁 Output saved to: {output_file}")
                messagebox.showinfo("Success", f"PDF processed successfully!\n\nOutput: {output_file}")
            else:
                self.status_var.set("❌ Failed to save CSV file")
                self.log_message("❌ Failed to save CSV file")
                messagebox.showerror("Error", "Failed to save CSV file")
        
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")
            messagebox.showerror("Error", f"Processing failed:\n\n{str(e)}")
        
        finally:
            self.processing = False
            self.process_button.config(state=tk.NORMAL)
    
    def preview_file(self):
        """Preview PDF extraction without saving"""
        input_file = self.input_file_var.get()
        
        if not input_file:
            messagebox.showerror("Error", "Please select an input PDF file")
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("Error", "Input file does not exist")
            return
        
        # Show preview in new window
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"Preview: {Path(input_file).name}")
        preview_window.geometry("600x400")
        
        preview_text = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD)
        preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            options = self._get_processing_options()
            options['preview_only'] = True
            
            extracted_data = self.extractor.extract_data(input_file, **options)
            
            if extracted_data:
                preview_text.insert(tk.END, f"PDF File: {Path(input_file).name}\n")
                preview_text.insert(tk.END, f"Pages: {extracted_data.get('pages', 'All')}\n")
                preview_text.insert(tk.END, f"Tables Found: {len(extracted_data.get('tables', []))}\n")
                preview_text.insert(tk.END, f"Total Rows: {extracted_data.get('total_rows', 0)}\n")
                preview_text.insert(tk.END, f"Total Columns: {extracted_data.get('total_columns', 0)}\n")
                preview_text.insert(tk.END, "="*50 + "\n\n")
                
                for i, table in enumerate(extracted_data.get('tables', [])):
                    preview_text.insert(tk.END, f"Table {i+1}:\n")
                    preview_text.insert(tk.END, str(table)[:1000] + "...\n\n")
            else:
                preview_text.insert(tk.END, "No data could be extracted from this PDF.")
        
        except Exception as e:
            preview_text.insert(tk.END, f"Error during preview: {str(e)}")
    
    def scan_directory(self):
        """Scan input directory for PDF files"""
        input_dir = self.input_dir_var.get()
        
        if not input_dir:
            messagebox.showerror("Error", "Please select an input directory")
            return
        
        if not os.path.exists(input_dir):
            messagebox.showerror("Error", "Input directory does not exist")
            return
        
        # Clear existing items
        self.clear_file_list()
        
        # Find PDF files
        pdf_files = list(Path(input_dir).glob("*.pdf"))
        
        for pdf_file in pdf_files:
            # Get file size
            size = pdf_file.stat().st_size
            size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
            
            # Add to tree
            self.file_tree.insert("", tk.END, text=pdf_file.name, values=(size_str, "Ready"))
        
        self.batch_status_var.set(f"Found {len(pdf_files)} PDF files")
        self.log_message(f"📁 Scanned directory: {input_dir}")
        self.log_message(f"📄 Found {len(pdf_files)} PDF files")
    
    def process_batch(self):
        """Process all files in batch mode"""
        if self.processing:
            return
        
        input_dir = self.input_dir_var.get()
        output_dir = self.output_dir_var.get()
        
        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Please select both input and output directories")
            return
        
        # Get list of files from tree
        files_to_process = []
        for item in self.file_tree.get_children():
            filename = self.file_tree.item(item, "text")
            files_to_process.append((item, filename))
        
        if not files_to_process:
            messagebox.showerror("Error", "No files to process. Please scan the directory first.")
            return
        
        # Start batch processing
        self.processing = True
        self.batch_process_button.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._process_batch_thread, args=(input_dir, output_dir, files_to_process))
        thread.start()
    
    def _process_batch_thread(self, input_dir, output_dir, files_to_process):
        """Process batch files in separate thread"""
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        total_files = len(files_to_process)
        processed = 0
        success_count = 0
        
        options = self._get_processing_options()
        
        for item_id, filename in files_to_process:
            try:
                self.batch_status_var.set(f"Processing {filename}...")
                self.file_tree.set(item_id, "status", "Processing...")
                
                # Update progress
                progress = (processed / total_files) * 100
                self.batch_progress_var.set(progress)
                
                # Process file
                input_path = Path(input_dir) / filename
                output_path = Path(output_dir) / (Path(filename).stem + ".csv")
                
                extracted_data = self.extractor.extract_data(str(input_path), **options)
                
                if extracted_data:
                    csv_data = self.converter.convert_to_csv(extracted_data, **options)
                    success = self.file_handler.save_csv(csv_data, str(output_path))
                    
                    if success:
                        self.file_tree.set(item_id, "status", "✅ Success")
                        success_count += 1
                        self.log_message(f"✅ Processed: {filename}")
                    else:
                        self.file_tree.set(item_id, "status", "❌ Save Failed")
                        self.log_message(f"❌ Failed to save: {filename}")
                else:
                    self.file_tree.set(item_id, "status", "❌ No Data")
                    self.log_message(f"❌ No data extracted: {filename}")
            
            except Exception as e:
                self.file_tree.set(item_id, "status", "❌ Error")
                self.log_message(f"❌ Error processing {filename}: {str(e)}")
            
            processed += 1
        
        # Batch complete
        self.batch_progress_var.set(100)
        self.batch_status_var.set(f"Batch complete: {success_count}/{total_files} files processed successfully")
        
        messagebox.showinfo("Batch Complete", 
                           f"Batch processing completed!\n\n"
                           f"Total files: {total_files}\n"
                           f"Successful: {success_count}\n"
                           f"Failed: {total_files - success_count}")
        
        self.processing = False
        self.batch_process_button.config(state=tk.NORMAL)
    
    # Utility methods
    def _get_processing_options(self):
        """Get current processing options from GUI"""
        return {
            'method': self.processing_method_var.get(),
            'pattern': self.data_pattern_var.get(),
            'pages': self.pages_var.get() if self.pages_var.get() else None,
            'delimiter': self.delimiter_var.get(),
            'encoding': self.encoding_var.get(),
            'clean_data': self.clean_data_var.get(),
            'merge_cells': self.merge_cells_var.get(),
            'skip_empty': self.skip_empty_var.get(),
            'header_row': self.header_row_var.get(),
            'ocr_enabled': self.ocr_enabled_var.get(),
            'verbose': self.verbose_logging_var.get()
        }
    
    def clear_single_form(self):
        """Clear single file form"""
        self.input_file_var.set("")
        self.output_file_var.set("")
        self.pages_var.set("")
        self.progress_var.set(0)
        self.status_var.set("Ready")
    
    def clear_file_list(self):
        """Clear batch file list"""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.batch_progress_var.set(0)
        self.batch_status_var.set("Ready for batch processing")
    
    def log_message(self, message):
        """Add message to processing log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear processing log"""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """Save processing log to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Processing Log",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Log saved to {filename}")
    
    def refresh_log(self):
        """Refresh log display"""
        # Implementation would depend on logging backend
        pass
    
    def save_settings(self):
        """Save current settings to config file"""
        try:
            settings = {
                'output': {
                    'delimiter': self.delimiter_var.get(),
                    'encoding': self.encoding_var.get(),
                    'header_row': self.header_row_var.get()
                },
                'processing': {
                    'clean_data': self.clean_data_var.get(),
                    'merge_cells': self.merge_cells_var.get(),
                    'skip_empty': self.skip_empty_var.get(),
                    'ocr_enabled': self.ocr_enabled_var.get(),
                    'verbose_logging': self.verbose_logging_var.get()
                }
            }
            
            self.config.save_settings(settings)
            messagebox.showinfo("Success", "Settings saved successfully")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        self.delimiter_var.set(",")
        self.encoding_var.set("utf-8")
        self.clean_data_var.set(True)
        self.merge_cells_var.set(True)
        self.skip_empty_var.set(True)
        self.header_row_var.set(True)
        self.ocr_enabled_var.set(False)
        self.verbose_logging_var.set(False)
        
        messagebox.showinfo("Success", "Settings reset to defaults")
    
    def load_config(self):
        """Load settings from config file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON Files", "*.json"), ("YAML Files", "*.yaml"), ("All Files", "*.*")]
        )
        if filename:
            try:
                self.config.load_config(filename)
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """Launch the GUI application"""
    root = tk.Tk()
    
    # Set application icon (if available)
    try:
        root.iconbitmap("assets/icon.ico")
    except:
        pass
    
    # Create and run application
    app = PDFProcessorGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.processing:
            if messagebox.askokcancel("Quit", "Processing is in progress. Do you want to quit anyway?"):
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()