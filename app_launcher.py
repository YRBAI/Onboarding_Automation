# app_launcher.py - Main GUI application launcher

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
from datetime import datetime
import json
from pathlib import Path

# Import your existing modules
from fund_fetcher import FundDataFetcher
from excel_exporter import ExcelExporter
from doc_processor import DocProcessor


class FundDataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fund Data Processor v2.0")
        self.root.geometry("800x600")
        
        # Create results directory
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Load/create config
        self.config_file = "config.json"
        self.config = self.load_config()
        
        self.setup_ui()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Default config
        return {
            "access_code": "",
            "old_text": "Sep 12_Mass",
            "folder": str(self.results_dir),
            "doc_filename": ""
        }
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Excel Processing Tab
        excel_frame = ttk.Frame(notebook)
        notebook.add(excel_frame, text="Excel Processing")
        self.setup_excel_tab(excel_frame)
        
        # Document Processing Tab
        doc_frame = ttk.Frame(notebook)
        notebook.add(doc_frame, text="Document Processing")
        self.setup_doc_tab(doc_frame)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_excel_tab(self, parent):
        """Setup Excel processing tab."""
        # Access Code
        ttk.Label(parent, text="Morningstar Access Code:").pack(pady=5)
        self.access_code_var = tk.StringVar(value=self.config.get("access_code", ""))
        access_entry = ttk.Entry(parent, textvariable=self.access_code_var, width=50, show="*")
        access_entry.pack(pady=5)
        
        # ISIN Input
        ttk.Label(parent, text="ISIN Codes (one per line):").pack(pady=(20, 5))
        self.isin_text = tk.Text(parent, height=10, width=60)
        self.isin_text.pack(pady=5)
        
        # Buttons frame
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Load ISINs from File", 
                  command=self.load_isins_from_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Process Excel", 
                  command=self.process_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear", 
                  command=lambda: self.isin_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.excel_progress = ttk.Progressbar(parent, mode='indeterminate')
        self.excel_progress.pack(pady=10, fill=tk.X, padx=20)
        
        # Output text
        ttk.Label(parent, text="Output:").pack(pady=(20, 5))
        self.excel_output = tk.Text(parent, height=8, width=60)
        self.excel_output.pack(pady=5, fill=tk.BOTH, expand=True)
    
    def setup_doc_tab(self, parent):
        """Setup document processing tab."""
        # Current config display
        config_frame = ttk.LabelFrame(parent, text="Current Configuration")
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.old_text_var = tk.StringVar(value=self.config.get("old_text", ""))
        ttk.Label(config_frame, text="Old Text:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(config_frame, textvariable=self.old_text_var, 
                 background="white", relief=tk.SUNKEN).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # New text input
        ttk.Label(config_frame, text="New Date (e.g., Sep 13):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.new_date_var = tk.StringVar()
        date_entry = ttk.Entry(config_frame, textvariable=self.new_date_var, width=20)
        date_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Auto-fill today's date button
        ttk.Button(config_frame, text="Use Today's Date", 
                  command=self.use_todays_date).grid(row=1, column=2, padx=5, pady=5)
        
        config_frame.columnconfigure(1, weight=1)
        
        # Document selection
        doc_frame = ttk.LabelFrame(parent, text="Document Processing")
        doc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.doc_file_var = tk.StringVar()
        ttk.Label(doc_frame, text="Template Document:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(doc_frame, textvariable=self.doc_file_var, width=50).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(doc_frame, text="Browse", 
                  command=self.browse_doc_file).grid(row=0, column=2, padx=5, pady=5)
        
        doc_frame.columnconfigure(1, weight=1)
        
        # Auto-detect documents button
        ttk.Button(doc_frame, text="Auto-detect Documents in Results Folder", 
                  command=self.auto_detect_docs).grid(row=1, column=0, columnspan=3, pady=10)
        
        # Process button
        ttk.Button(parent, text="Process Document", 
                  command=self.process_document).pack(pady=20)
        
        # Progress bar
        self.doc_progress = ttk.Progressbar(parent, mode='indeterminate')
        self.doc_progress.pack(pady=10, fill=tk.X, padx=20)
        
        # Output text
        ttk.Label(parent, text="Output:").pack(pady=(20, 5))
        self.doc_output = tk.Text(parent, height=8, width=60)
        self.doc_output.pack(pady=5, fill=tk.BOTH, expand=True)
    
    def use_todays_date(self):
        """Fill in today's date in the correct format."""
        today = datetime.now()
        date_str = today.strftime("%b %d")  # e.g., "Sep 13"
        self.new_date_var.set(date_str)
    
    def browse_doc_file(self):
        """Browse for document file."""
        file_path = filedialog.askopenfilename(
            title="Select Template Document",
            initialdir=self.results_dir,
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        if file_path:
            self.doc_file_var.set(file_path)
    
    def auto_detect_docs(self):
        """Auto-detect Word documents in results folder."""
        try:
            docx_files = list(self.results_dir.glob("*.docx"))
            if docx_files:
                # Filter out temporary files
                docx_files = [f for f in docx_files if not f.name.startswith('~')]
                
                if len(docx_files) == 1:
                    self.doc_file_var.set(str(docx_files[0]))
                    self.update_doc_output(f"Auto-detected: {docx_files[0].name}")
                else:
                    # Show selection dialog
                    self.show_doc_selection_dialog(docx_files)
            else:
                messagebox.showinfo("No Documents", 
                                  f"No Word documents found in {self.results_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Error auto-detecting documents: {e}")
    
    def show_doc_selection_dialog(self, doc_files):
        """Show dialog to select from multiple documents."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Document")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Multiple documents found. Select one:").pack(pady=10)
        
        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for doc in doc_files:
            listbox.insert(tk.END, doc.name)
        
        def select_doc():
            selection = listbox.curselection()
            if selection:
                selected_doc = doc_files[selection[0]]
                self.doc_file_var.set(str(selected_doc))
                self.update_doc_output(f"Selected: {selected_doc.name}")
                dialog.destroy()
        
        ttk.Button(dialog, text="Select", command=select_doc).pack(pady=10)
    
    def load_isins_from_file(self):
        """Load ISINs from a text file."""
        file_path = filedialog.askopenfilename(
            title="Select ISIN File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                self.isin_text.delete(1.0, tk.END)
                self.isin_text.insert(1.0, content)
                self.update_excel_output(f"Loaded ISINs from {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file: {e}")
    
    def update_excel_output(self, message):
        """Update Excel output text."""
        self.excel_output.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.excel_output.see(tk.END)
        self.root.update()
    
    def update_doc_output(self, message):
        """Update document output text."""
        self.doc_output.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.doc_output.see(tk.END)
        self.root.update()
    
    def process_excel(self):
        """Process Excel in a separate thread."""
        def run_excel_processing():
            try:
                self.excel_progress.start()
                self.status_var.set("Processing Excel...")
                
                # Get inputs
                access_code = self.access_code_var.get().strip()
                if not access_code:
                    messagebox.showerror("Error", "Please enter access code")
                    return
                
                # Save access code to config
                self.config["access_code"] = access_code
                self.save_config()
                
                isin_text = self.isin_text.get(1.0, tk.END).strip()
                if not isin_text:
                    messagebox.showerror("Error", "Please enter ISIN codes")
                    return
                
                isin_list = [line.strip() for line in isin_text.split('\n') if line.strip()]
                
                self.update_excel_output(f"Starting processing of {len(isin_list)} ISINs...")
                
                # Initialize fetcher and process
                fetcher = FundDataFetcher(access_code, verify_ssl=False)
                df = fetcher.fetch_multiple_funds(isin_list)
                
                if not df.empty:
                    # Generate output filename
                    date_str = datetime.now().strftime('%b %d')
                    filename = f"{date_str}_Mass Onboarding Retail Funds.xlsx"
                    output_path = self.results_dir / filename
                    
                    # Export to Excel
                    ExcelExporter.export_to_excel(df, str(output_path))
                    
                    self.update_excel_output(f"Success! File saved: {filename}")
                    self.update_excel_output(f"Total funds processed: {len(df)}")
                    
                    # Show summary
                    self.update_excel_output("=== SUMMARY ===")
                    ExcelExporter.generate_summary(df)
                else:
                    self.update_excel_output("No data was successfully retrieved.")
                
            except Exception as e:
                self.update_excel_output(f"Error: {e}")
                messagebox.showerror("Error", f"Processing failed: {e}")
            finally:
                self.excel_progress.stop()
                self.status_var.set("Ready")
        
        # Run in thread to prevent UI freezing
        thread = threading.Thread(target=run_excel_processing)
        thread.daemon = True
        thread.start()
    
    def process_document(self):
        """Process document in a separate thread."""
        def run_doc_processing():
            try:
                self.doc_progress.start()
                self.status_var.set("Processing Document...")
                
                # Get inputs
                new_date = self.new_date_var.get().strip()
                if not new_date:
                    messagebox.showerror("Error", "Please enter new date")
                    return
                
                doc_file = self.doc_file_var.get().strip()
                if not doc_file or not os.path.exists(doc_file):
                    messagebox.showerror("Error", "Please select a valid document file")
                    return
                
                # Format new text
                new_text = f"{new_date}_Mass"
                old_text = self.config.get("old_text", "Sep 12_Mass")
                
                self.update_doc_output(f"Processing document: {os.path.basename(doc_file)}")
                self.update_doc_output(f"Replacing '{old_text}' with '{new_text}'")
                
                # Create output filename
                output_filename = f"{new_text} Onboarding New Product Evaluation Appendix C.docx"
                output_path = self.results_dir / output_filename
                
                # Initialize processor and process
                processor = DocProcessor()
                success = processor.replace_text_in_document(
                    doc_file, str(output_path), old_text, new_text
                )
                
                if success:
                    # Update config with new text as old text for next time
                    self.config["old_text"] = new_text
                    self.old_text_var.set(new_text)
                    self.save_config()
                    
                    self.update_doc_output(f"Success! Document saved: {output_filename}")
                    self.update_doc_output(f"Config updated: old_text = '{new_text}'")
                else:
                    self.update_doc_output("Document processing failed.")
                
            except Exception as e:
                self.update_doc_output(f"Error: {e}")
                messagebox.showerror("Error", f"Processing failed: {e}")
            finally:
                self.doc_progress.stop()
                self.status_var.set("Ready")
        
        # Run in thread to prevent UI freezing
        thread = threading.Thread(target=run_doc_processing)
        thread.daemon = True
        thread.start()


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = FundDataApp(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()