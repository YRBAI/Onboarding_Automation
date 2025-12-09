# morningstar_api.py - Morningstar API integration and PHS document handling

import requests
import xml.etree.ElementTree as ET
import urllib.parse
from typing import Optional, Dict
from datetime import datetime
from config import MORNINGSTAR_BASE_URL, PHS_BASE_URL, FACTSHEET_BASE_URL, ASSET_MAPPING, RISK_CLASSIFICATION


class MorningstarAPI:
    """Handles Morningstar API calls and PHS document retrieval."""
    
    def __init__(self, access_code: str, session: requests.Session):
        self.access_code = access_code
        self.session = session
    
    def normalize_asset_type(self, raw_asset_type: Optional[str]) -> str:
        """Convert raw asset type to standardized format. Return blank if unknown."""
        if not raw_asset_type:
            return ""
        raw_lower = raw_asset_type.lower()
        for key, value in ASSET_MAPPING.items():
            if key in raw_lower:
                return value
        return ""  # Return blank instead of formatted string if no match

    def get_risk_classification(self, asset_type: str) -> str:
        """Get PSPL risk classification based on asset type. Return blank if unknown."""
        if not asset_type:
            return ""
        return RISK_CLASSIFICATION.get(asset_type.lower(), "")  # Return blank instead of "Medium" default

    def get_retail_ai_classification(self, isin: str) -> str:
        """Classify fund based on ISIN prefix."""
        if not isin:
            return ""
        isin_upper = isin.upper()
        if isin_upper.startswith('LU') or isin_upper.startswith('IE'):
            return "Recognised"
        elif isin_upper.startswith('SG'):
            return "Authorised"
        else:
            return ""  # Will be highlighted in yellow

    def extract_xml_field(self, root: ET.Element, field_name: str) -> Optional[str]:
        """Extract a field from XML, handling namespaces."""
        for elem in root.iter():
            tag = elem.tag
            if tag == field_name or tag.endswith(f'}}{field_name}'):
                return elem.text
        return None
    def get_factsheet_url(self, isin: str) -> str:
        """Generate factsheet URL for the given ISIN."""
        if not isin:
            return ""
        return FACTSHEET_BASE_URL.format(isin=isin)

    def fetch_fund_basic_info(self, isin: str, verify_ssl: bool = False) -> Dict[str, str]:
        """
        Fetch basic fund information from Morningstar API.
        Returns a dictionary with fund details or blanks on failure.
        """
        try:
            url = MORNINGSTAR_BASE_URL.format(isin=isin, accesscode=self.access_code)
            response = self.session.get(url, timeout=30, verify=verify_ssl)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            # Extract fields
            fund_house = self.extract_xml_field(root, 'AdvisoryCompanyName') or ""
            fund_name = self.extract_xml_field(root, 'FundLegalName') or ""
            raw_asset_type = self.extract_xml_field(root, 'MorningstarCategoryGroupName')

            # Process asset & risk
            asset_type = self.normalize_asset_type(raw_asset_type)
            risk_classification = self.get_risk_classification(asset_type)
            retail_ai = self.get_retail_ai_classification(isin)
            factsheet_url = self.get_factsheet_url(isin)  # NEW

            return {
                'fund_house': fund_house,
                'fund_name': fund_name,
                'asset_type': asset_type,
                'risk_classification': risk_classification,
                'retail_ai': retail_ai,
                'factsheet': factsheet_url,  # NEW
                'pspl_risk_classification': risk_classification
            }

        except Exception as e:
            print(f"Error fetching Morningstar data for {isin}: {e}")
            return {
                'fund_house': "",
                'fund_name': "",
                'asset_type': "",
                'risk_classification': "",
                'retail_ai': self.get_retail_ai_classification(isin),
                'factsheet': self.get_factsheet_url(isin),  # NEW - still generate URL even on error
                'pspl_risk_classification': ""
            }

    def fetch_phs_link(self, isin: str, verify_ssl: bool = False) -> str:
        """
        Fetch the latest PHS document link for the given ISIN.
        Returns the ViewUrl of the latest English PHS document, or blank if not found.
        """
        try:
            url = PHS_BASE_URL.format(isin=urllib.parse.quote(isin))
            response = self.session.get(url, timeout=30, verify=verify_ssl)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Find all Document elements
            documents = []
            for doc in root.findall('.//Document'):
                # Check if it's a PHS document (DocumentTypeId="77")
                doc_type_elem = doc.find('.//DocumentType[@DocumentTypeId="77"]')
                if doc_type_elem is None:
                    continue
                
                # Check if language is English
                language_elem = doc.find('.//Language')
                if language_elem is None or language_elem.text != 'English':
                    continue
                
                # Get DocumentDate and ViewUrl
                doc_date_elem = doc.find('.//DocumentDate')
                view_url_elem = doc.find('.//ViewUrl')
                
                if doc_date_elem is not None and view_url_elem is not None:
                    try:
                        doc_date = datetime.strptime(doc_date_elem.text, '%Y-%m-%d')
                        view_url = view_url_elem.text
                        
                        # Check for market preference (Singapore preferred)
                        market_elem = doc.find('.//Market')
                        market = market_elem.text if market_elem is not None else ""
                        is_singapore = market.lower() == 'singapore'
                        
                        documents.append({
                            'date': doc_date,
                            'url': view_url,
                            'is_singapore': is_singapore
                        })
                    except ValueError:
                        continue
            
            if not documents:
                return ""
            
            # Sort by date (newest first), then prefer Singapore market
            documents.sort(key=lambda x: (x['date'], x['is_singapore']), reverse=True)
            
            # Return the ViewUrl of the latest document
            return documents[0]['url']
            
        except Exception as e:
            print(f"Error fetching PHS link for {isin}: {e}")
            return ""