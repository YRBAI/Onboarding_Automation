# ft_scraper.py - Financial Times data scraping

import re
from typing import Dict
from bs4 import BeautifulSoup
from config import FT_BASE_URL


class FTScraper:
    """Handles Financial Times website scraping for fund data."""
    
    def __init__(self, session):
        self.session = session
    
    def parse_geographic_allocation(self, html_content: str) -> str:
        """Parse geographic allocation from FT HTML content. Return blank if not found."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            region_section = soup.find('div', {'class': 'mod-diversification__column', 'data-mod-section': 'Region'})
            if not region_section:
                return ""
            
            table = region_section.find('table', class_='mod-ui-table')
            if not table:
                return ""
            
            regions = []
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    region_span = cells[0].find('span', class_='mod-ui-table__cell--colored__wrapper')
                    if region_span:
                        region_name = region_span.get_text(strip=True)
                        percentage_text = cells[1].get_text(strip=True)
                        m = re.search(r'(\d+\.?\d*)%', percentage_text)
                        if m:
                            regions.append((region_name, float(m.group(1))))
            
            if not regions:
                return ""
            
            # If any region has >80%, return that region; otherwise return "Global"
            for region_name, pct in regions:
                if pct > 80:
                    return region_name
            return "Global"
            
        except Exception as e:
            print(f"Error parsing geographic allocation: {e}")
            return ""

    def parse_investment_objective(self, html_content: str) -> str:
        """Parse investment objective from FT HTML content. Return blank if not found."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            objective_header = soup.find('h2', string='Objective')
            if not objective_header:
                return ""
            
            content_div = objective_header.find_next('div', class_='mod-module__content')
            if not content_div:
                return ""
            
            # Remove the "More" link and expandable content elements
            for more_link in content_div.find_all('div', class_='mod-ui-show-more'):
                more_link.decompose()
            
            for more_link in content_div.find_all('span', class_='mod-ui-show-more__link'):
                more_link.decompose()
            
            paragraphs = content_div.find_all('p')
            text_parts = []
            for p in paragraphs:
                # Get all text including hidden content but exclude "More" links
                text = p.get_text(strip=True)
                if text:
                    # Remove "More ▼" or similar patterns
                    text = re.sub(r'\s*More\s*[▼▽⏷⏵]+\s*$', '', text)
                    text = re.sub(r'\s*More\s*$', '', text)
                    if text:  # Only add if there's still content after cleaning
                        text_parts.append(text)
            
            full_text = ' '.join(text_parts)
            
            # Final cleanup to remove any remaining "More" artifacts
            full_text = re.sub(r'\s*More\s*[▼▽⏷⏵]+\s*', ' ', full_text)
            full_text = re.sub(r'\s+', ' ', full_text).strip()
            
            return full_text
            
        except Exception as e:
            print(f"Error parsing investment objective: {e}")
            return ""
    def parse_launch_date(self, html_content: str) -> str:
        """Parse launch date from FT HTML content. Return blank if not found."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for launch date in profile table
            tables = soup.find_all('table', class_='mod-ui-table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        th_text = th.get_text(strip=True).lower()
                        if 'launch date' in th_text:
                            return td.get_text(strip=True)
            
            return ""
        except Exception as e:
            print(f"Error parsing launch date: {e}")
            return ""

    def parse_ongoing_charge(self, html_content: str) -> str:
        """Parse ongoing charge from FT HTML content. Return blank if not found."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for ongoing charge in investment table
            tables = soup.find_all('table', class_='mod-ui-table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        th_text = th.get_text(strip=True).lower()
                        if 'ongoing charge' in th_text:
                            td_text = td.get_text(strip=True)
                            # Extract percentage
                            percentage_match = re.search(r'(\d+\.?\d*%)', td_text)
                            if percentage_match:
                                return percentage_match.group(1)
                            return td_text
            
            return ""
        except Exception as e:
            print(f"Error parsing ongoing charge: {e}")
            return ""

    def parse_morningstar_category(self, html_content: str) -> str:
        """Parse Morningstar category from FT HTML content. Return blank if not found."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for Morningstar category in profile table
            tables = soup.find_all('table', class_='mod-ui-table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        th_text = th.get_text(strip=True).lower()
                        if 'morningstar category' in th_text:
                            return td.get_text(strip=True)
            
            return ""
        except Exception as e:
            print(f"Error parsing Morningstar category: {e}")
            return ""

    def fetch_ft_data(self, isin: str, verify_ssl: bool = False) -> Dict[str, str]:
        """
        Fetch additional data from Financial Times.
        Returns a dictionary with all FT data, or blanks on failure.
        """
        try:
            url = FT_BASE_URL.format(isin=isin)
            response = self.session.get(url, timeout=30, verify=verify_ssl)
            response.raise_for_status()
            
            html_content = response.text
            
            # Parse all fields
            geographic = self.parse_geographic_allocation(html_content)
            investment_objective = self.parse_investment_objective(html_content)
            launch_date = self.parse_launch_date(html_content)
            ongoing_charge = self.parse_ongoing_charge(html_content)
            morningstar_category = self.parse_morningstar_category(html_content)
            
            return {
                'geographic': geographic,
                'investment_objective': investment_objective,
                'launch_date': launch_date,
                'ongoing_charge': ongoing_charge,
                'morningstar_category': morningstar_category
            }
            
        except Exception as e:
            print(f"Error fetching FT data for {isin}: {e}")
            return {
                'geographic': "",
                'investment_objective': "",
                'launch_date': "",
                'ongoing_charge': "",
                'morningstar_category': ""
            }