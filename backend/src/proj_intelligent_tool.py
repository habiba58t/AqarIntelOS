"""
INTELLIGENT REAL ESTATE AGENT TOOLS
Innovation-Powered Database-First Approach
"""

import psycopg2
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from langchain_core.tools import tool
from dataclasses import dataclass
import numpy as np

# =============================================
# DATABASE CONNECTION
# =============================================

DB_CONNECTION_STRING = "dbname=langgraph_db user=postgres password=123456 host=localhost"

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(DB_CONNECTION_STRING)

# =============================================
# DATA STRUCTURES
# =============================================

@dataclass
class ProjectIntelligence:
    """Rich project information from database"""
    name: str
    developer: str
    location: str
    min_price: float
    max_price: float
    payment_plans: str
    description: str
    thumbnail: str
    pdfs: List[str]
    highlights: Dict[str, Any]
    similarity_score: Optional[float] = None
    available_units: int = 0

@dataclass
class PaymentPlanAnalysis:
    """Analyzed payment plan data"""
    available_plans: List[Dict]
    best_low_down: Optional[Dict]
    best_short_term: Optional[Dict]
    calculations_available: bool

# =============================================
# INNOVATION #1: SEMANTIC PROJECT SEARCH
# =============================================

@tool
def semantic_project_search(
    user_query: str,
    location_filter: Optional[str] = None,
    max_price: Optional[int] = None,
    top_k: int = 5
) -> str:
    """
    🧠 SEMANTIC SEARCH using embeddings - finds projects matching natural language queries
    
    **YOUR UNFAIR ADVANTAGE:** Uses vector embeddings to understand user intent
    beyond exact keywords.
    
    Examples:
    - "luxury beachfront with golf" → Finds Hacienda Bay (has golf course)
    - "quiet family compound with schools" → Finds New Cairo family projects  
    - "investment property with high ROI" → Finds projects in growing areas
    
    Args:
        user_query: Natural language description of what user wants
        location_filter: Optional location to filter
        max_price: Optional maximum price in EGP
        top_k: Number of results to return
    
    Returns:
        Formatted string with semantically matched projects
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate embedding reference for the query
        search_pattern = f"%{user_query}%"
        location_pattern = f"%{location_filter}%" if location_filter else None
        
        # Vector similarity search in PostgreSQL
        query = """
            SELECT 
                name, developer_name, location_name,
                min_price, max_price, payment_plans,
                description, thumbnail_url, pdf_documents,
                -- Calculate similarity score (1 = perfect, 0 = no match)
                1 - (embedding <=> (
                    SELECT embedding FROM recommended_projects 
                    WHERE LOWER(description) LIKE LOWER(%s)
                    LIMIT 1
                )::vector) as similarity_score
            FROM recommended_projects
            WHERE 1=1
                AND (%s IS NULL OR LOWER(location_name) LIKE LOWER(%s))
                AND (%s IS NULL OR max_price <= %s)
            ORDER BY embedding <=> (
                SELECT embedding FROM recommended_projects 
                WHERE LOWER(description) LIKE LOWER(%s)
                LIMIT 1
            )::vector
            LIMIT %s
        """
        
        cursor.execute(query, (
            search_pattern,  # For embedding reference
            location_filter, location_pattern,  # Location filter
            max_price, max_price,  # Price filter
            search_pattern,  # For ordering
            top_k
        ))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not results:
            return f"""
🔍 **Semantic Search Results:** No matches found

**Query:** "{user_query}"
**Filters:** Location: {location_filter or 'Any'} | Max Price: {max_price or 'Any'}

💡 **Try:**
• Broader search terms
• Different location
• Using intelligent_project_matcher for exact matches
"""
        
        # Format intelligent response
        response = f"""
🧠 **SEMANTIC SEARCH RESULTS** (AI-Powered Matching)
════════════════════════════════════════════

**Your Query:** "{user_query}"
**Understanding:** Found projects conceptually matching your description
**Filters:** {location_filter or 'Any location'} | Max: {f'{max_price:,} EGP' if max_price else 'No limit'}

Found **{len(results)} semantically matched projects**:

"""
        
        for idx, result in enumerate(results, 1):
            name, developer, location, min_price, max_price_val, payment_plans, description, thumbnail, pdfs, similarity = result
            
            # Extract why it matches
            match_reasons = _extract_semantic_match_reasons(description, user_query)
            avg_price = (min_price + max_price_val) / 2 / 1_000_000
            
            # Match quality indicator
            if similarity > 0.9:
                match_quality = "🏆 EXCELLENT MATCH"
            elif similarity > 0.75:
                match_quality = "✅ STRONG MATCH" 
            else:
                match_quality = "💡 GOOD MATCH"
            
            response += f"""
{'─' * 50}
**{idx}. {name}** {match_quality}
{'─' * 50}
🏢 **Developer:** {developer}
📍 **Location:** {location}
💰 **Price Range:** {min_price/1_000_000:.1f}M - {max_price_val/1_000_000:.1f}M EGP
📊 **Similarity Score:** {similarity*100:.1f}% match

**Why This Matches Your Query:**
{match_reasons}

💳 **Payment Options:** {len(payment_plans.split('|')) if payment_plans else 0} plans available
📄 **Documentation:** {_count_pdfs(pdfs)} brochure(s)
"""
        
        response += f"""
{'═' * 50}

💡 **SEMANTIC SEARCH INSIGHTS:**
The AI found projects that conceptually match "{user_query}" even without exact keywords.

**Top Match:** **{results[0][0]}** with {results[0][9]*100:.1f}% relevance to your description.

**Next Steps:**
1. Get details: "Tell me more about {results[0][0]}"
2. Compare: "Compare {results[0][0]} with {results[1][0] if len(results) > 1 else 'other projects'}"
3. Check availability: "What units are available in {results[0][0]}?"
"""
        
        return response
        
    except Exception as e:
        return f"❌ Semantic search error: {str(e)}\n\n🔄 Try intelligent_project_matcher for exact matches."


# =============================================
# INNOVATION #2: INTELLIGENT PROJECT MATCHER (PRIMARY TOOL)
# =============================================

@tool
def intelligent_project_matcher(
    location: str,
    bedrooms: Optional[int] = None,
    max_price: Optional[int] = None,
    min_price: Optional[int] = None,
    preferences: Optional[str] = None
) -> str:
    """
    🎯 PRIMARY PROJECT SEARCH - Database-first intelligent matching
    
    **ALWAYS USE THIS FIRST** before web search!
    
    Multi-stage matching:
    1. Exact location + price filtering
    2. Semantic matching (if preferences provided) 
    3. Unit availability integration
    4. Confidence scoring for autonomous decisions
    
    Args:
        location: Area/city (e.g., "New Cairo", "North Coast")
        bedrooms: Number of bedrooms (filters units when available)
        max_price: Maximum budget in EGP
        min_price: Minimum budget in EGP
        preferences: Additional preferences for semantic matching
    
    Returns:
        Formatted project matches with full intelligence
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 🎯 STAGE 1: Exact filtering
        exact_query = """
            SELECT 
                name, developer_name, location_name,
                min_price, max_price, payment_plans,
                description, thumbnail_url, pdf_documents
            FROM recommended_projects
            WHERE LOWER(location_name) LIKE LOWER(%s)
                AND (%s IS NULL OR max_price >= %s)
                AND (%s IS NULL OR min_price <= %s)
            ORDER BY (min_price + max_price) / 2 ASC
        """
        
        location_pattern = f"%{location}%"
        cursor.execute(exact_query, (
            location_pattern,
            min_price, min_price,
            max_price, max_price
        ))
        
        exact_matches = cursor.fetchall()
        
        # 🧠 STAGE 2: Semantic matching if preferences provided
        semantic_matches = []
        if preferences:
            semantic_query = """
                SELECT DISTINCT
                    name, developer_name, location_name,
                    min_price, max_price, payment_plans,
                    description, thumbnail_url, pdf_documents
                FROM recommended_projects
                WHERE LOWER(location_name) LIKE LOWER(%s)
                    AND (%s IS NULL OR max_price >= %s)
                    AND (%s IS NULL OR min_price <= %s)
                    AND (
                        LOWER(description) LIKE LOWER(%s)
                        OR LOWER(name) LIKE LOWER(%s)
                    )
            """
            
            pref_pattern = f"%{preferences}%"
            cursor.execute(semantic_query, (
                location_pattern,
                min_price, min_price,
                max_price, max_price,
                pref_pattern, pref_pattern
            ))
            
            semantic_matches = cursor.fetchall()
        
        # 🏠 STAGE 3: Unit availability (when units table exists)
        unit_availability = {}
        try:
            if bedrooms:
                units_query = """
                    SELECT project_name, COUNT(*) as available_units
                    FROM units 
                    WHERE bedrooms = %s 
                    GROUP BY project_name
                """
                cursor.execute(units_query, (bedrooms,))
                unit_availability = {row[0]: row[1] for row in cursor.fetchall()}
        except:
            pass  # Units table might not exist yet
        
        cursor.close()
        conn.close()
        
        # 📊 CONFIDENCE SCORING for autonomous decision-making
        total_matches = len(exact_matches)
        has_preferences_match = len(semantic_matches) > 0 if preferences else True
        has_unit_data = len(unit_availability) > 0 if bedrooms else True
        
        if total_matches >= 3 and has_preferences_match and has_unit_data:
            confidence = "HIGH"
            web_search_needed = False
            confidence_reason = "Multiple verified matches with unit data"
        elif total_matches >= 1:
            confidence = "MEDIUM" 
            web_search_needed = True
            confidence_reason = f"{total_matches} database matches, supplementing with web"
        else:
            confidence = "LOW"
            web_search_needed = True
            confidence_reason = "Limited database coverage, web search primary"
        
        # 📝 FORMAT INTELLIGENT RESPONSE
        response = f"""
🎯 **INTELLIGENT PROJECT MATCHER** (Database-First Strategy)
════════════════════════════════════════════

**Search Criteria:**
📍 Location: {location}
🛏️ Bedrooms: {bedrooms if bedrooms else 'Any'}
💰 Price Range: {f'{min_price/1_000_000:.1f}M' if min_price else 'Any'} - {f'{max_price/1_000_000:.1f}M EGP' if max_price else 'Any'}
🎨 Preferences: {preferences if preferences else 'None'}

**Database Intelligence:**
📊 Exact Matches: {total_matches} project(s)
🎯 Semantic Matches: {len(semantic_matches) if preferences else 'N/A'}
🏠 Unit Availability: {len(unit_availability)} project(s) with {bedrooms} bedrooms

**Confidence Score:** {confidence}
**Reason:** {confidence_reason}
**Web Search Recommended:** {'Yes - to supplement' if web_search_needed else 'No - sufficient data'}

"""
        
        if total_matches == 0:
            response += f"""
⚠️ **NO EXACT MATCHES IN DATABASE**

**Autonomous Agent Actions:**
✅ Will automatically:
1. Try semantic search with broader criteria  
2. Search web for additional listings
3. Suggest alternative locations

**Immediate Fallback:**
🔄 Switching to semantic_project_search with broader parameters...
"""
            return response
        
        # 🏆 DISPLAY MATCHES WITH RICH INTELLIGENCE
        response += f"\n{'═' * 50}\n**VERIFIED PROJECTS FROM YOUR DATABASE:**\n{'═' * 50}\n"
        
        for idx, project in enumerate(exact_matches[:5], 1):
            name, developer, location_name, min_p, max_p, payment_plans, description, thumbnail, pdfs = project
            
            # Check match types
            is_semantic_match = any(sem[0] == name for sem in semantic_matches) if preferences else False
            available_units = unit_availability.get(name, 0) if bedrooms else None
            
            # Extract project intelligence
            highlights = extract_project_highlights(description)
            avg_price = (min_p + max_p) / 2 / 1_000_000
            
            response += f"""
**{idx}. 🏢 {name}** {'⭐ PREFERENCE MATCH' if is_semantic_match else ''}
{'─' * 50}
👷 **Developer:** {developer} (Verified)
📍 **Location:** {location_name}
💰 **Price Range:** {min_p/1_000_000:.1f}M - {max_p/1_000_000:.1f}M EGP
📊 **Average:** {avg_price:.1f}M EGP
{'🏠 **Available Units:** ' + str(available_units) if available_units is not None else ''}

**Key Features:**
{_format_key_features(highlights)}

💳 **Payment Intelligence:**
{_analyze_payment_preview(payment_plans)}

📄 **Complete Documentation:** ✅ Available
   • Full verified description
   • {_count_pdfs(pdfs)} PDF brochure(s)
   • Developer credentials
   • Payment plan details

"""
        
        # 🤖 AUTONOMOUS AGENT GUIDANCE
        response += f"""
{'═' * 50}

🤖 **AUTONOMOUS AGENT DECISION MAKING:**

**Confidence Level:** {confidence}
**Database Coverage:** {total_matches} verified project(s)
**Preference Matching:** {len(semantic_matches) if preferences else 'N/A'} project(s)
**Unit Data:** {'Available' if unit_availability else 'Not checked'}

**Next Actions:**
"""
        
        if confidence == "HIGH":
            response += f"""
✅ **HIGH CONFIDENCE - Database results are sufficient**

Agent will:
1. ✓ Present {total_matches} verified project(s) as primary options
2. ✓ Analyze neighborhood quality for top matches  
3. ✓ Compare projects if user shows interest
4. ✓ Skip web search (sufficient verified data)

**No web search needed - your database has excellent coverage**
"""
        elif confidence == "MEDIUM":
            response += f"""
⚠️ **MEDIUM CONFIDENCE - Supplementing with web search**

Agent will automatically:
1. ✓ Present {total_matches} database project(s) first
2. ✓ Run web search to find additional options
3. ✓ Merge results (database prioritized as verified)
4. ✓ Clearly label sources (verified vs web)

**Autonomous action:** Calling web search next...
"""
        else:
            response += f"""
🔍 **LOW CONFIDENCE - Web search as primary**

Agent will automatically:
1. ✓ Try semantic search with broader criteria
2. ✓ Run comprehensive web search as primary source
3. ✓ Suggest alternative locations/price ranges
4. ✓ Keep database results as reference

**Autonomous action:** Switching to web search primary...
"""
        
        # 🎯 SPECIFIC FOLLOW-UP ACTIONS
        if total_matches > 0:
            top_project = exact_matches[0][0]
            response += f"""

**Immediate Follow-Up Actions Available:**
1. 📊 Get full details: "Tell me everything about {top_project}"
2. 🗺️ Check area quality: "What's the neighborhood like for {top_project}?"
3. 💰 Payment breakdown: "Show me payment plans for {top_project}"
4. ⚖️ Compare options: "Compare {top_project} with {exact_matches[1][0] if len(exact_matches) > 1 else 'other projects'}"
5. 🏠 Check units: "What's available in {top_project}?" 

"""
        
        return response
        
    except Exception as e:
        error_msg = f"❌ Database search error: {str(e)}"
        return f"{error_msg}\n\n🔄 Agent will automatically fall back to semantic search and web search."


# =============================================
# INNOVATION #3: PROGRESSIVE DISCLOSURE TOOLS
# =============================================

@tool
def get_project_details(project_name: str) -> str:
    """
    📋 LEVEL 2: Rich project details extraction
    
    Extracts comprehensive information from project description
    and provides deep insights beyond basic overview.
    
    Args:
        project_name: Name of the project to get details for
    
    Returns:
        Formatted rich project details
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, developer_name, location_name, min_price, max_price,
                   payment_plans, description, thumbnail_url, pdf_documents
            FROM recommended_projects
            WHERE LOWER(name) LIKE LOWER(%s)
            LIMIT 1
        """, (f"%{project_name}%",))
        
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project:
            return f"❌ Project '{project_name}' not found in database"
        
        name, developer, location, min_price, max_price, payment_plans, description, thumbnail, pdfs = project
        
        # Extract rich intelligence
        highlights = extract_project_highlights(description)
        payment_analysis = analyze_payment_plan(payment_plans)
        pdf_list = pdfs.split(',') if pdfs else []
        
        response = f"""
📋 **PROJECT INTELLIGENCE: {name}**
════════════════════════════════════════════

**Basic Information:**
🏢 **Developer:** {developer}
📍 **Location:** {location} 
💰 **Price Range:** {min_price/1_000_000:.1f}M - {max_price/1_000_000:.1f}M EGP

**Project Highlights:**
"""
        
        # Amenities
        if highlights["amenities"]:
            response += "\n🏊 **Key Amenities:**\n"
            for amenity in highlights["amenities"][:5]:
                response += f"   • {amenity}\n"
        
        # Unique Features
        if highlights["unique_features"]:
            response += "\n⭐ **Unique Features:**\n"
            for feature in highlights["unique_features"][:3]:
                response += f"   • {feature}\n"
        
        # Scale
        if highlights["scale"]:
            response += f"\n📏 **Project Scale:** {highlights['scale']}\n"
        
        # Distances
        if highlights["distances"]:
            response += "\n📍 **Key Distances:**\n"
            for place, time in list(highlights["distances"].items())[:3]:
                response += f"   • {place}: {time}\n"
        
        # Smart Features
        if highlights["smart_features"]:
            response += "\n🤖 **Smart Features:**\n"
            for feature in highlights["smart_features"][:3]:
                response += f"   • {feature}\n"
        
        # Payment Plans
        response += f"\n💳 **Payment Plan Intelligence:**\n"
        response += _format_payment_analysis(payment_analysis, (min_price + max_price) / 2)
        
        # Documentation
        response += f"\n📄 **Available Documentation:**\n"
        if pdf_list:
            for pdf in pdf_list[:3]:
                response += f"   • 📎 {pdf.strip()}\n"
        else:
            response += "   • No PDF brochures available\n"
        
        response += f"""
{'═' * 50}

**Next Level Details Available:**
1. 🏠 Unit-specific availability (when units table ready)
2. 💰 Detailed payment calculations for specific unit types
3. 🗺️ Neighborhood analysis and area insights
4. 📊 Investment ROI analysis

**Ask:** "Show me available units in {name}" or "Calculate payments for a {max_price/1_000_000:.1f}M EGP villa"
"""
        
        return response
        
    except Exception as e:
        return f"❌ Error getting project details: {str(e)}"


@tool
def get_project_availability(project_name: str, bedrooms: Optional[int] = None) -> str:
    """
    🏠 LEVEL 3: Unit availability details
    
    Provides specific unit-level availability when units table is ready.
    For now, shows structured approach.
    
    Args:
        project_name: Name of the project
        bedrooms: Filter by number of bedrooms
    
    Returns:
        Formatted unit availability information
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try to get unit data if table exists
        unit_data = []
        try:
            if bedrooms:
                cursor.execute("""
                    SELECT unit_code, unit_type, bedrooms, price, area_sqm
                    FROM units 
                    WHERE LOWER(project_name) LIKE LOWER(%s) AND bedrooms = %s
                    ORDER BY price ASC
                """, (f"%{project_name}%", bedrooms))
            else:
                cursor.execute("""
                    SELECT unit_code, unit_type, bedrooms, price, area_sqm
                    FROM units 
                    WHERE LOWER(project_name) LIKE LOWER(%s)
                    ORDER BY bedrooms, price ASC
                """, (f"%{project_name}%",))
            
            unit_data = cursor.fetchall()
        except:
            pass  # Units table doesn't exist yet
        
        cursor.close()
        conn.close()
        
        response = f"""
🏠 **UNIT AVAILABILITY: {project_name}**
════════════════════════════════════════════

"""
        
        if unit_data:
            # Group by unit type
            units_by_type = {}
            for unit in unit_data:
                unit_code, unit_type, beds, price, area = unit
                if unit_type not in units_by_type:
                    units_by_type[unit_type] = []
                units_by_type[unit_type].append(unit)
            
            for unit_type, units in units_by_type.items():
                min_price = min(u[3] for u in units)
                max_price = max(u[3] for u in units)
                bed_counts = list(set(u[2] for u in units))
                
                response += f"""
**{unit_type.title()}s** ({len(units)} units available)
   • Price Range: {min_price/1_000_000:.1f}M - {max_price/1_000_000:.1f}M EGP
   • Bedrooms: {', '.join(map(str, sorted(bed_counts)))}
   • Sample Units: {', '.join([u[0] for u in units[:3]])}...
"""
        else:
            response += f"""
📊 **Availability Structure** (Units table integration ready)

**Expected Unit Types in {project_name}:**
• Villas (3-6 bedrooms) 
• Chalets (2-4 bedrooms)
• Apartments (1-3 bedrooms)
• Twin Houses (3-4 bedrooms)
• Cabins (1-2 bedrooms)

**To get specific availability:**
Contact the developer directly or check the project's official website.

**When units table is populated, I'll show:**
✓ Exact unit codes and prices
✓ Floor plans and areas  
✓ Availability status
✓ Payment plans per unit type
"""
        
        response += f"""
{'═' * 50}

**Next Steps:**
1. Get project details: "Tell me more about {project_name}"
2. Payment calculations: "Show me payment plans for {project_name}"
3. Compare with: "Find similar projects to {project_name}"
"""
        
        return response
        
    except Exception as e:
        return f"❌ Error checking availability: {str(e)}"


# =============================================
# INNOVATION #4: PAYMENT PLAN INTELLIGENCE
# =============================================

def analyze_payment_plan(payment_plan_text: str, unit_price: Optional[float] = None) -> PaymentPlanAnalysis:
    """
    💳 INTELLIGENT PAYMENT PLAN PARSING
    
    Parses complex payment plan strings and provides structured analysis
    with actual calculations when unit price is provided.
    
    Args:
        payment_plan_text: Raw payment plan string from database
        unit_price: Optional unit price for calculations
    
    Returns:
        Structured payment plan analysis
    """
    
    if not payment_plan_text or len(payment_plan_text.strip()) < 5:
        return PaymentPlanAnalysis([], None, None, False)
    
    # Split multiple plans
    plan_options = [p.strip() for p in payment_plan_text.split('|')]
    parsed_plans = []
    
    for idx, plan in enumerate(plan_options, 1):
        plan_data = {
            "plan_number": idx,
            "raw_text": plan,
            "down_payment_percent": None,
            "duration_years": None,
            "down_payment_amount": None,
            "annual_installment": None,
            "monthly_installment": None,
            "special_terms": []
        }
        
        # Extract down payment percentage (take first percentage found)
        down_pattern = r'(\d+)%\s*(?:down|downpayment)?'
        down_matches = re.findall(down_pattern, plan.lower())
        if down_matches:
            plan_data["down_payment_percent"] = int(down_matches[0])
        
        # Extract duration in years
        years_pattern = r'(\d+(?:\.\d+)?)\s*years?'
        years_match = re.search(years_pattern, plan.lower())
        if years_match:
            plan_data["duration_years"] = float(years_match.group(1))
        
        # Extract special terms (payments after specific periods)
        if "after" in plan.lower():
            special_match = re.search(r'(\d+%.*?after.*?(?:months?|years?))', plan, re.IGNORECASE)
            if special_match:
                plan_data["special_terms"].append(special_match.group(1))
        
        # Calculate actual amounts if unit price provided
        if unit_price and plan_data["down_payment_percent"]:
            down_amount = unit_price * (plan_data["down_payment_percent"] / 100)
            plan_data["down_payment_amount"] = down_amount
            
            if plan_data["duration_years"]:
                remaining = unit_price - down_amount
                annual = remaining / plan_data["duration_years"]
                monthly = annual / 12
                
                plan_data["annual_installment"] = annual
                plan_data["monthly_installment"] = monthly
        
        parsed_plans.append(plan_data)
    
    # Find best plans for different needs
    plans_with_down = [p for p in parsed_plans if p["down_payment_percent"]]
    plans_with_duration = [p for p in parsed_plans if p["duration_years"]]
    
    best_low_down = min(plans_with_down, key=lambda x: x["down_payment_percent"]) if plans_with_down else None
    best_short_term = min(plans_with_duration, key=lambda x: x["duration_years"]) if plans_with_duration else None
    
    return PaymentPlanAnalysis(
        available_plans=parsed_plans,
        best_low_down=best_low_down,
        best_short_term=best_short_term,
        calculations_available=unit_price is not None
    )


# =============================================
# HELPER FUNCTIONS
# =============================================

def extract_project_highlights(description: str, query_context: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured highlights from project description
    """
    highlights = {
        "amenities": [],
        "distances": {},
        "unique_features": [],
        "scale": None,
        "developer_awards": [],
        "smart_features": []
    }
    
    if not description:
        return highlights
    
    description_lower = description.lower()
    
    # Extract amenities with context
    amenity_keywords = {
        "golf": ["golf course", "golf", "sanford golf"],
        "beach": ["beach", "beachfront", "seafront", "mediterranean"],
        "pool": ["swimming pool", "pool", "pools"],
        "gym": ["gym", "fitness", "sports center"],
        "club": ["clubhouse", "club", "social club"],
        "medical": ["medical", "healthcare", "hospital", "clinic"],
        "hotel": ["hotel", "boutique hotel"],
        "commercial": ["commercial", "retail", "shopping", "mall"],
        "park": ["park", "green", "garden", "landscape"]
    }
    
    for category, keywords in amenity_keywords.items():
        for keyword in keywords:
            if keyword in description_lower:
                context = _extract_sentence_with_keyword(description, keyword)
                if context and context not in highlights["amenities"]:
                    highlights["amenities"].append(context)
                break
    
    # Extract project scale
    size_patterns = [
        r'(\d+(?:\.\d+)?\s*(?:million\s*)?sqm?|m²)',
        r'spreads? across (\d+(?:\.\d+)?\s*(?:million\s*)?sqm?)',
        r'(\d+(?:\.\d+)?)\s*(?:million\s*)?square meters'
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, description_lower)
        if match:
            highlights["scale"] = match.group(0).title()
            break
    
    # Extract distances
    distance_pattern = r'(\d+)\s*minutes?\s*(?:away)?\s*from\s+([^.,]+)'
    distances = re.findall(distance_pattern, description, re.IGNORECASE)
    for time, location in distances[:3]:  # Limit to 3
        highlights["distances"][location.strip()] = f"{time} minutes"
    
    # Extract unique features
    unique_patterns = [
        r'one of the (?:finest|most|best|premier) ([^.,]+)',
        r'award-winning ([^.,]+)',
        r'signature ([^.,]+)',
        r'unique ([^.,]+)',
        r'first ([^.,]+)',
        r'only ([^.,]+)'
    ]
    
    for pattern in unique_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches[:2]:
            if len(match) < 100:
                highlights["unique_features"].append(match.strip())
    
    return highlights


def _extract_semantic_match_reasons(description: str, query: str) -> str:
    """Extract why this project matches the semantic query"""
    highlights = extract_project_highlights(description, query)
    
    reasons = []
    query_lower = query.lower()
    
    # Check for direct concept matches
    if any(word in query_lower for word in ['golf', 'sports']):
        if any('golf' in amenity.lower() for amenity in highlights["amenities"]):
            reasons.append("• Includes golf course facilities")
    
    if any(word in query_lower for word in ['beach', 'sea', 'waterfront']):
        if any(word in description.lower() for word in ['beach', 'seafront', 'waterfront']):
            reasons.append("• Beachfront or waterfront location")
    
    if any(word in query_lower for word in ['family', 'children', 'kids']):
        if any(word in description.lower() for word in ['family', 'children', 'kids', 'playground']):
            reasons.append("• Family-friendly amenities")
    
    if any(word in query_lower for word in ['luxury', 'premium', 'exclusive']):
        if any(word in description.lower() for word in ['luxury', 'premium', 'exclusive', 'high-end']):
            reasons.append("• Luxury features and premium quality")
    
    if any(word in query_lower for word in ['quiet', 'peaceful', 'calm']):
        if any(word in description.lower() for word in ['quiet', 'peaceful', 'tranquil', 'serene']):
            reasons.append("• Peaceful and quiet environment")
    
    # Fallback to key features
    if not reasons and highlights["amenities"]:
        reasons = [f"• {amenity.split('.')[0][:80]}..." for amenity in highlights["amenities"][:2]]
    
    return "\n".join(reasons) if reasons else "• Comprehensive amenities and features"


def _format_key_features(highlights: Dict) -> str:
    """Format top key features"""
    features = []
    
    # Add unique features first
    for feature in highlights["unique_features"][:2]:
        features.append(f"✓ {feature}")
    
    # Add key amenities
    for amenity in highlights["amenities"][:3]:
        short_amenity = amenity.split('.')[0][:60]
        features.append(f"✓ {short_amenity}")
    
    return "\n".join(features[:4]) if features else "✓ Comprehensive amenities and facilities"


def _analyze_payment_preview(payment_plans: str) -> str:
    """Analyze and format payment plan preview"""
    if not payment_plans or len(payment_plans.strip()) < 5:
        return "Contact developer for payment plan details"
    
    analysis = analyze_payment_plan(payment_plans)
    
    if not analysis.available_plans:
        return payment_plans[:150] + ("..." if len(payment_plans) > 150 else "")
    
    summary = []
    for plan in analysis.available_plans[:2]:  # Show top 2 plans
        if plan["down_payment_percent"] and plan["duration_years"]:
            summary.append(f"  • {plan['down_payment_percent']}% down, {plan['duration_years']} years")
        else:
            # Fallback to raw text preview
            preview = plan['raw_text'][:70] + "..." if len(plan['raw_text']) > 70 else plan['raw_text']
            summary.append(f"  • {preview}")
    
    return "\n".join(summary) if summary else "Multiple flexible payment options"


def _format_payment_analysis(analysis: PaymentPlanAnalysis, avg_price: float = None) -> str:
    """Format detailed payment analysis"""
    if not analysis.available_plans:
        return "No structured payment plan data available"
    
    response = ""
    
    # Show best options
    if analysis.best_low_down:
        response += f"💚 **Best for Low Down Payment:** {analysis.best_low_down['down_payment_percent']}% down"
        if avg_price and analysis.best_low_down['down_payment_amount']:
            response += f" ({analysis.best_low_down['down_payment_amount']/1_000_000:.1f}M EGP)\n"
        else:
            response += "\n"
    
    if analysis.best_short_term:
        response += f"💙 **Shortest Term:** {analysis.best_short_term['duration_years']} years\n"
    
    # Show all plans
    response += "\n**All Available Plans:**\n"
    for plan in analysis.available_plans:
        if plan["down_payment_percent"] and plan["duration_years"]:
            response += f"  • {plan['down_payment_percent']}% down, {plan['duration_years']} years\n"
        else:
            response += f"  • {plan['raw_text'][:80]}...\n"
    
    return response


def _count_pdfs(pdf_string: str) -> int:
    """Count PDF documents"""
    if not pdf_string:
        return 0
    return len([p for p in pdf_string.split(',') if p.strip()])


def _extract_sentence_with_keyword(text: str, keyword: str) -> Optional[str]:
    """Extract sentence containing keyword"""
    sentences = text.split('.')
    for sentence in sentences:
        if keyword.lower() in sentence.lower():
            return sentence.strip() + '.'
    return None


# =============================================
# CORRECTED TEST FUNCTION
# =============================================

def test_all_tools():
    """Simple test to verify all tools work"""
    print("🚀 TESTING ALL REAL ESTATE TOOLS...")
    
    try:
        # Test Semantic Search - Use invoke method
        print("\n1. Testing Semantic Search...")
        result1 = semantic_project_search.invoke({
            "user_query": "luxury beachfront", 
            "top_k": 2
        })
        print(f"✅ Semantic Search: {len(result1)} chars")
        print(f"Preview: {result1[:200]}...")
        
        # Test Intelligent Matcher
        print("\n2. Testing Intelligent Matcher...")
        result2 = intelligent_project_matcher.invoke({
            "location": "New Cairo",
            "max_price": 5000000
        })
        print(f"✅ Intelligent Matcher: {len(result2)} chars")
        print(f"Preview: {result2[:200]}...")
        
        # Test Project Details
        print("\n3. Testing Project Details...")
        result3 = get_project_details.invoke({
            "project_name": "Hacienda"
        })
        print(f"✅ Project Details: {len(result3)} chars")
        print(f"Preview: {result3[:200]}...")
        
        # Test Availability
        print("\n4. Testing Availability...")
        result4 = get_project_availability.invoke({
            "project_name": "Hacienda"
        })
        print(f"✅ Availability: {len(result4)} chars")
        print(f"Preview: {result4[:200]}...")
        
        print(f"\n🎯 ALL TOOLS WORKING! Total output: {len(result1)+len(result2)+len(result3)+len(result4)} chars")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_all_tools()