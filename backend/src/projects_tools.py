
"""
Dynamic Project Information Tools for Real Estate Agent
Provides intelligent project data retrieval and comparison
"""

import psycopg2  # ✅ Use psycopg2, not psycopg
from typing import Dict, List, Optional, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# =============================================
# Database Connection Configuration
# =============================================
DB_CONNECTION_STRING = "dbname=langgraph_db user=postgres password=123456 host=localhost"

def get_db_connection():
    """Create database connection using psycopg2"""
    return psycopg2.connect(DB_CONNECTION_STRING)

# =============================================
# TOOL 1: Smart Project Information Retrieval
# =============================================

class ProjectInfoInput(BaseModel):
    """Input schema for project information requests"""
    project_name: str = Field(
        description="Name of the project (can be partial match, e.g., 'Palm' will match 'Palm Hills')"
    )
    info_type: Literal[
        "overview", "payment_plans", "prices", "location", 
        "details", "all", "documents"
    ] = Field(
        default="overview",
        description="""
        Type of information requested:
        - 'overview': Basic project info (name, developer, location, price range)
        - 'payment_plans': Detailed payment plan explanation
        - 'prices': Price range and affordability analysis
        - 'location': Location details and area information
        - 'details': Full project description
        - 'documents': PDF brochures and documentation links
        - 'all': Complete project information
        """
    )




@tool(args_schema=ProjectInfoInput)
def get_project_info_tool(project_name: str, info_type: str = "overview") -> str:
    """
    Get detailed project information in a user-friendly format.
    
    Use when users ask:
    - "Tell me about [project]" → overview
    - "Payment plans for [project]" → payment_plans
    - "How much is [project]?" → prices
    - "Full details on [project]" → details or all
    - "Everything about [project]" → all
    """
    
    try:
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
    SELECT
        name, developer_name, location_name,
        min_price, max_price, payment_plans,
        description, thumbnail_url, pdf_documents
    FROM recommended_projects
    WHERE similarity(name, %s) > 0.5
    ORDER BY similarity(name, %s) DESC
    LIMIT 1;
"""
        
        # FIXED: Consistent parameter passing - use the same format for both placeholders
        print(f"🔍 Query: {query}")
        print(f"🔍 Parameters: {(project_name, project_name)}")
        cursor.execute(query, (project_name, project_name))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        
        if not results:
            print(f"📌 Using ILIKE fallback for: {project_name}")
            query_like = """
                SELECT 
                    name, developer_name, location_name, 
                    min_price, max_price, payment_plans,
                    description, thumbnail_url, pdf_documents
                FROM recommended_projects
                WHERE LOWER(name) LIKE LOWER(%s)
                ORDER BY 
                    CASE 
                        WHEN LOWER(name) = LOWER(%s) THEN 1
                        WHEN LOWER(name) LIKE LOWER(%s) THEN 2
                        ELSE 3
                    END
                LIMIT 1
            """
            
            # ✅ CRITICAL: 3 parameters for 3 placeholders!
            search_pattern = f"%{project_name}%"
            starts_with_pattern = f"{project_name}%"
            
            print(f"🔍 ILIKE Query parameters:")
            print(f"   1. Pattern: {search_pattern}")
            print(f"   2. Exact: {project_name}")
            print(f"   3. Starts: {starts_with_pattern}")
            
            cursor.execute(query_like, (search_pattern, project_name, starts_with_pattern))
            results = cursor.fetchall()
            
            if results:
                print(f"✅ Found {len(results)} results using ILIKE")
        
        cursor.close()
        conn.close()
        
        
        # Multiple matches - let user choose
        if len(results) > 1:
            response = f"I found {len(results)} projects matching '{project_name}':\n\n"
            for result in results:
                # SAFE UNPACKING for multiple results
                name = result[0] if len(result) > 0 else "Unknown Project"
                dev = result[1] if len(result) > 1 else "Unknown Developer"
                loc = result[2] if len(result) > 2 else "Unknown Location"
                min_p = result[3] if len(result) > 3 else None
                max_p = result[4] if len(result) > 4 else None
                
                price = f"{min_p/1_000_000:.1f}M - {max_p/1_000_000:.1f}M EGP" if min_p and max_p else "Price on request"
                response += f"• **{name}** by {dev} in {loc} ({price})\n"
            response += f"\nWhich one would you like to know more about?"
            return response
        
        
        # Single match - SAFE UNPACKING with error handling
        result = results[0]
        
        # Safe extraction with defaults to handle NULL values and missing columns
        name = result[0] if len(result) > 0 and result[0] is not None else "Not available"
        developer = result[1] if len(result) > 1 and result[1] is not None else "Not available"
        location = result[2] if len(result) > 2 and result[2] is not None else "Not available"
        min_price = result[3] if len(result) > 3 else None
        max_price = result[4] if len(result) > 4 else None
        payment_plans = result[5] if len(result) > 5 and result[5] is not None else "Contact sales for payment plans"
        description = result[6] if len(result) > 6 and result[6] is not None else "No description available"
        thumbnail = result[7] if len(result) > 7 and result[7] is not None else ""
        pdfs = result[8] if len(result) > 8 and result[8] is not None else ""
        
        # ============================================
        # BUILD RESPONSE BASED ON INFO_TYPE
        # ============================================
        
        response = f"# 🏗️ {name}\n\n"
        response += f"**Developer:** {developer}\n"
        response += f"**Location:** {location}\n"
        
        # Add price summary upfront if available
        if min_price and max_price:
            response += f"**Price Range:** {min_price/1_000_000:.1f}M - {max_price/1_000_000:.1f}M EGP\n"
        
        response += "\n---\n\n"
        
        # ============================================
        # OVERVIEW - Quick Summary
        # ============================================
        if info_type == "overview":
            if description and len(description.strip()) > 20:
                clean_desc = description[:300]
                if len(description) > 300:
                    clean_desc = clean_desc.rsplit('.', 1)[0] + '.'
                response += f"## 📋 Overview\n\n{clean_desc}\n\n"
            
            if min_price and max_price:
                avg = (min_price + max_price) / 2
                if avg < 3_000_000:
                    category = "💚 **Entry-Level** - Great for first-time buyers"
                elif avg < 6_000_000:
                    category = "💙 **Mid-Market** - Balanced pricing and amenities"
                else:
                    category = "⭐ **Premium** - Luxury project"
                response += f"{category}\n\n"
            
            # Quick links
            if thumbnail:
                response += f"🖼️ [View Photos]({thumbnail})\n"
            if pdfs:
                response += f"📄 [Download Brochure]({pdfs.split(',')[0].strip()})\n"
            
            response += f"\n💡 Want full details? Ask me about payment plans, pricing, or request complete information!"
        
        # ============================================
        # PAYMENT PLANS - Show Actual Plans
        # ============================================
        elif info_type == "payment_plans":
            response += "## 💳 Payment Plans\n\n"
            
            if payment_plans and len(payment_plans.strip()) > 10:
                clean_plans = payment_plans.strip()
                
                if any(word in clean_plans.lower() for word in ['%', 'down payment', 'years', 'installment', 'deposit']):
                    response += f"{clean_plans}\n\n"
                    response += "### ✨ Benefits of These Plans:\n"
                    response += "• Flexible payment schedules to match your budget\n"
                    response += "• Reduced upfront costs make entry easier\n"
                    response += "• Extended payment periods improve cash flow\n"
                else:
                    response += f"**{name}** offers customized payment plans based on unit type and timing.\n\n"
                    response += "📞 **To get specific payment options:**\n"
                    response += "• Contact the sales team for current down payment rates\n"
                    response += "• Ask about available installment periods\n"
                    response += "• Inquire about any special promotions\n"
            else:
                response += f"Payment plan details for **{name}** are available through the sales team.\n\n"
                response += "📞 **How to proceed:**\n"
                response += "• Call the developer's sales hotline\n"
                response += "• Visit the project's sales center\n"
                response += "• Schedule a consultation for personalized plans\n"
        
        # ============================================
        # PRICES - Detailed Analysis
        # ============================================
        elif info_type == "prices":
            response += "## 💰 Detailed Pricing\n\n"
            
            if min_price and max_price:
                avg = (min_price + max_price) / 2
                
                response += f"**Minimum Price:** {min_price/1_000_000:.2f}M EGP\n"
                response += f"**Maximum Price:** {max_price/1_000_000:.2f}M EGP\n"
                response += f"**Average Price:** {avg/1_000_000:.2f}M EGP\n\n"
                
                # Categorization
                if avg < 2_500_000:
                    response += "💚 **Market Position: Entry-Level**\n"
                    response += "Perfect for first-time buyers and investors seeking rental income.\n\n"
                elif avg < 4_000_000:
                    response += "💙 **Market Position: Mid-Range**\n"
                    response += "Balanced pricing with good amenities and location value.\n\n"
                elif avg < 7_000_000:
                    response += "💜 **Market Position: Upper Mid-Range**\n"
                    response += "Quality finishes with premium features and facilities.\n\n"
                else:
                    response += "⭐ **Market Position: Luxury**\n"
                    response += "High-end project with exclusive amenities and prime location.\n\n"
                
                # Down payment estimate
                if payment_plans and '10%' in payment_plans.lower():
                    down_payment = avg * 0.10
                    response += f"### 💡 Payment Estimate\n"
                    response += f"With a 10% down payment: ~{down_payment/1_000_000:.2f}M EGP upfront\n"
                    response += f"Remaining: ~{(avg - down_payment)/1_000_000:.2f}M EGP in installments\n"
            else:
                response += "Pricing details are available through the sales team.\n"
        
        # ============================================
        # DETAILS or ALL - COMPLETE INFORMATION
        # ============================================
        elif info_type in ["details", "all"]:
            # DESCRIPTION
            if description and len(description.strip()) > 20:
                response += "## 📝 Project Description\n\n"
                response += f"{description}\n\n"
                response += "---\n\n"
            
            # PRICING
            if min_price and max_price:
                response += "## 💰 Pricing Information\n\n"
                avg = (min_price + max_price) / 2
                
                response += f"**Price Range:** {min_price/1_000_000:.2f}M - {max_price/1_000_000:.2f}M EGP\n"
                response += f"**Average Price:** {avg/1_000_000:.2f}M EGP\n\n"
                
                if avg < 2_500_000:
                    response += "💚 **Entry-Level Pricing** - Ideal for first-time buyers\n\n"
                elif avg < 4_000_000:
                    response += "💙 **Mid-Market** - Great value for money\n\n"
                elif avg < 7_000_000:
                    response += "💜 **Upper Mid-Range** - Premium features\n\n"
                else:
                    response += "⭐ **Luxury Segment** - Exclusive living\n\n"
                
                response += "---\n\n"
            
            # PAYMENT PLANS
            response += "## 💳 Payment Plans\n\n"
            if payment_plans and len(payment_plans.strip()) > 10:
                clean_plans = payment_plans.strip()
                
                if any(word in clean_plans.lower() for word in ['%', 'down', 'years', 'installment']):
                    response += f"{clean_plans}\n\n"
                    
                    # Add down payment calculation if possible
                    if min_price and max_price:
                        avg = (min_price + max_price) / 2
                        if '10%' in clean_plans:
                            down = float(avg) * 0.10
                            response += f"**Example:** For an average unit (~{avg/1_000_000:.1f}M EGP):\n"
                            response += f"• 10% Down Payment: ~{down/1_000_000:.2f}M EGP\n"
                            response += f"• Remaining: ~{(avg-down)/1_000_000:.2f}M EGP in installments\n\n"
                else:
                    response += f"Flexible payment plans are available. Contact the sales team for:\n"
                    response += "• Current down payment percentages\n"
                    response += "• Installment period options\n"
                    response += "• Special financing offers\n\n"
            else:
                response += "Payment plans are customized based on unit selection. Contact sales for details.\n\n"
            
            response += "---\n\n"
            
            # LOCATION
            response += "## 📍 Location\n\n"
            response += f"**{name}** is located in **{location}**, "
            
            location_context = {
                "New Cairo": "one of Cairo's most prestigious areas with modern infrastructure and top universities.",
                "new cairo": "one of Cairo's most prestigious areas with modern infrastructure and top universities.",
                "6th of October": "a rapidly growing city west of Cairo, known for spacious developments.",
                "Sheikh Zayed": "an upscale area with luxury compounds and Mall of Arabia nearby.",
                "North Coast": "Egypt's premier Mediterranean summer destination.",
                "New Capital": "the new administrative capital with cutting-edge infrastructure."
            }
            
            response += location_context.get(location, "a well-established residential area with good accessibility.")
            response += "\n\n---\n\n"
            
            # RESOURCES
            response += "## 📥 Downloads & Media\n\n"
            
            if thumbnail:
                response += f"🖼️ **[View Project Photos & Gallery]({thumbnail})**\n\n"
            
            if pdfs:
                response += "📄 **Download Brochures:**\n"
                pdf_list = pdfs.split(',') if ',' in pdfs else [pdfs]
                for i, pdf in enumerate(pdf_list[:3], 1):
                    response += f"   {i}. [Download PDF Brochure {i}]({pdf.strip()})\n"
                response += "\n"
            
            response += "---\n\n"
            response += "### 💬 Need More Information?\n"
            response += "Feel free to ask me about:\n"
            response += "• Nearby amenities and facilities\n"
            response += "• Comparing this project with others\n"
            response += "• Getting directions via Google Maps\n"
            response += "• Finding similar projects in the area\n"
        
        return response
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"🚨 FULL ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return f"❌ Oops! Something went wrong: {str(e)}\n\nPlease try again or ask about a different project."


# =============================================
# TOOL 2: Intelligent Project Comparison
# =============================================

class CompareProjectsInput(BaseModel):
    """Input schema for project comparison"""
    project_names: List[str] = Field(
        description="List of 2-4 project names to compare (e.g., ['Palm Hills', 'Madinaty'])"
    )
    comparison_focus: Literal[
        "prices", "payment_plans", "location", "overall"
    ] = Field(
        default="overall",
        description="""
        Focus area for comparison:
        - 'prices': Compare price ranges and affordability
        - 'payment_plans': Compare payment options
        - 'location': Compare locations and accessibility
        - 'overall': Comprehensive comparison with recommendation
        """
    )
    user_budget: Optional[int] = Field(
        default=None,
        description="User's budget in EGP (optional, helps with recommendations)"
    )

@tool(args_schema=CompareProjectsInput)
def compare_projects_tool(
    project_names: List[str], 
    comparison_focus: str = "overall",
    user_budget: Optional[int] = None
) -> str:
    """
    🔄 Intelligent project comparison and recommendation tool.
    
    Compares multiple projects and provides smart recommendations based on:
    - Price ranges and affordability
    - Payment plan flexibility
    - Location advantages
    - Overall value proposition
    
    Use this tool when users ask to:
    - Compare projects ("compare Palm Hills vs Madinaty")
    - Find alternatives ("what's similar to Hyde Park?")
    - Get recommendations ("which is better for 5M budget?")
    - Evaluate options ("help me choose between X and Y")
    
    Examples:
    - "Compare Palm Hills and Madinaty" → comparison_focus="overall"
    - "Which has better payment plans: X or Y?" → comparison_focus="payment_plans"
    - "Best project for 5M budget?" → user_budget=5000000
    """
    
    if len(project_names) < 2:
        return "❌ Please provide at least 2 projects to compare."
    
    if len(project_names) > 4:
        return "⚠️ Please limit comparison to maximum 4 projects for clarity."
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Database connection established for compare_projects_tool")
        
        # Fetch all matching projects
        projects_data = []
        for proj_name in project_names:
            compare_query = """
                SELECT 
                    name, developer_name, location_name,
                    min_price, max_price, payment_plans,
                    description
                FROM recommended_projects
                WHERE LOWER(name) LIKE LOWER(%s)
                LIMIT 1
            """
            cursor.execute(compare_query, (f"%{proj_name}%",))
            result = cursor.fetchone()
            
            if result:
                projects_data.append({
                    'name': result[0],
                    'developer': result[1],
                    'location': result[2],
                    'min_price': result[3],
                    'max_price': result[4],
                    'payment_plans': result[5],
                    'description': result[6]
                })
            else:
                projects_data.append({'name': proj_name, 'found': False})
        
        cursor.close()
        conn.close()
        
        # Check for missing projects
        missing = [p['name'] for p in projects_data if not p.get('found', True)]
        if missing:
            return f"❌ Could not find these projects: {', '.join(missing)}\n\nPlease check the names and try again."
        
        # Build comparison response
        response = f"# 🔄 Project Comparison\n\n"
        response += f"Comparing **{len(projects_data)}** projects:\n"
        for p in projects_data:
            response += f"   • {p['name']} ({p['location']})\n"
        response += "\n---\n\n"
        
        # Price comparison
        if comparison_focus in ["prices", "overall"]:
            response += "## 💰 Price Comparison\n\n"
            response += compare_prices(projects_data, user_budget)
            response += "\n\n"
        
        # Payment plans comparison
        if comparison_focus in ["payment_plans", "overall"]:
            response += "## 💳 Payment Plans Comparison\n\n"
            response += compare_payment_plans(projects_data)
            response += "\n\n"
        
        # Location comparison
        if comparison_focus in ["location", "overall"]:
            response += "## 📍 Location Comparison\n\n"
            response += compare_locations(projects_data)
            response += "\n\n"
        
        # Smart recommendation
        if comparison_focus == "overall":
            response += "## 🎯 Our Recommendation\n\n"
            response += generate_recommendation(projects_data, user_budget)
            response += "\n\n"
        
        response += "---\n"
        response += "💡 **Want more details?** Ask me about any specific project or aspect!"
        
        return response
        
    except Exception as e:
        error_msg = f"❌ Error comparing projects: {str(e)}\n\nPlease try again."
        print(error_msg)
        return error_msg


# =============================================
# Helper Functions for Formatting
# =============================================

def format_price_range(min_price: float, max_price: float) -> str:
    """Format price range in millions with EGP currency"""
    min_m = min_price / 1_000_000
    max_m = max_price / 1_000_000
    return f"{min_m:.1f}M - {max_m:.1f}M EGP"

def format_price_analysis(min_price: float, max_price: float, project_name: str) -> str:
    """Provide contextual price analysis"""
    avg_price = (min_price + max_price) / 2
    avg_m = avg_price / 1_000_000
    
    analysis = f"Units in **{project_name}** range from **{format_price_range(min_price, max_price)}**.\n\n"
    
    if avg_m < 3:
        analysis += "✅ **Affordable Range** - Great option for first-time buyers or investors.\n"
    elif avg_m < 6:
        analysis += "💼 **Mid-Range** - Balanced pricing with good value for money.\n"
    else:
        analysis += "⭐ **Premium Range** - Luxury project with high-end amenities.\n"
    
    return analysis

def format_payment_plans(payment_plans: str, project_name: str) -> str:
    """Format and explain payment plans"""
    if not payment_plans:
        return "Payment details not available."
    
    formatted = f"**{project_name}** offers flexible payment options:\n\n"
    formatted += f"{payment_plans}\n\n"
    formatted += "💡 **Key Benefits:**\n"
    formatted += "   • Extended payment periods reduce monthly burden\n"
    formatted += "   • Lower down payment makes entry more accessible\n"
    formatted += "   • Installment plans help with financial planning\n"
    
    return formatted

def format_description(description: str) -> str:
    """Format project description for readability"""
    if len(description) > 500:
        return description[:500] + "...\n\n*(Full description available in project documents)*"
    return description

def format_documents(pdfs: str, project_name: str) -> str:
    """Format document links"""
    docs = f"📥 **Download brochures and detailed information for {project_name}:**\n\n"
    
    if isinstance(pdfs, str):
        # Assuming pdfs might be JSON array or comma-separated
        doc_list = pdfs.split(',') if ',' in pdfs else [pdfs]
        for i, doc in enumerate(doc_list[:3], 1):  # Limit to 3 docs
            docs += f"   {i}. [Download PDF {i}]({doc.strip()})\n"
    
    return docs

def get_location_context(location: str) -> str:
    """Provide location context"""
    location_info = {
        "New Cairo": "one of Cairo's most prestigious areas with excellent infrastructure and connectivity.",
        "6th of October": "a rapidly developing city west of Cairo, known for its spacious compounds and modern facilities.",
        "Sheikh Zayed": "an upscale area adjacent to 6th of October, featuring luxury developments and proximity to Mall of Arabia.",
        "North Coast": "Egypt's premier summer destination along the Mediterranean, perfect for vacation homes.",
        "New Capital": "Egypt's new administrative capital, offering cutting-edge smart city infrastructure."
    }
    
    return location_info.get(location, f"a well-established area with good accessibility.")

def compare_prices(projects: List[Dict], user_budget: Optional[int]) -> str:
    """Compare prices across projects"""
    comparison = "| Project | Price Range | Avg Price | Budget Fit |\n"
    comparison += "|---------|-------------|-----------|------------|\n"
    
    for p in projects:
        if p.get('min_price') and p.get('max_price'):
            avg = (p['min_price'] + p['max_price']) / 2
            price_range = format_price_range(p['min_price'], p['max_price'])
            avg_str = f"{avg/1_000_000:.1f}M EGP"
            
            budget_fit = "N/A"
            if user_budget:
                if p['min_price'] <= user_budget <= p['max_price']:
                    budget_fit = "✅ Perfect"
                elif user_budget >= p['max_price']:
                    budget_fit = "💰 Above"
                elif user_budget < p['min_price']:
                    budget_fit = "⚠️ Below"
            
            comparison += f"| {p['name']} | {price_range} | {avg_str} | {budget_fit} |\n"
    
    if user_budget:
        comparison += f"\n*Based on your budget of {user_budget/1_000_000:.1f}M EGP*"
    
    return comparison

def compare_payment_plans(projects: List[Dict]) -> str:
    """Compare payment plan flexibility"""
    comparison = ""
    
    for p in projects:
        comparison += f"**{p['name']}:**\n"
        if p.get('payment_plans'):
            comparison += f"   {p['payment_plans'][:200]}...\n\n"
        else:
            comparison += "   Payment details available upon request.\n\n"
    
    return comparison

def compare_locations(projects: List[Dict]) -> str:
    """Compare project locations"""
    comparison = ""
    
    locations = list(set([p['location'] for p in projects]))
    
    for loc in locations:
        projects_in_loc = [p['name'] for p in projects if p['location'] == loc]
        comparison += f"**{loc}:** {', '.join(projects_in_loc)}\n"
        comparison += f"   {get_location_context(loc)}\n\n"
    
    return comparison

def generate_recommendation(projects: List[Dict], user_budget: Optional[int]) -> str:
    """Generate smart recommendation based on comparison"""
    
    if user_budget:
        # Find best match for budget
        best_match = None
        for p in projects:
            if p.get('min_price') and p.get('max_price'):
                if p['min_price'] <= user_budget <= p['max_price']:
                    best_match = p
                    break
        
        if best_match:
            return f"🎯 For your budget of **{user_budget/1_000_000:.1f}M EGP**, we recommend **{best_match['name']}** in {best_match['location']}. It offers the best value within your range with flexible payment options."
    
    # General recommendation based on average price
    avg_prices = [(p['name'], (p['min_price'] + p['max_price']) / 2) 
                  for p in projects if p.get('min_price')]
    
    if avg_prices:
        avg_prices.sort(key=lambda x: x[1])
        affordable = avg_prices[0]
        premium = avg_prices[-1]
        
        return f"💡 **{affordable[0]}** offers the most affordable entry point at {affordable[1]/1_000_000:.1f}M EGP average, while **{premium[0]}** is positioned as the premium option at {premium[1]/1_000_000:.1f}M EGP average. Choose based on your budget and desired amenities!"
    
    return "All projects offer unique advantages. Consider visiting the sales centers for detailed tours and personalized recommendations."