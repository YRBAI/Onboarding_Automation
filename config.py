# config.py - Enhanced configuration for executable distribution
import urllib3
import os
import sys

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Get base directory for executable
if getattr(sys, 'frozen', False):
    # Running as executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Results directory
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Ensure results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)

# API URLs
MORNINGSTAR_BASE_URL = "https://api.morningstar.com/v2/service/mf/FundShareClassBasicInfo/isin/{isin}?accesscode={accesscode}"
FT_BASE_URL = "https://markets.ft.com/data/funds/tearsheet/summary?s={isin}"
PHS_BASE_URL = "http://doc.morningstar.com/services.aspx?type=customalldocnew&investmenttype=1&clientid=phillipssec&key=52c4533bcc966857&ISIN={isin}&documenttype=77"
FACTSHEET_BASE_URL = "http://doc.morningstar.com/services.aspx?type=customalldocnew&investmenttype=1&clientid=phillipssec&key=52c4533bcc966857&ISIN={isin}&documenttype=52"
# Asset type mapping
ASSET_MAPPING = {
    'allocation': 'Balanced Fund',
    'equity': 'Equity Fund',
    'fixed income': 'Fixed Income Fund',
    'commodity': 'Commodity Fund',
    'cash equivalent': 'Cash Equivalent Fund',
    'alternative': 'Alternative Fund'
}

# Risk classification mapping
RISK_CLASSIFICATION = {
    'cash equivalent fund': 'Low',
    'fixed income fund': 'Low to Medium',
    'balanced fund': 'Medium to High',
    'equity fund': 'High',
    'commodity fund': 'High',
    'alternative fund': 'High'
}

# Session headers for web scraping
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Excel column configuration
EXCEL_COLUMNS = [
    'No.', 'Fund House', 'Fund Name', 'ISIN', 'Retail/AI', 'Asset', 
    'Geographic', 'Sector', 'Launch Date', 'Annual Management Fee', 
    'Factsheet', 'Highlights (PHS Link)', 'Investment Objective', 'Key Risks for Investors', 'Other Risks', 'PSPL Risk Classification'
]

# Excel column widths
EXCEL_COLUMN_WIDTHS = {
    'A': 5,   # No.
    'B': 12,  # Fund House
    'C': 34,  # Fund Name
    'D': 17,  # ISIN
    'E': 12,  # Retail/AI
    'F': 20,  # Asset
    'G': 15,  # Geographic
    'H': 25,  # Sector
    'I': 15,  # Launch Date
    'J': 15,  # Annual Management Fee
    'K': 60,  # Factsheet (NEW)
    'L': 60,  # Highlights (PHS Link) (shifted from K)
    'M': 60,  # Investment Objective (shifted from L)
    'N': 60,  # Key Risks for Investors (shifted from M)
    'O': 60,  # Other Risks (shifted from N)
    'P': 20,  # PSPL Risk Classification (shifted from O)
}

# Text processing constants for intelligent risk extraction
FILLER_WORDS = {
    'the', 'and', 'to', 'of', 'are', 'in', 'for', 'with', 'by', 'from', 
    'an', 'a', 'or', 'but', 'as', 'at', 'be', 'been', 'have', 'has', 
    'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 
    'may', 'might', 'must', 'can', 'is', 'was', 'were', 'this', 'that',
    'these', 'those', 'on', 'up', 'down', 'over', 'under', 'through'
}

RISK_PHRASE_WINDOW = 3  # Number of words before and after "risk"

# Document processing settings - Updated for executable
DEFAULT_DOC_CONFIG = {
    "folder": RESULTS_DIR,
    "old_text": "Sep 12_Mass",
    "doc_filename": "",
    "access_code": ""
}

DOC_FONT_NAME = "Arial"
DOC_FONT_SIZE = 10

# Config file path
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")