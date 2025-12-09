# fund_fetcher.py - Fixed version with correct factsheet handling

import requests
import pandas as pd
import time
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import DEFAULT_HEADERS, EXCEL_COLUMNS
from morningstar_api import MorningstarAPI
from ft_scraper import FTScraper
from pdf_extractor import PDFRiskExtractor


class FundDataFetcher:
    """Main class that orchestrates fund data fetching from all sources."""
    
    def __init__(self, access_code: str, verify_ssl: bool = False):
        self.access_code = access_code
        self.verify_ssl = verify_ssl
        
        # Setup session with headers and SSL configuration
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.verify = verify_ssl
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Initialize component classes
        self.morningstar_api = MorningstarAPI(access_code, self.session)
        self.ft_scraper = FTScraper(self.session)
        self.pdf_extractor = PDFRiskExtractor(self.session)
    
    def fetch_fund_data(self, isin: str) -> Optional[Dict]:
        """
        Fetch comprehensive fund data for a single ISIN from all sources.
        Returns a dict with all fund information; unknown/missing fields are blank strings.
        """
        try:
            print(f"  → Fetching Morningstar data...")
            # Fetch basic fund info from Morningstar
            morningstar_data = self.morningstar_api.fetch_fund_basic_info(isin, self.verify_ssl)
            
            print(f"  → Fetching FT data...")
            # FT data
            ft_data = self.ft_scraper.fetch_ft_data(isin, self.verify_ssl)
            geographic = ft_data.get('geographic', '')
            investment_objective = ft_data.get('investment_objective', '')
            launch_date = ft_data.get('launch_date', '')
            annual_management_fee = ft_data.get('ongoing_charge', '')
            morningstar_category = ft_data.get('morningstar_category', '')
            asset_type = morningstar_data.get('asset_type', '')
            
            if asset_type and morningstar_category:
                sector = f"{asset_type} - {morningstar_category}"
            else:
                sector = ""
            
            print(f"  → Fetching PHS link...")
            # Fetch PHS document link
            phs_link = self.morningstar_api.fetch_phs_link(isin, self.verify_ssl)
            
            print(f"  → Extracting key risks...")
            # Extract key risks from PHS document (now returns two strings)
            if phs_link:
                standard_risks, other_risks = self.pdf_extractor.extract_key_risks_from_pdf(phs_link, self.verify_ssl)
            else:
                standard_risks, other_risks = "", ""
            
            # Combine all data - FIXED: Use morningstar_data, not fund_data
            fund_data = {
                'isin': isin,
                'fund_house': morningstar_data.get('fund_house', ''),
                'fund_name': morningstar_data.get('fund_name', ''),
                'asset_type': asset_type,
                'retail_ai': morningstar_data.get('retail_ai', ''),
                'geographic': geographic,
                'sector': sector,
                'launch_date': launch_date,
                'annual_management_fee': annual_management_fee,
                'factsheet': morningstar_data.get('factsheet', ''),  # FIXED
                'investment_objective': investment_objective,
                'standard_risks': standard_risks, 
                'other_risks': other_risks,        
                'phs_link': phs_link,
                'pspl_risk_classification': morningstar_data.get('risk_classification', '')
            }
            
            return fund_data

        except Exception as e:
            # Return a row with blanks so highlighting flags it
            print(f"Error fetching data for {isin}: {e}")
            return {
                'isin': isin,
                'fund_house': "",
                'fund_name': "",
                'asset_type': "",
                'retail_ai': self.morningstar_api.get_retail_ai_classification(isin),
                'geographic': "",
                'sector': "",
                'launch_date': "",
                'annual_management_fee': "",
                'factsheet': self.morningstar_api.get_factsheet_url(isin),  # FIXED
                'investment_objective': "",
                'standard_risks': "",  # Empty for error cases
                'other_risks': "",     # Empty for error cases
                'phs_link': "",
                'pspl_risk_classification': ""
            }
            

    def fetch_multiple_funds(self, isin_list: List[str], delay: float = 2.0) -> pd.DataFrame:
        """
        Fetch fund data for multiple ISINs.
        
        Args:
            isin_list: List of ISIN codes to process
            delay: Delay between requests to avoid rate limiting
            
        Returns:
            DataFrame with all fund data
        """
        results = []
        total = len(isin_list)
        
        for i, isin in enumerate(isin_list, 1):
            print(f"\nProcessing {i}/{total}: {isin}")
            fund_data = self.fetch_fund_data(isin.strip())
            if fund_data:
                fund_data['no'] = i
                results.append(fund_data)
            
            # Add delay between requests (except for the last one)
            if i < len(isin_list):
                print(f"  → Waiting {delay}s before next request...")
                time.sleep(delay)
        
        # Convert to DataFrame and format columns
        df = pd.DataFrame(results)
        if not df.empty:
            # Reorder columns to match EXCEL_COLUMNS - FIXED order
            df = df[[
                'no', 'fund_house', 'fund_name', 'isin', 'retail_ai', 'asset_type',
                'geographic', 'sector', 'launch_date', 'annual_management_fee', 
                'factsheet', 'phs_link', 'investment_objective', 'standard_risks', 'other_risks', 'pspl_risk_classification'
            ]]
            # Rename columns for display
            df.columns = EXCEL_COLUMNS
        
        return df