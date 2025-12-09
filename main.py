# main.py - Main application with intelligent risk classification

import pandas as pd
import sys
import subprocess
from typing import List

from fund_fetcher import FundDataFetcher
from excel_exporter import ExcelExporter


def check_and_install_requirements():
    """Check for required packages and install if missing."""
    required_packages = {
        'beautifulsoup4': 'bs4',
        'openpyxl': 'openpyxl',
        'requests': 'requests',
        'pandas': 'pandas'
    }
    
    missing_packages = []
    
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Installing required packages...")
        for package in missing_packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Check for optional PDF extraction libraries
    pdf_libs = {
        'PyMuPDF': 'fitz',
        'pdfplumber': 'pdfplumber', 
        'PyPDF2': 'PyPDF2'
    }
    
    available_pdf_libs = []
    missing_pdf_libs = []
    
    for lib_name, import_name in pdf_libs.items():
        try:
            __import__(import_name)
            available_pdf_libs.append(lib_name)
        except ImportError:
            missing_pdf_libs.append(lib_name)
    
    if available_pdf_libs:
        print(f"✅ PDF extraction libraries available: {', '.join(available_pdf_libs)}")
    
    if missing_pdf_libs:
        print(f"📚 Optional PDF libraries not installed: {', '.join(missing_pdf_libs)}")
        print("   For optimal PDF risk extraction, consider installing:")
        for lib in missing_pdf_libs:
            if lib == 'PyMuPDF':
                print("   pip install PyMuPDF      # Recommended - fastest and most accurate")
            elif lib == 'pdfplumber':
                print("   pip install pdfplumber   # Good alternative")
            elif lib == 'PyPDF2':
                print("   pip install PyPDF2       # Basic fallback")


def get_isin_input() -> List[str]:
    """Get ISIN codes from user input."""
    print("\nEnter ISIN codes (one per line, press Enter twice when done):")
    isin_list = []
    while True:
        line = input().strip()
        if not line:
            break
        isin_list.append(line)
    return isin_list


def main():
    """Main application function with simplified risk classification."""
    print("=" * 70)
    print("🚀 Enhanced Fund Data Fetcher with Intelligent Risk Classification")
    print("=" * 70)
    print("🎯 FEATURES:")
    print("   • Automatic risk detection using master dictionary (40+ risk types)")
    print("   • Two-column output: Standard risks + Manual review needed")
    print("   • Simple Excel format with yellow highlighting for blanks")
    print("\n⚙️  TECHNICAL:")
    print("   • SSL verification disabled for certificate compatibility")
    print("   • Multi-method PDF extraction (PyMuPDF + pdfplumber + PyPDF2)")
    print("   • Data sources: Morningstar API + Financial Times + PHS Documents")
    print()
    
    # Check and install requirements
    try:
        check_and_install_requirements()
    except Exception as e:
        print(f"❌ Error installing requirements: {e}")
        print("Please install required packages manually and try again.")
        return
    
    # Get access code
    access_code = input("Enter your Morningstar access code: ").strip()
    if not access_code:
        print("❌ Access code is required!")
        return
    
    # Get ISIN codes
    isin_list = get_isin_input()
    if not isin_list:
        print("❌ No ISIN codes provided!")
        return
    
    print(f"\n🔄 Processing {len(isin_list)} ISINs with intelligent risk classification...")
    print("=" * 60)
    
    # Initialize fetcher and process funds
    fetcher = FundDataFetcher(access_code, verify_ssl=False)
    df = fetcher.fetch_multiple_funds(isin_list)
    
    # Generate summary and export
    if not df.empty:
        ExcelExporter.generate_summary(df)
        
        # Export to Excel
        date_str = pd.Timestamp.now().strftime('%b %d')  # Format: "Aug 28"
        filename = f"{date_str}_Mass Onboarding Retail Funds.xlsx"
        ExcelExporter.export_to_excel(df, filename)
        
    else:
        print("❌ No data was successfully retrieved.")


def process_from_file(access_code: str, input_file: str, output_file: str = None):
    """
    Process ISINs from a text file with simplified risk classification.
    
    Args:
        access_code: Morningstar API access code
        input_file: Path to text file containing ISINs (one per line)
        output_file: Optional output filename (defaults to timestamped name)
    """
    try:
        print(f"📂 Reading ISINs from {input_file}...")
        with open(input_file, 'r') as f:
            isin_list = [line.strip() for line in f if line.strip()]
        
        print(f"📋 Found {len(isin_list)} ISINs to process with intelligent risk analysis.\n")
        
        fetcher = FundDataFetcher(access_code, verify_ssl=False)
        df = fetcher.fetch_multiple_funds(isin_list)
        
        if output_file is None:
            date_str = pd.Timestamp.now().strftime('%b %d')  # Format: "Aug 28"
            output_file = f"{date_str}_Mass Onboarding Retail Funds.xlsx"
        
        if not df.empty:
            ExcelExporter.generate_summary(df)
            ExcelExporter.export_to_excel(df, output_file)
        else:
            print("❌ No data was successfully retrieved.")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ Error: File {input_file} not found!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Check for command line arguments for batch processing
    if len(sys.argv) > 1:
        if sys.argv[1] == 'batch' and len(sys.argv) >= 4:
            # Usage: python main.py batch <access_code> <input_file> [output_file]
            access_code = sys.argv[2]
            input_file = sys.argv[3]
            output_file = sys.argv[4] if len(sys.argv) > 4 else None
            process_from_file(access_code, input_file, output_file)
        else:
            print("Usage:")
            print("  Interactive mode: python main.py")
            print("  Batch mode: python main.py batch <access_code> <input_file> [output_file]")
    else:
        main()