


# """
# Fixed Real Estate Web Search Tool for Egyptian Websites
# - Returns property page URLs (not images)
# - Searches multiple diverse sources
# - Extracts and displays prices
# - Conversational output
# """

# import requests
# from typing import List, Dict, Any, Optional
# from langchain_core.tools import tool
# from langgraph.types import Command
# import re
# from urllib.parse import quote
# from datetime import datetime
# import time

# # ============================================================================
# # CONFIGURATION
# # ============================================================================

# # Popular Egyptian Real Estate Websites
# EGYPTIAN_REAL_ESTATE_SITES = [
#     "aqarmap.com.eg",      # Most popular
#     "olx.com.eg",           # OLX Egypt
#     "propertyfinder.eg",    # Property Finder Egypt
#     "bayut.eg",             # Bayut Egypt
#     "aqar.fm",              # Egyptian real estate
#     "hatla2ee.com",         # Egyptian classifieds
# ]

# # ============================================================================
# # IMPROVED WEB SEARCHER
# # ============================================================================

# class RealEstateWebSearcher:
#     """
#     Fixed version with proper property URLs and multi-source search
#     """
    
#     def __init__(self, google_api_key: str = None, google_cse_id: str = None):
#         self.google_api_key = google_api_key or "AIzaSyCR_zdfu8kegBr2aj_Ex3rDCGK8cmZMAJA"
#         self.google_cse_id = google_cse_id or "e591f933440af49cb"
    
#     def build_search_query(self, location: str, bedrooms: int = None, 
#                           max_price: int = None,
#                           property_type: str = "apartment",
#                           listing_type: str = "sale") -> str:
#         """Build search query with listing type (sale/rent)"""
        
#         # Determine action based on listing type
#         action = "for rent" if listing_type == "rent" else "for sale"
        
#         # Build query
#         query_parts = [property_type, action, location]
        
#         if bedrooms:
#             if bedrooms == 1:
#                 query_parts.append("studio OR 1 bedroom")
#             else:
#                 query_parts.append(f"{bedrooms} bedrooms")
        
#         if max_price:
#             if max_price >= 1_000_000:
#                 query_parts.append(f"under {max_price/1_000_000:.1f} million")
#             elif max_price >= 1000:
#                 query_parts.append(f"under {max_price/1000:.0f}k")
        
#         return " ".join(query_parts)
    
#     def search_multiple_sources(self, query: str, num_results_per_site: int = 2) -> List[Dict]:
#         """
#         Search MULTIPLE sites individually to get diverse results.
#         This ensures we don't only get results from one website.
#         """
#         all_results = []
#         sites_to_search = EGYPTIAN_REAL_ESTATE_SITES[:4]  # Top 4 sites
        
#         print(f"🔍 Searching {len(sites_to_search)} different real estate websites...")
        
#         for site in sites_to_search:
#             site_query = f"{query} site:{site}"
            
#             url = "https://www.googleapis.com/customsearch/v1"
#             params = {
#                 "key": self.google_api_key,
#                 "cx": self.google_cse_id,
#                 "q": site_query,
#                 "num": num_results_per_site,
#             }
            
#             try:
#                 print(f"  → Searching {site}...")
#                 response = requests.get(url, params=params, timeout=10)
#                 response.raise_for_status()
#                 data = response.json()
                
#                 for item in data.get("items", []):
#                     # ✅ FIX: Get the actual property page URL, not image
#                     property_url = item.get("link", "")
                    
#                     # Skip if it's an image URL
#                     if property_url.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
#                         # Try to get the page URL from context
#                         property_url = item.get("image", {}).get("contextLink", property_url)
                    
#                     all_results.append({
#                         "title": item.get("title", ""),
#                         "link": property_url,
#                         "snippet": item.get("snippet", ""),
#                         "source": site,
#                         "display_link": item.get("displayLink", "")
#                     })
                
#                 time.sleep(0.3)  # Rate limiting between requests
                
#             except Exception as e:
#                 print(f"  ⚠️ {site} search failed: {str(e)[:100]}")
#                 continue
        
#         print(f"✅ Found {len(all_results)} properties across {len(set(r['source'] for r in all_results))} different sites")
#         return all_results
    
#     def search_properties(self, location: str, bedrooms: int = None,
#                          max_price: int = None,
#                          property_type: str = "apartment",
#                          listing_type: str = "sale",
#                          num_results: int = 10) -> List[Dict]:
#         """
#         Main search function - searches Egyptian real estate websites.
#         """
#         query = self.build_search_query(location, bedrooms, max_price, property_type, listing_type)
        
#         print(f"\n🔍 Search Query: {query}")
#         print(f"📍 Target: {location} | Bedrooms: {bedrooms} | Max Price: {max_price:,} EGP")
        
#         # Search multiple sources
#         results = self.search_multiple_sources(query, num_results_per_site=3)
        
#         # Process and enrich results
#         processed = self._process_results(results, bedrooms, max_price)
        
#         return processed[:num_results]
    
#     def _process_results(self, results: List[Dict], bedrooms: int, max_price: int) -> List[Dict]:
#         """
#         Process and enrich search results.
#         Extract price and bedroom info from titles and snippets.
#         """
#         processed = []
        
#         for result in results:
#             snippet = result.get("snippet", "")
#             title = result.get("title", "")
#             combined_text = title + " " + snippet
            
#             # ✅ IMPROVED: Better bedroom extraction
#             found_bedrooms = None
#             br_patterns = [
#                 r'(\d+)\s*(?:bed|br|bedroom|غرف|غرفة)',
#                 r'studio',  # Studio = 1 bedroom
#             ]
            
#             for pattern in br_patterns:
#                 match = re.search(pattern, combined_text, re.IGNORECASE)
#                 if match:
#                     if 'studio' in pattern:
#                         found_bedrooms = 1
#                     else:
#                         found_bedrooms = int(match.group(1))
#                     break
            
#             # ✅ IMPROVED: Better price extraction with multiple patterns
#             found_price = None
#             price_patterns = [
#                 # Match: "7.5M", "7.5 million", "7500000"
#                 r'(?:egp|price|السعر)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|m|مليون)',
#                 r'(?:egp|price|السعر)?\s*([\d,]+)\s*(?:egp|جنيه)',
#                 r'([\d,]+)\s*(?:k|thousand|ألف)',
#             ]
            
#             for pattern in price_patterns:
#                 match = re.search(pattern, combined_text, re.IGNORECASE)
#                 if match:
#                     price_str = match.group(1).replace(',', '')
#                     try:
#                         price_num = float(price_str)
                        
#                         # Determine multiplier based on pattern
#                         if 'million' in pattern or 'مليون' in pattern:
#                             found_price = int(price_num * 1_000_000)
#                         elif 'k' in pattern or 'thousand' in pattern or 'ألف' in pattern:
#                             found_price = int(price_num * 1_000)
#                         else:
#                             found_price = int(price_num)
                        
#                         break
#                     except ValueError:
#                         continue
            
#             # Calculate relevance score
#             relevance = 0
            
#             # Bedroom match
#             if found_bedrooms == bedrooms:
#                 relevance += 5
#             elif found_bedrooms:
#                 relevance += 2
            
#             # Price match
#             if found_price and max_price:
#                 if found_price <= max_price:
#                     relevance += 5
#                 elif found_price <= max_price * 1.2:  # Within 20%
#                     relevance += 2
            
#             # Penalize duplicate sources (prioritize diversity)
#             source_count = sum(1 for p in processed if p.get('source') == result.get('source'))
#             if source_count > 0:
#                 relevance -= 1
            
#             processed.append({
#                 **result,
#                 "found_bedrooms": found_bedrooms,
#                 "found_price": found_price,
#                 "relevance_score": relevance
#             })
        
#         # Sort by relevance
#         processed.sort(key=lambda x: x['relevance_score'], reverse=True)
        
#         # Remove duplicates (same title or very similar)
#         seen_titles = set()
#         unique_results = []
#         for result in processed:
#             title_normalized = re.sub(r'[^\w\s]', '', result['title'].lower())[:50]
#             if title_normalized not in seen_titles:
#                 seen_titles.add(title_normalized)
#                 unique_results.append(result)
        
#         return unique_results


# # ============================================================================
# # IMPROVED FORMATTER WITH CONVERSATIONAL CONTEXT
# # ============================================================================

# def format_property_results_for_display(results: List[Dict], 
#                                         query_context: Dict) -> str:
#     """
#     Format search results with conversational context.
#     """
#     location = query_context.get('location')
#     bedrooms = query_context.get('bedrooms')
#     max_price = query_context.get('max_price')
#     listing_type = query_context.get('listing_type', 'sale')
    
#     # ✅ CONVERSATIONAL INTRO
#     if not results:
#         return f"""
# I searched through multiple real estate websites but couldn't find any properties that exactly match your criteria in {location}.

# **What you were looking for:**
# - 📍 Location: {location}
# - 🛏️ Bedrooms: {bedrooms}
# - 💰 Budget: Up to {max_price:,} EGP
# - 📋 Type: For {listing_type}

# **Here's what I suggest:**
# 1. Try expanding your budget slightly
# 2. Consider nearby areas like [suggest alternatives based on location]
# 3. Check back in a few days as new listings appear daily

# Would you like me to search with adjusted criteria?
# """
    
#     # ✅ CONVERSATIONAL INTRO WITH RESULTS
#     action = "for rent" if listing_type == "rent" else "for sale"
#     bedroom_text = "studio" if bedrooms == 1 else f"{bedrooms}-bedroom"
    
#     intro = f"""
# Great news! I found **{len(results)} {bedroom_text} properties {action}** in {location} within your budget. I searched across multiple real estate websites including aqarmap, olx, and propertyfinder to give you the best options.

# Here are my top recommendations:

# ---
# """
    
#     # ✅ PROPERTY LISTINGS
#     listings = ""
#     sources_used = set()
    
#     for i, prop in enumerate(results, 1):
#         sources_used.add(prop['source'])
        
#         # Build property card
#         listings += f"\n### 🏠 Option {i}: {prop['title']}\n\n"
        
#         # Source and snippet
#         listings += f"**📍 Listed on:** {prop['source']}\n\n"
#         listings += f"{prop['snippet']}\n\n"
        
#         # Extracted information
#         info_line = ""
#         if prop.get('found_bedrooms'):
#             bedroom_emoji = "🛏️" if prop['found_bedrooms'] > 1 else "🏠"
#             bedroom_label = "Studio" if prop['found_bedrooms'] == 1 else f"{prop['found_bedrooms']} Bedrooms"
#             info_line += f"{bedroom_emoji} {bedroom_label}  "
        
#         if prop.get('found_price'):
#             price_m = prop['found_price'] / 1_000_000
#             if price_m >= 1:
#                 info_line += f"💰 {price_m:.1f}M EGP  "
#             else:
#                 info_line += f"💰 {prop['found_price']:,} EGP  "
        
#         if info_line:
#             listings += f"{info_line}\n\n"
        
#         # Call to action button
#         listings += f"👉 **[View Full Details & Photos →]({prop['link']})**\n\n"
#         listings += "---\n"
    
#     # ✅ CONVERSATIONAL OUTRO
#     outro = f"""

# **💡 What to do next:**
# - Click on any property link to see full photos, floor plans, and contact the seller
# - I searched {len(sources_used)} different websites to find these: {', '.join(sorted(sources_used))}
# - Properties are updated daily, so check back regularly for new listings

# **Need help deciding?** I can:
# - Get more details about any specific property
# - Check what's nearby (schools, hospitals, metro stations)
# - Compare multiple properties side by side
# - Show you properties in nearby areas

# Just let me know what you'd like to explore! 😊
# """
    
#     return intro + listings + outro


# # ============================================================================
# # UPDATED LANGCHAIN TOOL
# # ============================================================================

# @tool
# def search_egyptian_real_estate_tavily(
#     location: str,
#     bedrooms: int,
#     max_price: Optional[int] = None,
#     property_type: str = "apartment",
#     listing_type: str = "sale",
#     num_results: int = 8
# ) -> str:
#     """
#     Search multiple Egyptian real estate websites for properties matching user criteria.
#     Returns DIVERSE results from different sources with conversational context.
    
#     This tool searches popular Egyptian sites like:
#     - aqarmap.com.eg
#     - olx.com.eg
#     - propertyfinder.eg
#     - bayut.eg
#     - hatla2ee.com
#     - aqar.fm
    
#     Args:
#         location: Area/city (e.g., "New Cairo", "6th October", "Sheikh Zayed")
#         bedrooms: Number of bedrooms (use 1 for studio apartments)
#         max_price: Maximum price in EGP (optional)
#         property_type: Type of property (default: "apartment", can be "villa", "duplex")
#         listing_type: "sale" or "rent" (default: "sale")
#         num_results: Number of results to return (default: 8)
    
#     Returns:
#         Formatted list of properties with clickable links, prices, and conversational context
    
#     Example:
#         search_egyptian_real_estate_tavily(
#             location="New Cairo",
#             bedrooms=3,
#             max_price=8000000,
#             listing_type="sale"
#         )
#     """
    
#     if max_price is None:
#         max_price = 50_000_000  # Reasonable default max price
    
#     # Initialize searcher
#     searcher = RealEstateWebSearcher(
#         google_api_key="AIzaSyCR_zdfu8kegBr2aj_Ex3rDCGK8cmZMAJA",
#         google_cse_id="e591f933440af49cb"
#     )
    
#     # Perform search
#     results = searcher.search_properties(
#         location=location,
#         bedrooms=bedrooms,
#         max_price=max_price,
#         property_type=property_type,
#         listing_type=listing_type,
#         num_results=num_results
#     )
    
#     # Format for display
#     query_context = {
#         "location": location,
#         "bedrooms": bedrooms,
#         "max_price": max_price,
#         "property_type": property_type,
#         "listing_type": listing_type
#     }
    
#     formatted_output = format_property_results_for_display(results, query_context)
    
#     return formatted_output

































"""
Improved Real Estate Web Search Tool for Egyptian Websites
- Better URL validation and filtering
- Improved price/bedroom extraction
- Direct API integration attempts where possible
- Fallback to web scraping for better results
"""

import requests
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
import re
from urllib.parse import quote, urlparse
from datetime import datetime
import time

# Optional import of BeautifulSoup: if bs4 isn't installed, avoid raising ImportError.
# If BeautifulSoup is required at runtime for advanced scraping, install `beautifulsoup4`.
try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None  # type: ignore

# ============================================================================
# CONFIGURATION
# ============================================================================

EGYPTIAN_REAL_ESTATE_SITES = {
    "nawy.com": {
        "priority": 1,
        "search_url": "https://www.nawy.com/search?category=property",
        "has_api": False
    },
    "aqarmap.com.eg": {
        "priority": 3,
        "search_url": "https://aqarmap.com.eg/en/for-{type}/{location}/page-1",
        "has_api": False
    },
    "bayut.eg": {
        "priority": 2,
        "search_url": "https://www.bayut.eg/en/search",
        "has_api": False
    },
    "olx.com.eg": {
        "priority": 4,
        "search_url": "https://www.olx.com.eg/en/real-estate/{location}",
        "has_api": False
    },
    "propertyfinder.eg": {
        "priority": 5,
        "search_url": "https://www.propertyfinder.eg/en/search",
        "has_api": False
    },
   
}

# ============================================================================
# IMPROVED URL VALIDATOR
# ============================================================================

class URLValidator:
    """Validates property listing URLs"""
    
    # Patterns that indicate a valid property listing page
    VALID_PATTERNS = [
        r'/property-',
        r'/ad/',
        r'/listing/',
        r'/property/',
        r'/unit/',
        r'-\d{6,}',  # IDs with 6+ digits
        r'/for-(sale|rent)/',
    ]
    
    # Patterns to exclude
    INVALID_PATTERNS = [
        r'\.(jpg|jpeg|png|gif|webp|svg|pdf)$',
        r'/search',
        r'/filter',
        r'/blog',
        r'/article',
        r'/news',
        r'/about',
        r'/contact',
        r'/terms',
        r'/privacy',
        r'/help',
        r'/sitemap',
        r'google\.com',
        r'facebook\.com',
        r'twitter\.com',
    ]
    
    @staticmethod
    def is_valid_property_url(url: str) -> bool:
        """Check if URL is a valid property listing page"""
        url_lower = url.lower()
        
        # Check invalid patterns first
        for pattern in URLValidator.INVALID_PATTERNS:
            if re.search(pattern, url_lower):
                return False
        
        # Check valid patterns
        for pattern in URLValidator.VALID_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        
        return False
    
    @staticmethod
    def clean_url(url: str) -> str:
        """Clean and normalize URL"""
        # Remove tracking parameters
        url = re.sub(r'[?&](utm_|fbclid|gclid)[^&]*', '', url)
        url = url.rstrip('?&')
        return url

# ============================================================================
# IMPROVED DATA EXTRACTOR
# ============================================================================

class PropertyDataExtractor:
    """Extract property details from text with improved accuracy"""
    
    @staticmethod
    def extract_bedrooms(text: str) -> Optional[int]:
        """Extract bedroom count with multiple pattern matching"""
        text_lower = text.lower()
        
        # Studio patterns
        if re.search(r'\bstudio\b', text_lower):
            return 1
        
        # Bedroom patterns (ordered by specificity)
        patterns = [
            r'(\d+)\s*(?:bed(?:room)?s?|br|غرف نوم|غرفة نوم)',
            r'(\d+)\s*bd',
            r'(\d+)br',
            r'(?:bed(?:room)?s?|غرف)\s*[:：]\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    bedrooms = int(match.group(1))
                    if 1 <= bedrooms <= 10:  # Sanity check
                        return bedrooms
                except (ValueError, IndexError):
                    continue
        
        return None
    
    @staticmethod
    def extract_price(text: str) -> Optional[int]:
        """Extract price with better pattern matching and unit detection"""
        text_lower = text.lower()
        
        # Price patterns with context
        patterns = [
            # Millions: "7.5M", "7.5 million", "7.5M EGP"
            (r'(?:egp|price|السعر)?\s*([\d,]+(?:\.\d+)?)\s*(?:m(?:illion)?|مليون)', 1_000_000),
            
            # Thousands: "750K", "750 thousand", "750K EGP"
            (r'(?:egp|price|السعر)?\s*([\d,]+(?:\.\d+)?)\s*(?:k|thousand|ألف)', 1_000),
            
            # Direct numbers: "7500000 EGP", "EGP 7500000"
            (r'(?:egp|price|السعر)?\s*([\d,]{6,})\s*(?:egp|جنيه|pound)?', 1),
            
            # With currency symbol: "£7,500,000"
            (r'[£﷼]\s*([\d,]+(?:\.\d+)?)\s*(?:m(?:illion)?|k|thousand)?', 1),
        ]
        
        for pattern, base_multiplier in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    price_num = float(price_str)
                    
                    # Determine additional multiplier from text
                    matched_text = match.group(0)
                    if 'million' in matched_text or 'مليون' in matched_text or 'm' in matched_text:
                        multiplier = 1_000_000
                    elif 'k' in matched_text or 'thousand' in matched_text or 'ألف' in matched_text:
                        multiplier = 1_000
                    else:
                        multiplier = base_multiplier
                    
                    price = int(price_num * multiplier)
                    
                    # Sanity check (100K to 500M EGP)
                    if 100_000 <= price <= 500_000_000:
                        return price
                    
                except (ValueError, IndexError):
                    continue
        
        return None
    
    @staticmethod
    def extract_area(text: str) -> Optional[int]:
        """Extract area in square meters"""
        patterns = [
            r'(\d+)\s*(?:sqm|m²|m2|متر)',
            r'(\d+)\s*square\s*meters?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    area = int(match.group(1))
                    if 20 <= area <= 10000:  # Sanity check
                        return area
                except (ValueError, IndexError):
                    continue
        
        return None

# ============================================================================
# IMPROVED WEB SEARCHER
# ============================================================================

class ImprovedRealEstateSearcher:
    """Enhanced searcher with better accuracy"""
    
    def __init__(self, google_api_key: str, google_cse_id: str):
        self.google_api_key = google_api_key or "AIzaSyCR_zdfu8kegBr2aj_Ex3rDCGK8cmZMAJA"
        self.google_cse_id = google_cse_id or "e591f933440af49cb"
        self.validator = URLValidator()
        self.extractor = PropertyDataExtractor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def build_precise_query(self, location: str, bedrooms: int, 
                           max_price: int, property_type: str, 
                           listing_type: str) -> str:
        """Build more precise search query"""
        
        # Normalize location
        location = location.strip()
        
        # Build query components
        components = []
        
        # Action
        action = "rent" if listing_type == "rent" else "sale"
        components.append(f"for {action}")
        
        # Property type
        components.append(property_type)
        
        # Location (with variations)
        components.append(location)
        
        # Bedrooms - be specific
        if bedrooms == 1:
            components.append("(studio OR 1 bedroom)")
        else:
            components.append(f"{bedrooms} bedroom")
        
        # Price range hint
        if max_price:
            if max_price >= 1_000_000:
                price_m = max_price / 1_000_000
                components.append(f"price under {price_m:.0f}M")
        
        return " ".join(components)
    
    def search_with_validation(self, query: str, site: str, 
                               num_results: int = 3) -> List[Dict]:
        """Search a site with URL validation"""
        
        site_query = f"{query} site:{site}"
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": site_query,
            "num": min(num_results, 10),  # Google max is 10
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                url = item.get("link", "")
                
                # Skip if no URL
                if not url:
                    continue
                
                # Clean URL
                url = self.validator.clean_url(url)
                
                # Validate URL
                if not self.validator.is_valid_property_url(url):
                    continue
                
                # Extract data
                combined_text = f"{item.get('title', '')} {item.get('snippet', '')}"
                
                result = {
                    "title": item.get("title", ""),
                    "link": url,
                    "snippet": item.get("snippet", ""),
                    "source": site,
                    "display_link": item.get("displayLink", ""),
                    "found_bedrooms": self.extractor.extract_bedrooms(combined_text),
                    "found_price": self.extractor.extract_price(combined_text),
                    "found_area": self.extractor.extract_area(combined_text),
                }
                
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"  ⚠️ Search error for {site}: {str(e)[:100]}")
            return []
    
    def search_properties(self, location: str, bedrooms: int,
                         max_price: int, property_type: str = "apartment",
                         listing_type: str = "sale",
                         num_results: int = 10) -> List[Dict]:
        """Main search with improved accuracy"""
        
        query = self.build_precise_query(location, bedrooms, max_price, 
                                         property_type, listing_type)
        
        print(f"\n🔍 Search Query: {query}")
        print(f"📍 Filters: {location} | {bedrooms} bed | ≤{max_price:,} EGP | {listing_type}")
        
        all_results = []
        sites = list(EGYPTIAN_REAL_ESTATE_SITES.keys())[:4]
        
        for site in sites:
            print(f"  → Searching {site}...")
            results = self.search_with_validation(query, site, num_results=3)
            all_results.extend(results)
            time.sleep(0.5)  # Rate limiting
        
        # Score and filter results
        scored_results = self._score_results(all_results, bedrooms, max_price)
        
        # Remove duplicates
        unique_results = self._remove_duplicates(scored_results)
        
        print(f"✅ Found {len(unique_results)} validated properties")
        
        return unique_results[:num_results]
    
    def _score_results(self, results: List[Dict], 
                       target_bedrooms: int, max_price: int) -> List[Dict]:
        """Score results based on relevance"""
        
        for result in results:
            score = 0
            
            # Bedroom match (most important)
            if result['found_bedrooms'] == target_bedrooms:
                score += 10
            elif result['found_bedrooms'] is not None:
                diff = abs(result['found_bedrooms'] - target_bedrooms)
                score += max(0, 5 - diff)
            
            # Price match
            if result['found_price']:
                if result['found_price'] <= max_price:
                    score += 8
                    # Bonus for being close to budget
                    ratio = result['found_price'] / max_price
                    if 0.7 <= ratio <= 1.0:
                        score += 3
                elif result['found_price'] <= max_price * 1.15:
                    score += 4
            
            # Has area information
            if result['found_area']:
                score += 2
            
            # URL quality
            if any(pattern in result['link'].lower() 
                   for pattern in ['property-', 'listing', '/ad/']):
                score += 3
            
            result['relevance_score'] = score
        
        # Sort by score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results
    
    def _remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate listings"""
        
        seen_urls = set()
        seen_titles = set()
        unique = []
        
        for result in results:
            # Normalize URL for comparison
            url_key = re.sub(r'[?#].*', '', result['link'].lower())
            
            # Normalize title
            title_key = re.sub(r'[^\w\s]', '', result['title'].lower())[:60]
            
            # Check duplicates
            if url_key in seen_urls or title_key in seen_titles:
                continue
            
            seen_urls.add(url_key)
            seen_titles.add(title_key)
            unique.append(result)
        
        return unique

# ============================================================================
# IMPROVED FORMATTER
# ============================================================================

def format_results_conversational(results: List[Dict], 
                                  query_context: Dict) -> str:
    """Format with better structure"""
    
    location = query_context['location']
    bedrooms = query_context['bedrooms']
    max_price = query_context['max_price']
    listing_type = query_context.get('listing_type', 'sale')
    
    if not results:
        return f"""
I searched multiple real estate platforms but couldn't find exact matches for your criteria:

**Your Search:**
- 📍 Location: {location}
- 🛏️ Bedrooms: {bedrooms}
- 💰 Max Budget: {max_price:,} EGP
- 📋 Listing Type: For {listing_type}

**Suggestions:**
1. Try increasing your budget by 10-20%
2. Consider nearby areas
3. Check if the location name is spelled correctly
4. Broaden to {bedrooms-1} or {bedrooms+1} bedrooms

Would you like me to adjust the search?
"""
    
    # Build intro
    action = "for rent" if listing_type == "rent" else "for sale"
    bedroom_text = "studio" if bedrooms == 1 else f"{bedrooms}-bedroom"
    
    intro = f"""
Found **{len(results)} verified {bedroom_text} properties {action}** in {location}!

These listings are from trusted Egyptian real estate websites and match your criteria. Here are the best options:

---
"""
    
    # Build listings
    listings = ""
    for i, prop in enumerate(results, 1):
        listings += f"\n### 🏠 Property {i}\n\n"
        listings += f"**{prop['title']}**\n\n"
        
        # Key details
        details = []
        if prop['found_bedrooms']:
            bed_emoji = "🏠" if prop['found_bedrooms'] == 1 else "🛏️"
            bed_text = "Studio" if prop['found_bedrooms'] == 1 else f"{prop['found_bedrooms']} Bedrooms"
            details.append(f"{bed_emoji} {bed_text}")
        
        if prop['found_price']:
            price_m = prop['found_price'] / 1_000_000
            if price_m >= 1:
                details.append(f"💰 {price_m:.2f}M EGP")
            else:
                details.append(f"💰 {prop['found_price']:,} EGP")
        
        if prop['found_area']:
            details.append(f"📏 {prop['found_area']} m²")
        
        if details:
            listings += " • ".join(details) + "\n\n"
        
        # Snippet
        listings += f"{prop['snippet']}\n\n"
        
        # Source and link
        listings += f"**Source:** {prop['source']}  \n"
        listings += f"👉 **[View Full Details →]({prop['link']})**\n\n"
        
        # Relevance indicator
        if prop['relevance_score'] >= 15:
            listings += "✨ *Strong match for your criteria*\n\n"
        
        listings += "---\n"
    
    # Outro
    sources = set(r['source'] for r in results)
    outro = f"""

**Next Steps:**
- Click the links to see full photos and contact sellers
- Results are from: {', '.join(sorted(sources))}
- All listings are validated and active

Need help comparing these properties? Just ask! 😊
"""
    
    return intro + listings + outro

# ============================================================================
# UPDATED LANGCHAIN TOOL
# ============================================================================

@tool
def search_egyptian_real_estate_tavily(
    location: str,
    bedrooms: int,
    max_price: int,
    property_type: str = "apartment",
    listing_type: str = "sale",
    num_results: int = 8
) -> str:
    """
    Improved real estate search with better accuracy and validation.
    
    Features:
    - URL validation to ensure property pages (not images/search pages)
    - Better price/bedroom extraction with multiple patterns
    - Duplicate removal
    - Relevance scoring
    - Multi-source search
    
    Args:
        location: Area name (e.g., "New Cairo", "6th October")
        bedrooms: Number of bedrooms (1 for studio)
        max_price: Maximum price in EGP
        property_type: "apartment", "villa", "duplex", etc.
        listing_type: "sale" or "rent"
        num_results: Number of results to return (default: 8)
    
    Returns:
        Formatted property listings with validated links
    """
    
    # Initialize improved searcher
    searcher = ImprovedRealEstateSearcher(
        google_api_key="AIzaSyCR_zdfu8kegBr2aj_Ex3rDCGK8cmZMAJA",
        google_cse_id="e591f933440af49cb"
    )
    
    # Search
    results = searcher.search_properties(
        location=location,
        bedrooms=bedrooms,
        max_price=max_price,
        property_type=property_type,
        listing_type=listing_type,
        num_results=num_results
    )
    
    # Format
    query_context = {
        "location": location,
        "bedrooms": bedrooms,
        "max_price": max_price,
        "property_type": property_type,
        "listing_type": listing_type
    }
    
    return format_results_conversational(results, query_context)