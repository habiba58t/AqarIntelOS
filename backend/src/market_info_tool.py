"""
Egyptian Real Estate Market Intelligence Tool
Separate tool for market information, trends, regulations, investment analysis
(NOT for property listings - use search_egyptian_real_estate_tavily for that)
"""

from langchain_core.tools import tool
from typing import Literal, Optional, List, Dict, Any
from tavily import TavilyClient
import os
from datetime import datetime
import re

# Initialize Tavily client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


# =============================================
# 🎯 TRUSTED EGYPTIAN REAL ESTATE INFO SOURCES
# =============================================

TRUSTED_INFO_SOURCES = {
    # Market Research & Analytics
    "globalpropertyguide.com": {
        "priority": "high",
        "specialty": "Price indices, historical trends, macro analysis, international comparisons",
        "best_for": ["market trends", "price history", "growth rates"]
    },
    "mordorintelligence.com": {
        "priority": "high",
        "specialty": "5-year forecasts, CAGR, market segmentation, investment analysis",
        "best_for": ["forecasts", "market size", "investment outlook"]
    },
    "imarcgroup.com": {
        "priority": "high",
        "specialty": "Long-term projections, structural trends, market sizing",
        "best_for": ["long-term forecast", "market drivers", "future trends"]
    },
    "valustrat.com": {
        "priority": "high",
        "specialty": "Price indices, market monitoring, transparent methodology",
        "best_for": ["price indices", "market performance", "valuation"]
    },
    
    # International Real Estate Research Firms
    "jll.com.eg": {
        "priority": "high",
        "specialty": "Quarterly market reports, rental indices, professional analysis",
        "best_for": ["market updates", "rental market", "investment trends"]
    },
    "cushmanwakefield.com": {
        "priority": "high",
        "specialty": "MarketBeat reports, sector analysis, investment flows",
        "best_for": ["market analysis", "investment volumes", "sector trends"]
    },
    "savills.com": {
        "priority": "high",
        "specialty": "Market research, investment advice, global perspectives",
        "best_for": ["investment strategy", "market outlook", "comparisons"]
    },
    "cbre.com": {
        "priority": "high",
        "specialty": "Market research, valuations, investment analysis",
        "best_for": ["market intelligence", "valuations", "trends"]
    },
    "knightfrank.com": {
        "priority": "medium",
        "specialty": "Luxury segment, high-end market analysis",
        "best_for": ["luxury market", "prime locations", "wealth report"]
    },
    
    # Local Market Data Platforms
    "aqarmap.com.eg/ar/research": {
        "priority": "high",
        "specialty": "Neighborhood pricing trends, supply/demand analysis, local insights",
        "best_for": ["area trends", "price per meter trends", "demand analysis"]
    },
    "propertyfinder.eg": {
        "priority": "high",
        "specialty": "Annual market reports, developer activity, project pipelines",
        "best_for": ["new projects", "developer trends", "market activity"]
    },
    
    # Arabic Market Analysis
    "masrlilaqarat.com": {
        "priority": "medium",
        "specialty": "Local market insights in Arabic, neighborhood guides",
        "best_for": ["local perspectives", "cultural insights", "arabic content"]
    },
    "albayanalarabi.com": {
        "priority": "medium",
        "specialty": "Arabic market reports, investment analysis",
        "best_for": ["arabic analysis", "local investor views"]
    },
    
    # Government & Regulatory
    "cbe.org.eg": {
        "priority": "high",
        "specialty": "Central Bank reports, economic indicators, lending data",
        "best_for": ["economic data", "inflation", "interest rates", "lending"]
    },
    "mof.gov.eg": {
        "priority": "high",
        "specialty": "Ministry of Finance, fiscal policy, tax regulations",
        "best_for": ["taxes", "fiscal policy", "government budget"]
    },
    "moss.gov.eg": {
        "priority": "high",
        "specialty": "Ministry of Housing, development projects, regulations",
        "best_for": ["housing policy", "regulations", "government projects"]
    },
    "nuca.gov.eg": {
        "priority": "medium",
        "specialty": "New Urban Communities Authority, new cities development",
        "best_for": ["new cities", "urban planning", "land allocation"]
    },
    
    # Legal & Regulatory Information
    "tamimi.com": {
        "priority": "medium",
        "specialty": "Legal insights, real estate law, regulatory updates",
        "best_for": ["legal issues", "regulations", "compliance"]
    },
    "lexology.com": {
        "priority": "medium",
        "specialty": "Legal updates, regulatory changes, expert analysis",
        "best_for": ["law changes", "legal analysis", "compliance"]
    },
    
    # Financial & Economic News
    "dailynewsegypt.com": {
        "priority": "medium",
        "specialty": "Real estate news, market updates, policy changes",
        "best_for": ["current news", "policy updates", "market events"]
    },
    "egypttoday.com": {
        "priority": "medium",
        "specialty": "Current events, real estate sector news",
        "best_for": ["breaking news", "sector updates"]
    },
    "zawya.com": {
        "priority": "medium",
        "specialty": "Financial news, investment analysis, MENA focus",
        "best_for": ["financial analysis", "investment news", "regional context"]
    },
    "reuters.com": {
        "priority": "medium",
        "specialty": "International news, economic updates",
        "best_for": ["major news", "economic context", "global perspective"]
    },
    
    # Investment & Analysis
    "colliers.com": {
        "priority": "medium",
        "specialty": "Investment research, market reports",
        "best_for": ["investment analysis", "market research"]
    }
}


# =============================================
# 🧠 QUERY CLASSIFICATION FOR INFO SEARCHES
# =============================================

INFO_QUERY_PATTERNS = {
    "market_trends": {
        "keywords": ["trend", "growing", "rising", "falling", "direction", "momentum", "shift", "change"],
        "sources": ["globalpropertyguide.com", "jll.com.eg", "mordorintelligence.com", "aqarmap.com.eg"],
        "search_terms": ["egypt real estate trends", "market direction", "growth momentum"]
    },
    
    "pricing_analysis": {
        "keywords": ["price trend", "appreciation", "depreciation", "price growth", "per meter", "valuation", "pricing"],
        "sources": ["valustrat.com", "aqarmap.com.eg", "globalpropertyguide.com"],
        "search_terms": ["egypt property prices", "price appreciation", "valuation trends"]
    },
    
    "investment_advice": {
        "keywords": ["invest", "roi", "return", "yield", "profit", "best investment", "where to invest", "opportunity"],
        "sources": ["mordorintelligence.com", "jll.com.eg", "savills.com", "cushmanwakefield.com"],
        "search_terms": ["egypt real estate investment", "roi analysis", "investment opportunities"]
    },
    
    "market_forecast": {
        "keywords": ["forecast", "future", "prediction", "outlook", "2026", "2027", "2028", "projection", "expected"],
        "sources": ["mordorintelligence.com", "imarcgroup.com", "jll.com.eg"],
        "search_terms": ["egypt real estate forecast", "market outlook", "future trends"]
    },
    
    "regulations_laws": {
        "keywords": ["law", "regulation", "legal", "rule", "permit", "license", "compliance", "tax", "registration"],
        "sources": ["tamimi.com", "lexology.com", "mof.gov.eg", "moss.gov.eg"],
        "search_terms": ["egypt real estate law", "property regulations", "legal requirements"]
    },
    
    "economic_factors": {
        "keywords": ["inflation", "currency", "interest rate", "economy", "gdp", "economic", "devaluation"],
        "sources": ["cbe.org.eg", "reuters.com", "zawya.com"],
        "search_terms": ["egypt economy real estate", "inflation impact", "economic indicators"]
    },
    
    "government_policy": {
        "keywords": ["government", "policy", "initiative", "program", "subsidy", "mortgage", "financing"],
        "sources": ["moss.gov.eg", "cbe.org.eg", "dailynewsegypt.com"],
        "search_terms": ["egypt housing policy", "government initiatives", "mortgage program"]
    },
    
    "developer_activity": {
        "keywords": ["developer", "construction", "delivery", "project pipeline", "new launch", "builder"],
        "sources": ["propertyfinder.eg", "cushmanwakefield.com", "zawya.com"],
        "search_terms": ["egypt developers", "new projects", "construction activity"]
    },
    
    "rental_market": {
        "keywords": ["rental", "rent", "lease", "tenant", "occupancy", "rental yield"],
        "sources": ["jll.com.eg", "aqarmap.com.eg", "cushmanwakefield.com"],
        "search_terms": ["egypt rental market", "rental yields", "tenant demand"]
    },
    
    "market_size": {
        "keywords": ["market size", "market value", "total value", "market worth", "industry size"],
        "sources": ["mordorintelligence.com", "imarcgroup.com", "colliers.com"],
        "search_terms": ["egypt real estate market size", "industry value", "market worth"]
    },
    
    "new_cities": {
        "keywords": ["new capital", "new cities", "satellite city", "urban development", "smart city"],
        "sources": ["nuca.gov.eg", "propertyfinder.eg", "dailynewsegypt.com"],
        "search_terms": ["egypt new cities", "new administrative capital", "urban development"]
    },
    
    "foreign_investment": {
        "keywords": ["foreign", "expat", "international", "foreign investor", "non-egyptian"],
        "sources": ["tamimi.com", "jll.com.eg", "zawya.com"],
        "search_terms": ["egypt foreign investment", "expat property", "international investors"]
    }
}


def classify_info_query(query: str) -> Dict[str, Any]:
    """
    Classify market information queries (not property searches)
    """
    query_lower = query.lower()
    
    # Detect categories
    detected_categories = []
    for category, config in INFO_QUERY_PATTERNS.items():
        if any(keyword in query_lower for keyword in config["keywords"]):
            detected_categories.append(category)
    
    # Default to market trends if nothing specific detected
    if not detected_categories:
        detected_categories = ["market_trends"]
    
    # Extract temporal context
    years = re.findall(r'20\d{2}', query_lower)
    
    # Detect if question is about specific location (for context)
    egypt_locations = [
        "new cairo", "6th october", "sheikh zayed", "new administrative capital", "new capital",
        "zamalek", "maadi", "heliopolis", "north coast", "ain sokhna",
        "5th settlement", "fifth settlement", "nasr city", "giza", "cairo", "alexandria",
        "hurghada", "sharm el sheikh", "el gouna"
    ]
    
    mentioned_locations = [loc for loc in egypt_locations if loc in query_lower]
    
    return {
        "categories": detected_categories,
        "locations": mentioned_locations,
        "years": years,
        "is_comparative": any(word in query_lower for word in ["compare", "vs", "versus", "difference", "better"]),
        "is_future_focused": any(word in query_lower for word in ["future", "forecast", "will", "2026", "2027", "2028"]),
        "is_regulatory": "regulations_laws" in detected_categories or "government_policy" in detected_categories
    }


def build_info_search_query(user_query: str, classification: Dict[str, Any]) -> str:
    """
    Build optimized search query for information (not property listings)
    """
    base_terms = ["egypt", "real estate"]
    
    # Add primary category terms
    if classification["categories"]:
        primary_category = classification["categories"][0]
        base_terms.extend(INFO_QUERY_PATTERNS[primary_category]["search_terms"][:2])
    
    # Add temporal context
    if classification["is_future_focused"]:
        base_terms.append("2025 2026")
    else:
        base_terms.append("2025")
    
    # Add location if mentioned (for context)
    if classification["locations"]:
        base_terms.append(classification["locations"][0])
    
    # Construct query
    enhanced_query = f"{user_query} {' '.join(base_terms[:4])}"
    
    return enhanced_query[:200]


def build_info_domain_filter(classification: Dict[str, Any]) -> List[str]:
    """
    Build priority domains for information search
    """
    priority_domains = []
    
    # Get sources for each category
    for category in classification["categories"]:
        if category in INFO_QUERY_PATTERNS:
            category_sources = INFO_QUERY_PATTERNS[category]["sources"]
            priority_domains.extend(category_sources)
    
    # Remove duplicates
    seen = set()
    filtered = []
    for domain in priority_domains:
        if domain not in seen:
            seen.add(domain)
            filtered.append(domain)
    
    return filtered[:6]  # Top 6 sources


# =============================================
# 🔍 MAIN MARKET INTELLIGENCE TOOL
# =============================================

@tool
def search_market_intelligence(
    query: str,
    max_results: int = 10,
    include_answer: bool = True,
    search_depth: Literal["basic", "advanced"] = "advanced"
) -> str:
    """
    Search for Egyptian real estate MARKET INFORMATION - trends, investments, 
    regulations, laws, economic factors, forecasts, analysis, and advice.
    
    ⚠️ DO NOT USE for property listings - use search_egyptian_real_estate_tavily for that!
    
    USE THIS TOOL FOR QUESTIONS ABOUT:
    ✅ Market trends ("What are current trends in Egyptian real estate?")
    ✅ Price trends & appreciation ("How are prices changing in Egypt?")
    ✅ Investment advice ("Best areas to invest?", "ROI analysis?", "Is it good time to invest?")
    ✅ Market forecasts ("What's the outlook for 2026?", "Future of Egyptian market?")
    ✅ Regulations & laws ("What are property ownership laws?", "Foreign ownership rules?")
    ✅ Economic factors ("How does inflation affect real estate?", "Currency impact?")
    ✅ Government policies ("What are government housing initiatives?", "Mortgage programs?")
    ✅ Developer activity ("Top developers?", "New project pipelines?")
    ✅ Rental market analysis ("Rental yields?", "Tenant demand trends?")
    ✅ Market size & growth ("How big is the market?", "Growth rate?")
    ✅ New cities development ("Tell me about New Administrative Capital")
    ✅ Foreign investment rules ("Can foreigners buy?", "Investment restrictions?")
    
    ❌ DO NOT USE for:
    - Finding specific properties/units ("Show me 3-bedroom apartments")
    - Property listings ("What's available in New Cairo?")
    - Specific unit searches (use search_egyptian_real_estate_tavily instead)
    
    Args:
        query: Market information question (not property search)
        max_results: Number of sources to return (default: 10)
        include_answer: Include AI-generated summary (default: True)
        search_depth: "basic" for quick, "advanced" for comprehensive
    
    Returns:
        Formatted market intelligence with expert sources and analysis
    """
    
    try:
        print(f"\n🧠 MARKET INTELLIGENCE SEARCH")
        print(f"📝 Query: {query}")
        
        # Step 1: Classify query
        classification = classify_info_query(query)
        print(f"🎯 Categories: {classification['categories']}")
        
        # Step 2: Build search query
        search_query = build_info_search_query(query, classification)
        print(f"🔎 Enhanced: {search_query}")
        
        # Step 3: Get priority domains
        domains = build_info_domain_filter(classification)
        print(f"🌐 Sources: {domains}")
        
        # Step 4: Execute search
        search_params = {
            "query": search_query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": include_answer,
            "include_domains": domains if domains else None
        }
        
        print(f"⚙️ Searching...")
        response = tavily_client.search(**search_params)
        
        # Step 5: Format results
        output = format_intelligence_report(response, classification, query)
        
        return output
        
    except Exception as e:
        error_msg = f"❌ Search Error: {str(e)}\n\n"
        error_msg += "🔄 Attempting fallback search...\n"
        
        try:
            # Fallback without domain restrictions
            fallback_response = tavily_client.search(
                query=query + " egypt real estate 2025",
                max_results=max_results,
                include_answer=True
            )
            return format_intelligence_report(fallback_response, classification, query)
        except Exception as fallback_error:
            return f"❌ Search failed: {str(fallback_error)}\n\n💡 Suggestion: Try rephrasing your question or being more specific about what information you need."


def format_intelligence_report(
    response: Dict[str, Any],
    classification: Dict[str, Any],
    original_query: str
) -> str:
    """
    Format search results into professional market intelligence report
    """
    output = []
    
    # Header
    output.append("=" * 90)
    output.append("📊 EGYPTIAN REAL ESTATE MARKET INTELLIGENCE REPORT")
    output.append("=" * 90)
    output.append(f"🔍 Query: {original_query}")
    output.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append(f"🎯 Focus: {', '.join(classification['categories']).replace('_', ' ').title()}")
    
    if classification['locations']:
        output.append(f"📍 Locations: {', '.join(classification['locations']).title()}")
    
    output.append("")
    
    # Executive Summary (Tavily AI Answer)
    if response.get("answer"):
        output.append("📋 EXECUTIVE SUMMARY:")
        output.append("─" * 90)
        output.append(response["answer"])
        output.append("")
    
    # Detailed Sources
    results = response.get("results", [])
    if results:
        output.append(f"📚 DETAILED SOURCES & ANALYSIS ({len(results)} sources):")
        output.append("=" * 90)
        
        for idx, result in enumerate(results, 1):
            url = result.get("url", "")
            domain = extract_domain(url)
            
            # Get source info
            source_info = get_source_info(domain)
            
            output.append(f"\n[{idx}] {result.get('title', 'Untitled')}")
            output.append(f"    🔗 Source: {url}")
            output.append(f"    {source_info['badge']} {source_info['specialty']}")
            
            # Content
            content = result.get("content", "")
            if content:
                clean_content = content.replace("\n", " ").strip()
                if len(clean_content) > 500:
                    clean_content = clean_content[:500] + "..."
                output.append(f"    📝 {clean_content}")
            
            output.append("")
    else:
        output.append("⚠️ No sources found for this query.")
        output.append("")
    
    # Footer with actionable insights
    output.append("=" * 90)
    output.append("💡 KEY RECOMMENDATIONS:")
    output.append(generate_intelligence_recommendations(classification, results))
    output.append("=" * 90)
    
    # Additional guidance
    output.append("\n🔍 For property listings, use: search_egyptian_real_estate_tavily()")
    output.append("📊 For statistical analysis, use: execute_python_query()")
    
    return "\n".join(output)


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', url)
    return match.group(1) if match else url


def get_source_info(domain: str) -> Dict[str, str]:
    """Get information about source reliability and specialty"""
    for source_domain, config in TRUSTED_INFO_SOURCES.items():
        if source_domain in domain:
            priority = config["priority"]
            if priority == "high":
                badge = "⭐⭐⭐ VERIFIED"
            elif priority == "medium":
                badge = "⭐⭐ RELIABLE"
            else:
                badge = "⭐ STANDARD"
            
            return {
                "badge": badge,
                "specialty": config["specialty"]
            }
    
    return {
        "badge": "🔍 GENERAL SOURCE",
        "specialty": "Market information"
    }


def generate_intelligence_recommendations(
    classification: Dict[str, Any], 
    results: List[Dict]
) -> str:
    """
    Generate actionable recommendations based on query type
    """
    recommendations = []
    
    if not results:
        return """
   ⚠️ Limited results found. Try:
      • Using different search terms
      • Being more specific about timeframe (e.g., "2025", "current")
      • Specifying location (e.g., "New Cairo", "6th October")
      • Breaking complex questions into simpler ones
"""
    
    # Category-specific recommendations
    if "investment_advice" in classification["categories"]:
        recommendations.append("💰 Investment: Cross-verify ROI claims with multiple sources (JLL, Mordor, Savills)")
        recommendations.append("📊 Investment: Consider economic factors (inflation, currency) from CBE reports")
    
    if "regulations_laws" in classification["categories"]:
        recommendations.append("⚖️ Legal: Always consult a licensed attorney for legal matters")
        recommendations.append("📜 Legal: Check official government websites for latest regulations")
    
    if "market_forecast" in classification["categories"]:
        recommendations.append("🔮 Forecasts: Treat predictions as estimates, not guarantees")
        recommendations.append("📈 Forecasts: Compare multiple forecasts (Mordor, IMARC, JLL) for better accuracy")
    
    if "pricing_analysis" in classification["categories"]:
        recommendations.append("💵 Pricing: Local asking prices differ from final sale prices - verify actual transactions")
    
    if "economic_factors" in classification["categories"]:
        recommendations.append("🏦 Economics: Monitor CBE announcements for interest rate and policy changes")
    
    # General recommendations
    recommendations.append("✅ Always verify information with official sources before making decisions")
    recommendations.append("🔄 Market conditions change rapidly in Egypt - check data freshness")
    
    if classification["locations"]:
        recommendations.append(f"📍 Location-specific: Visit {classification['locations'][0]} personally to verify market conditions")
    
    return "\n   ".join(recommendations)


# =============================================
# 🧪 TESTING
# =============================================

def test_intelligence_tool():
    """Test the market intelligence tool"""
    test_queries = [
        # Trends
        "What are the current trends in Egyptian real estate market?",
        
        # Investment
        "Is it a good time to invest in Egyptian real estate? ROI analysis",
        
        # Regulations
        "Can foreigners buy property in Egypt? What are the legal requirements?",
        
        # Economic
        "How does Egyptian pound devaluation affect real estate prices?",
        
        # Forecast
        "What is the forecast for Egyptian residential market in 2026?",
        
        # Policy
        "What are the government mortgage programs in Egypt?",
        
        # Rental
        "What are typical rental yields in New Cairo?",
        
        # New Cities
        "Tell me about real estate opportunities in New Administrative Capital"
    ]
    
    print("🧪 TESTING MARKET INTELLIGENCE TOOL")
    print("=" * 90)
    
    for query in test_queries:
        print(f"\n\n🔍 Query: {query}")
        print("-" * 90)
        classification = classify_info_query(query)
        print(f"Categories: {classification['categories']}")
        enhanced = build_info_search_query(query, classification)
        print(f"Enhanced: {enhanced}")
        domains = build_info_domain_filter(classification)
        print(f"Domains: {domains}")


if __name__ == "__main__":
    test_intelligence_tool()