# pdf_extractor.py - Enhanced PDF text extraction with ML-based classification and deduplication

import re
import io
import numpy as np
from typing import List, Optional, Tuple, Dict, Set
from collections import Counter
from config import FILLER_WORDS, RISK_PHRASE_WINDOW

# Try to import ML libraries with fallbacks
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: ML libraries not available. Install with: pip install sentence-transformers scikit-learn")

# Master Risk Dictionary - Expanded with more variations
MASTER_RISKS = {
    # Market & Asset Class Risks
    "Market Risk": ["market risk", "market risks", "market volatility", "market movements", "market downturns", "market stress"],
    "Equity Risk": ["equity risk", "equity risks", "stock risk", "share price risk", "share risk"],
    "Interest Rate Risk": ["interest rate risk", "interest rate risks", "rate risk", "ir risk", "duration risk", "yield curve risk"],
    "Credit Risk": ["credit risk", "credit risks", "default risk", "issuer risk", "credit default", "issuer default", "credit quality"],
    "Sovereign Risk": ["sovereign risk", "sovereign risks", "government risk", "country risk", "government default"],
    "Currency Risk": ["currency risk", "currency risks", "fx risk", "foreign exchange risk", "exchange rate risk", "currency exposure"],
    "Commodity Risk": ["commodity risk", "commodity risks", "commodity price risk"],
    
    # Liquidity & Funding Risks
    "Liquidity Risk": ["liquidity risk", "liquidity risks", "illiquidity risk", "illiquidity", "lack of liquidity", "limited liquidity"],
    "Redemption Risk": ["redemption risk", "redemption risks", "early redemption", "redemption delay"],
    "Funding Liquidity Risk": ["funding liquidity risk", "funding risk", "liquidity funding risk"],
    
    # Concentration & Correlation Risks
    "Concentration Risk": ["concentration risk", "concentration risks", "single issuer risk", "geographic concentration", "lack of diversification", "concentrated exposure"],
    "Correlation Risk": ["correlation risk", "correlation risks", "correlation breakdown"],
    "Sector Concentration Risk": ["sector risk", "sector concentration", "industry risk"],
    
    # Investment Strategy Risks
    "Style Risk": ["style risk", "growth risk", "value risk", "investment style risk"],
    "Volatility Risk": ["volatility risk", "volatility risks", "price volatility", "higher volatility"],
    "Derivatives Risk": ["derivatives risk", "derivative risk", "derivatives risks"],
    "Hedging Risk": ["hedging risk", "hedging risks", "hedge risk"],
    "Leverage Risk": ["leverage risk", "leveraging risk", "gearing risk"],
    "Short Selling Risk": ["short selling risk", "shorting risk", "short position risk"],
    
    # Counterparty & Operational Risks
    "Counterparty Risk": ["counterparty risk", "counterparty risks", "counterparty default"],
    "Operational Risk": ["operational risk", "operational risks", "operational failure"],
    "Management Risk": ["management risk", "manager risk", "fund manager risk"],
    "Model Risk": ["model risk", "model risks", "quantitative model risk"],
    
    # Economic & Macro Risks
    "Inflation Risk": ["inflation risk", "inflation risks", "inflationary risk"],
    "Deflation Risk": ["deflation risk", "deflation risks", "deflationary risk"],
    "Recession Risk": ["recession risk", "economic downturn risk", "economic risk"],
    
    # Regulatory & Legal Risks
    "Political Risk": ["political risk", "political risks", "geopolitical risk"],
    "Regulatory Risk": ["regulatory risk", "regulatory risks", "legal risk", "compliance risk"],
    "Expropriation Risk": ["expropriation risk", "nationalization risk", "confiscation risk"],
    
    # Specialized Product Risks
    "High Yield Risk": ["high yield risk", "junk bond risk", "sub investment grade risk", "below investment grade"],
    "Perpetual Bond Risk": ["perpetual bond risk", "perpetual bonds risk", "perpetual securities risk", "hybrid securities risk"],
    "Complex Product Risk": ["complex product risk", "structured product risk", "complexity risk"],
    "Synthetic Risk": ["synthetic risk", "replication risk", "tracking risk"],
    "Default Risk": ["default risk", "issuer default", "bond default", "payment default", "unable to make payments"],
    "ELN Risk": ["eln risk", "equity linked note risk", "equity-linked note risk", "structured note risk"],
    "Prepayment Risk": ["prepayment risk", "prepayment and extension risk", "early repayment risk", "call risk", "extension risk"],
    
    # ESG & Sustainability
    "ESG Risk": ["esg risk", "sustainability risk", "environmental risk", "social risk", "governance risk"],
    "Climate Risk": ["climate risk", "climate change risk", "environmental risk"],
    
    # Emerging Markets
    "Emerging Market Risk": ["emerging market risk", "emerging markets risk", "developing market risk"],
    "Capital Controls Risk": ["capital controls risk", "capital restriction risk"],
    
    # Other Common Risks
    "Reputation Risk": ["reputation risk", "reputational risk"],
    "Technology Risk": ["technology risk", "cyber risk", "it risk"],
    "Reinvestment Risk": ["reinvestment risk", "prepayment risk"]
}

# Create reverse lookup for faster matching
RISK_KEYWORDS_TO_STANDARD = {}
for standard_name, keywords in MASTER_RISKS.items():
    for keyword in keywords:
        RISK_KEYWORDS_TO_STANDARD[keyword.lower()] = standard_name


class MLRiskClassifier:
    """Machine Learning-based risk classifier using sentence embeddings."""
    
    def __init__(self):
        self.model = None
        self.risk_embeddings = None
        self.initialized = False
        
        if ML_AVAILABLE:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self._precompute_risk_embeddings()
                self.initialized = True
                print("ML risk classifier initialized successfully")
            except Exception as e:
                print(f"Failed to initialize ML classifier: {e}")
                self.initialized = False
        else:
            print("ML libraries not available - using rule-based classification only")
    
    def _precompute_risk_embeddings(self):
        """Precompute embeddings for all risk categories."""
        self.risk_embeddings = {}
        
        # Create descriptive definitions for better semantic matching
        risk_definitions = {
            "Market Risk": "market movements volatility financial market conditions",
            "Credit Risk": "issuer default credit quality financial health deterioration",
            "Currency Risk": "exchange rate fluctuations foreign currency exposure",
            "Interest Rate Risk": "interest rate changes bond value duration",
            "Liquidity Risk": "difficulty selling assets marketability trading",
            "Equity Risk": "stock share price volatility company performance",
            "Derivatives Risk": "derivative instruments complex financial products",
            "Leverage Risk": "borrowing amplified exposure financial leverage",
            "Concentration Risk": "single issuer geographic sector concentration",
            "Counterparty Risk": "counterparty default inability to meet obligations",
            "High Yield Risk": "below investment grade junk bonds credit quality",
            "Perpetual Bond Risk": "perpetual securities no maturity date call risk",
            "Emerging Market Risk": "developing markets political instability",
            "Volatility Risk": "price fluctuations market volatility",
            "Default Risk": "issuer inability to pay debt obligations",
            "ELN Risk": "equity linked notes structured products",
            "Prepayment Risk": "early repayment extension callable securities"
        }
        
        for risk_name in MASTER_RISKS.keys():
            definition = risk_definitions.get(risk_name, risk_name.lower())
            self.risk_embeddings[risk_name] = self.model.encode([definition])
    
    def classify_risk(self, phrase: str, threshold: float = 0.65) -> Optional[str]:
        """Classify a risk phrase using semantic similarity."""
        if not self.initialized:
            return None
        
        try:
            phrase_embedding = self.model.encode([phrase])
            
            best_match = None
            best_similarity = 0
            
            for risk_name, risk_embedding in self.risk_embeddings.items():
                similarity = cosine_similarity(phrase_embedding, risk_embedding)[0][0]
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = risk_name
            
            # Only return if similarity exceeds threshold
            if best_similarity >= threshold:
                return best_match
                
        except Exception as e:
            print(f"ML classification error for '{phrase}': {e}")
        
        return None


class AdvancedDeduplicator:
    """Advanced deduplication logic for risk phrases."""
    
    def __init__(self):
        self.noise_patterns = [
            'what risk', 'investment risk', 'factors cause', 'than bonds', 
            'their value', 'generally fall', 'generally greater', 'behaviour',
            'unexpected behaviour', 'factors may cause', 'lose some all'
        ]
    
    def deduplicate_phrases(self, phrases: List[str]) -> List[str]:
        """Remove duplicate phrases before classification."""
        seen_normalized = set()
        unique_phrases = []
        
        for phrase in phrases:
            # Normalize for comparison
            normalized = self._normalize_phrase(phrase)
            
            if normalized not in seen_normalized and len(normalized) > 5:
                seen_normalized.add(normalized)
                unique_phrases.append(phrase)
        
        return unique_phrases
    
    def _normalize_phrase(self, phrase: str) -> str:
        """Normalize phrase for comparison."""
        normalized = phrase.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)  # Collapse spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
        return normalized
    
    def deduplicate_other_risks(self, other_risks: List[str]) -> List[str]:
        """Remove similar unclassified risks and obvious noise."""
        # First, filter out obvious noise
        filtered_risks = [risk for risk in other_risks if not self._is_noise(risk)]
        
        # Then deduplicate similar risks
        unique_risks = []
        
        for risk in filtered_risks:
            if not any(self._are_similar_risks(risk, existing) for existing in unique_risks):
                unique_risks.append(risk)
        
        return unique_risks
    
    def _is_noise(self, phrase: str) -> bool:
        """Check if phrase is likely noise/extraction artifact."""
        phrase_lower = phrase.lower()
        
        # Check for noise patterns
        if any(pattern in phrase_lower for pattern in self.noise_patterns):
            return True
        
        # Check for very short phrases (likely incomplete)
        if len(phrase.split()) < 2:
            return True
        
        # Check for phrases with too many common words
        words = phrase_lower.split()
        common_word_ratio = sum(1 for word in words if word in FILLER_WORDS) / len(words)
        if common_word_ratio > 0.6:
            return True
        
        return False
    
    def _are_similar_risks(self, risk1: str, risk2: str) -> bool:
        """Check if two risk phrases are essentially the same."""
        words1 = set(self._normalize_phrase(risk1).split())
        words2 = set(self._normalize_phrase(risk2).split())
        
        # Remove very common words for comparison
        words1 = {w for w in words1 if w not in FILLER_WORDS and len(w) > 2}
        words2 = {w for w in words2 if w not in FILLER_WORDS and len(w) > 2}
        
        if not words1 or not words2:
            return False
        
        # If 70% of meaningful words overlap, consider them similar
        overlap = len(words1.intersection(words2))
        min_length = min(len(words1), len(words2))
        
        return overlap / min_length > 0.7


class PDFRiskExtractor:
    """Enhanced PDF text extraction and intelligent risk classification."""
    
    def __init__(self, session):
        self.session = session
        self.ml_classifier = MLRiskClassifier()
        self.deduplicator = AdvancedDeduplicator()
    
    def normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, replace newlines with spaces, collapse multiple spaces."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        # Replace newlines with spaces
        text = text.replace('\n', ' ').replace('\r', ' ')
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def clean_and_title_case_phrase(self, phrase: str) -> str:
        """Clean & title-case phrase."""
        if not phrase:
            return ""
        
        # Remove parentheses and their contents
        phrase = re.sub(r'\([^)]*\)', '', phrase)
        
        # Split into words
        words = phrase.split()
        
        # Filter out filler words
        cleaned_words = [word for word in words if word.lower() not in FILLER_WORDS]
        
        # Join and title case
        if cleaned_words:
            cleaned_phrase = ' '.join(cleaned_words).title()
            # Append " Risk" if not already present
            if not cleaned_phrase.lower().endswith('risk'):
                cleaned_phrase += " Risk"
            return cleaned_phrase
        
        return ""

    def enhanced_match_to_master_risks(self, phrase: str) -> Optional[str]:
        """Enhanced matching with fuzzy logic and ML fallback."""
        phrase_lower = phrase.lower().strip()
        
        # Method 1: Direct keyword matching
        for keyword, standard_risk in RISK_KEYWORDS_TO_STANDARD.items():
            if keyword in phrase_lower:
                return standard_risk
        
        # Method 2: Handle plural/singular variations
        normalized_phrase = self._normalize_plurals(phrase_lower)
        for keyword, standard_risk in RISK_KEYWORDS_TO_STANDARD.items():
            normalized_keyword = self._normalize_plurals(keyword)
            if normalized_keyword in normalized_phrase:
                return standard_risk
        
        # Method 3: Word-level matching (order independent)
        phrase_words = set(phrase_lower.split())
        for keyword, standard_risk in RISK_KEYWORDS_TO_STANDARD.items():
            keyword_words = set(keyword.split())
            # If 80% of keyword words are present
            overlap = len(keyword_words.intersection(phrase_words))
            if overlap >= len(keyword_words) * 0.8 and overlap >= 2:
                return standard_risk
        
        # Method 4: ML-based semantic matching (fallback)
        ml_match = self.ml_classifier.classify_risk(phrase)
        if ml_match:
            return ml_match
        
        return None
    
    def _normalize_plurals(self, text: str) -> str:
        """Simple plural/singular normalization."""
        replacements = {
            'bonds': 'bond', 'risks': 'risk', 'markets': 'market',
            'rates': 'rate', 'securities': 'security', 'currencies': 'currency'
        }
        
        for plural, singular in replacements.items():
            text = text.replace(plural, singular)
        return text

    def classify_extracted_risks(self, raw_phrases: List[str]) -> Tuple[List[str], List[str]]:
        """Enhanced classification with deduplication and ML."""
        # Step 1: Deduplicate raw phrases
        unique_phrases = self.deduplicator.deduplicate_phrases(raw_phrases)
        
        # Step 2: Classify risks
        standard_risks = set()
        other_risks = []
        classification_stats = Counter()
        
        for phrase in unique_phrases:
            match = self.enhanced_match_to_master_risks(phrase)
            
            if match:
                standard_risks.add(match)
                classification_stats['standard'] += 1
            else:
                other_risks.append(phrase)
                classification_stats['other'] += 1
        
        # Step 3: Deduplicate and clean other risks
        cleaned_other_risks = self.deduplicator.deduplicate_other_risks(other_risks)
        
        # Step 4: Sort results
        sorted_standard = sorted(list(standard_risks))
        
        return sorted_standard, cleaned_other_risks

    def extract_risk_phrases(self, text: str) -> List[str]:
        """Extract risk phrases - exactly 3 words before and after risk terms."""
        if not text:
            return []
        
        # Step 1: Normalize text
        normalized_text = self.normalize_text(text)
        
        # Step 2: Extract words (excluding punctuation)
        words = re.findall(r"\w+", normalized_text)
        raw_results = []
        
        for i, w in enumerate(words):
            if w.lower().startswith("risk"):  # matches 'risk', 'risks'
                # Get exactly 3 words before and after if available
                start = max(0, i - RISK_PHRASE_WINDOW)
                end = min(len(words), i + RISK_PHRASE_WINDOW + 1)
                phrase = " ".join(words[start:end])
                raw_results.append(phrase)
        
        # Step 3: Clean and title-case each phrase
        cleaned_results = []
        for phrase in raw_results:
            cleaned = self.clean_and_title_case_phrase(phrase)
            if cleaned:  # Only add non-empty results
                cleaned_results.append(cleaned)
        
        return cleaned_results

    def extract_pdf_text_method1_pymupdf(self, pdf_content: bytes) -> Optional[str]:
        """Method 1: PyMuPDF (fitz)"""
        try:
            import fitz
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text += page.get_text() + "\n"
            pdf_document.close()
            return text.strip()
        except ImportError:
            return None
        except Exception:
            return None

    def extract_pdf_text_method2_pdfplumber(self, pdf_content: bytes) -> Optional[str]:
        """Method 2: pdfplumber"""
        try:
            import pdfplumber
            pdf_file = io.BytesIO(pdf_content)
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except ImportError:
            return None
        except Exception:
            return None

    def extract_pdf_text_method3_pypdf2(self, pdf_content: bytes) -> Optional[str]:
        """Method 3: PyPDF2"""
        try:
            import PyPDF2
            pdf_file = io.BytesIO(pdf_content)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except ImportError:
            return None
        except Exception:
            return None

    def extract_key_risks_from_pdf(self, pdf_url: str, verify_ssl: bool = False) -> tuple[str, str]:
        """Enhanced risk extraction with ML and deduplication."""
        if not pdf_url:
            return "", ""
        
        try:
            print(f"  → Attempting to extract risks from: {pdf_url}")
            # Download PDF content
            response = self.session.get(pdf_url, timeout=30, verify=verify_ssl)
            response.raise_for_status()
            pdf_content = response.content
            print(f"  → Downloaded {len(pdf_content)} bytes")
            
            # Try multiple extraction methods
            extraction_methods = [
                ("PyMuPDF", self.extract_pdf_text_method1_pymupdf),
                ("pdfplumber", self.extract_pdf_text_method2_pdfplumber),
                ("PyPDF2", self.extract_pdf_text_method3_pypdf2)
            ]
            
            best_result = None
            best_risk_count = 0
            best_method = ""
            
            for method_name, method_func in extraction_methods:
                text = method_func(pdf_content)
                if text:
                    risk_count = text.lower().count('risk')
                    print(f"  → {method_name}: {len(text)} chars, {risk_count} risk instances")
                    
                    if risk_count > best_risk_count:
                        best_result = text
                        best_risk_count = risk_count
                        best_method = method_name
            
            if best_result and best_risk_count > 0:
                print(f"  → Using {best_method} (best result with {best_risk_count} risk instances)")
                
                # Extract raw risk phrases
                raw_risk_phrases = self.extract_risk_phrases(best_result)
                print(f"  → Extracted {len(raw_risk_phrases)} raw risk phrases")
                
                # Enhanced classify with ML and deduplication
                standard_risks, other_risks = self.classify_extracted_risks(raw_risk_phrases)
                
                # Format outputs
                standard_risks_str = '; '.join(standard_risks)
                other_risks_str = '; '.join(other_risks)
                
                print(f"  → Final result: {len(standard_risks)} standard risks, {len(other_risks)} other risks")
                if standard_risks:
                    print(f"  → Standard risks: {', '.join(standard_risks[:3])}{'...' if len(standard_risks) > 3 else ''}")
                if other_risks:
                    print(f"  → Other risks: {', '.join(other_risks[:2])}{'...' if len(other_risks) > 2 else ''}")
                
                return standard_risks_str, other_risks_str
            else:
                print(f"  → No 'risk' found in PDF content or text extraction failed")
                return "", ""
            
        except Exception as e:
            print(f"  → Error extracting risks from PDF {pdf_url}: {e}")
            return "", ""

    def get_master_risks_list(self) -> List[str]:
        """Return the list of all standardized risk categories."""
        return sorted(list(MASTER_RISKS.keys()))

    def export_master_risks_to_file(self, filename: str = "master_risks_dictionary.txt"):
        """Export the master risks dictionary to a text file for reference."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Enhanced Master Risk Dictionary with ML Classification\n")
                f.write("# Auto-generated list of standardized risk categories\n\n")
                
                for standard_risk, keywords in MASTER_RISKS.items():
                    f.write(f"## {standard_risk}\n")
                    f.write(f"Keywords: {', '.join(keywords)}\n\n")
                
                f.write(f"\nTotal Categories: {len(MASTER_RISKS)}\n")
                f.write(f"Total Keywords: {len(RISK_KEYWORDS_TO_STANDARD)}\n")
                f.write(f"ML Classification: {'Available' if self.ml_classifier.initialized else 'Not Available'}\n")
            
            print(f"✅ Enhanced master risks dictionary exported to: {filename}")
        except Exception as e:
            print(f"❌ Error exporting master risks: {e}")