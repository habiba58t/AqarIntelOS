


import pandas as pd
import operator
from typing import Dict, Union, Any, Annotated, Sequence, TypedDict, Literal, Optional, List
from langchain_core.runnables.config import RunnableConfig

import re
from typing import Literal
from groq import APIError

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from langchain.tools import StructuredTool
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool
#from pydantic import BaseModel

from langgraph.graph import StateGraph, START, END

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from src.config import  api_key, OPENAI_API_KEY

from langchain_core.messages import SystemMessage
#from src.visuals import units_visual_tool_struct
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
from psycopg_pool import AsyncConnectionPool
import uuid,json
import psycopg
from psycopg_pool import ConnectionPool
#from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import os
import asyncio
from src.tools import find_properties_tool, google_maps_link_tool, nearby_places_tool
from src.projects_tools import get_project_info_tool,  compare_projects_tool
from src.python_code_tool import execute_python_query 
from src.search_tool import search_egyptian_real_estate_tavily
from src.market_info_tool import search_market_intelligence
from src.map_tool import analyze_egyptian_neighborhood_advanced
from src.proj_intelligent_tool import get_project_details, semantic_project_search,intelligent_project_matcher, get_project_availability
#from src.user_profile import load_user_profile_by_email,save_user_profile_by_email
# Initialize your datasets (replace with your actual data loading)
projects_df = pd.read_csv("data/projects_cleaned.csv")
units_df = pd.read_csv("data/units_cleaned.csv")

class UserInfo(TypedDict, total=False):
    email: str
    name: str
    preferredLocations: list[str]  
    averageBudget: int
    family_size: int
    is_investor: bool
    


# Define the agent state
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    saved_plots: Annotated[list, operator.add]
    next: str
    user: Optional[UserInfo]
    plan: str  
    completed_steps: Annotated[list, operator.add]  
    current_goal: str 

initial_state = {
    "saved_plots": [],
    "user": None,
    "plan": "",
    "completed_steps": [],
    "current_goal": "" #  initialize this once
}

# Initialize memory store
memory_store = InMemoryStore(
    index={
        "dims": 1536,  # OpenAI embedding dimensions
        "embed": "openai:text-embedding-3-small",
    }
)

# Create memory tools


manage_memeory=create_manage_memory_tool(namespace=("real_estate_assistant", "{user_email}", "memories"))
search_memory=create_search_memory_tool(namespace=("real_estate_assistant", "{user_email}", "memories"))


    
 
# Initialize the LLM with tools
llm = ChatOpenAI(model_name="gpt-4o", temperature=0.3, api_key=OPENAI_API_KEY, max_retries=2)
#llm = ChatGroq(model_name="llama-3.1-8b-instant",temperature=0,api_key=api_key)
#llm = ChatGroq(model_name="llama-3.3-70b-versatile",temperature=0,api_key=api_key)
#  VERIFY
print("=" * 50)
print(f" CONFIRMED ACTIVE MODEL: {llm.model_name}")
print("=" * 50)
tools = [execute_python_query,find_properties_tool, google_maps_link_tool, nearby_places_tool,get_project_details,semantic_project_search,intelligent_project_matcher,
         compare_projects_tool,search_egyptian_real_estate_tavily,search_market_intelligence,analyze_egyptian_neighborhood_advanced,get_project_availability,manage_memeory,search_memory] 
llm_with_tools = llm.bind_tools(tools)





def planning_node(state: AgentState) -> dict:
    """
    Creates a multi-step plan instead of single-intent routing
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": []}
    
    last_human_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_msg = msg.content
            break
    
    if not last_human_msg:
        return {"messages": []}
    
    user_info = state.get("user", {})
    user_email = user_info.get("email")

    
    # Create a planning prompt

    memory_instructions = f"""
 **MEMORY TOOLS**:
- ALWAYS pass user_email: "{user_email}" when calling memory tools
- Use search_memory to find user preferences  
- Use manage_memory to save user preferences

**Examples**:
- User says "I prefer quiet areas" → manage_memory (user_email="{user_email}", action="save", content="User prefers quiet neighborhoods")
- Before property search → search_memory(user_email="{user_email}", query="user preferences quiet budget location")
"""
    planning_prompt = f"""Analyze this real estate query and create a simple plan.

    

USER: "{last_human_msg}"
 USER CONTEXT:
- Budget: {user_info.get('averageBudget', 'N/A')} EGP
- Preferred Locations: {', '.join(user_info.get('preferredLocations', [])) or 'N/A'}
- Family Size: {user_info.get('family_size', 'N/A')}

## SMART TOOL MATCHING:

###  USER ASKS ABOUT PROPERTIES TO BUY/RENT
Use ALL three (combo approach):
1. **intelligent_project_matcher** - Find matching projects by budget/location
2. **semantic_project_search** - If user mentions specific features ("quiet", "modern", "family-friendly")
3. **search_egyptian_real_estate_tavily** - Get online listings with real sources
 Return: Projects + online options + sources

###  USER ASKS ABOUT AREA/NEIGHBORHOOD QUALITY
Use **analyze_egyptian_neighborhood_advanced** ONLY
 When they ask: "Is it quiet?", "Good for families?", "Schools nearby?", "Tell me about [Area]"

###  USER ASKS ABOUT MARKET/TRENDS/INVESTMENT
Use **search_market_intelligence** 
USE WHEN USER ASKS ABOUT*:
   Market Trends: "What are current real estate trends in Egypt?"
   Investment Advice: "Is it a good time to invest?", "Best ROI areas?"
   Price Trends: "Are prices going up or down?", "Price appreciation rates?"
   Laws/Regulations: "Can foreigners buy?", "What are ownership laws?", "Property taxes?"
   Economic Factors: "How does inflation affect prices?", "Currency impact?"
   Market Forecasts: "What's the outlook for 2026?", "Future predictions?"
   Government Policies: "Mortgage programs?", "Government initiatives?"
   Rental Market: "Typical rental yields?", "Tenant demand?"
   Developer Activity: "Top developers?", "New project pipelines?"
   Market Analysis: "Market size?", "Growth rate?", "Market health?"
   Location Analysis: "Tell me about New Administrative Capital as investment"
   General Advice: "Should I invest now or wait?", "Risks in Egyptian market?"
    *CRITICAL RULES*:
- DO NOT use this for finding specific properties
- Use for questions, analysis, advice, information
- Great for "why", "how", "should I", "what about" questions


### USER ASKS ABOUT SPECIFIC PROJECT
Use **get_project_details** for info
Use **get_project_availability** to check units
 When they ask: "Tell me about [Project Name]", "What units are available?"

###  USER WANTS PROXIMITY/NEARBY PLACES
Use **find_properties_tool** - Search near locations (work, school)
Use **nearby_places_tool** - Show amenities near a property
 When they ask: "Near my office?", "What's around [Project]?", "Schools nearby?"

###  USER NEEDS ANALYSIS/STATISTICS
Use **execute_python_query** with smart functions
 When they ask: "Compare prices", "Budget breakdown", "Stats by area"

---

## DECISION RULES (Pick 1-3 tools):

**Property Search** → intelligent_project_matcher + semantic_project_search + search_egyptian_real_estate_tavily
**Area Info** → analyze_egyptian_neighborhood_advanced (+ nearby_places_tool if asking about amenities)
**Market Info** → search_market_intelligence (include sources)
**Specific Project** → get_project_details + get_project_availability
**Proximity** → find_properties_tool + nearby_places_tool
**Stats/Analysis** → execute_python_query

---

## PLAN FORMAT:
1. [Tool Name] - Why we need it
2. [Tool Name] - Why we need it (optional)
3. [Tool Name] - Why we need it (optional)

Keep it short. 1 tool for simple questions, max 3 for complex ones.
Always mention sources when using search_market_intelligence"""
    
    # Get planning from LLM
    planning_msg = llm.invoke([
        SystemMessage(content="You are a real estate planning expert. Create concise step-by-step plans."),
        HumanMessage(content=planning_prompt)
    ])
    
    # Add plan to state
    plan_content = f"""
 **EXECUTION PLAN**:
{planning_msg.content}

I'll now execute this plan step by step...
"""
    
    return {"messages": [SystemMessage(content=plan_content)], "plan": planning_msg.content}


def clean_messages_for_token_limit(messages, max_messages=4):
    """Keep only essential messages to stay under token limit"""
    if len(messages) <= max_messages:
        return messages
    
    print(f"🧹 Cleaning messages: {len(messages)} → {max_messages}")
    
    # Strategy: Keep system + last user + last assistant + last tool result
    cleaned = []
    
    # 1. Keep system message (if exists)
    system_msgs = [msg for msg in messages if msg.type == "system"]
    if system_msgs:
        cleaned.append(system_msgs[0])
    
    # 2. Keep last user message
    user_msgs = [msg for msg in messages if msg.type == "human"]
    if user_msgs:
        cleaned.append(user_msgs[-1])
    
    # 3. Keep last assistant message
    ai_msgs = [msg for msg in messages if msg.type == "ai"]
    if ai_msgs:
        cleaned.append(ai_msgs[-1])
    
    # 4. Keep only the most recent tool message
    tool_msgs = []
    for msg in messages:
        if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs.get('tool_calls'):
            tool_msgs.append(msg)
        elif hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_msgs.append(msg)
    
    if tool_msgs:
        cleaned.append(tool_msgs[-1])  # Only keep most recent tool call
    
    return cleaned

def reasoning_agent_node(state: AgentState) -> AgentState:
    """
    Enhanced agent that reasons about which tools to call based on the plan
    """
    messages = state.get("messages", [])
    #messages = clean_messages_for_token_limit(state["messages"], max_messages=4)
    user_info = state.get("user", {})
    plan = state.get("plan", "")
    user_email = user_info['email']

    
    personal_context = f"""
 ACTIVE USER: **{user_info.get('name', 'User')}**

 USER PROFILE:
- Locations: {', '.join(user_info.get('preferredLocations', [])) or ' Not set'}
- Budget: {user_info.get('averageBudget', ' Not set')} EGP
- Family: {user_info.get('family_size', ' Unknown')} members
- Type: {' Investor' if user_info.get('is_investor') else ' Residence'}




 **When recommending properties, ALWAYS consider proximity to frequent places!**
"""

    
    memory_instructions = f"""
 **MEMORY TOOLS**:
- ALWAYS pass user_email: "{user_email}" when calling memory tools
- Use search_memory to find user preferences  
- Use manage_memory to save user preferences

**Examples**:
- User says "I prefer quiet areas" → manage_memory(user_email="{user_email}", action="create", content="User prefers quiet neighborhoods")
- Before property search → search_memory(user_email="{user_email}", query="user preferences quiet budget location")
"""
    
    system_context = f"""You are a smart real estate AI assistant. Think before you act.
    

{personal_context}



PLAN: {plan}

---

## STEP 1: UNDERSTAND THE USER'S CORE NEED (Think)
Before executing tools:
- What is the user REALLY asking? (property search, area advice, investment decision?)
- What matters to them? (budget, family, commute, lifestyle, investment ROI?)
- Extract: budget, location, family size, specific concerns from context
- Use user's requirements IF given, else use context info

---

## STEP 2: EXECUTE THE PLAN (Act)
Run the tools from your plan above with actual parameters.

---

## STEP 3: SYNTHESIZE & PERSONALIZE (Reason & Format)
 DON'T: Just list tool outputs
 DO: 
- Reference user's specific situation ("Based on your 2M budget and family of 4...")
- Interpret results in their context ("This area is good for you because...")
- Compare options if multiple ("Property A is closer to your work, Property B is quieter...")
- Flag concerns ("Note: Area B has limited schools nearby")
- Make clear recommendations ("I suggest focusing on...")

---

## ANSWER STRUCTURE:

1️ **OPENING** (1-2 sentences)- do not explictly right opening this is just to show you structure
   - Acknowledge their question
   - Reference their specific situation

2️ **FINDINGS** (Tool outputs formatted naturally)-do not explictly right findings this is just to show you structure
   - For properties: "Here are the best options for you..."
   - For areas: "This neighborhood is ideal because..."
   - Weave results into narrative, not bullet lists
   - Include links/sources but integrated, not raw

3️ **PERSONALIZED ANALYSIS** (2-3 sentences)
   - What do these results mean FOR THEM?
   - How does it match their needs?
   - Any trade-offs to consider?

4️ **SUMMARY & SUGGESTIONS** (3-5 points)
   - Top 2-3 recommendations for them specifically
   - Next steps ("Would you like to know more about X?")
   - Questions to consider ("How important is school proximity?")

---

## TOOL EXECUTION REFERENCE:

search_egyptian_real_estate_tavily(
    location="New Cairo",
    bedrooms=3,
    max_price=8000000
)

analyze_egyptian_neighborhood_advanced(
    neighborhood="Rehab",
    user_scenario="family",
    specific_needs=["schools", "parks"]
)

search_market_intelligence(
    query="What are the current investment trends in Egyptian real estate?"
)

get_project_details(project_name="Palm Hills")

get_project_availability(project_name="Palm Hills", bedrooms=3)

nearby_places_tool(project_name="Palm Hills", radius_m=2000)

find_properties_tool(place_name="German University in Cairo", radius_km=5)

execute_python_query(code="get_market_summary()")

---

## CRITICAL RULES:
1.  Always reference user's personal context (budget, family, location preferences)
2.  Format as flowing narrative, not tool dumps
3.  Include links/sources but naturally integrated
4.  End with 2-3 personalized suggestions
5.  Be friendly, clear, and conversational, make the user feel like its taking to someone not a robot
6.  Flag risks or trade-offs relevant to them
7.  Ask follow-up questions to refine future searches

Execute the plan now using this reasoning approach."""
    
    # Add reasoning to messages
    enhanced_messages = [SystemMessage(content=system_context)] + clean_messages_for_groq(messages)
    
    response = llm_with_tools.invoke(enhanced_messages)
    
    # Log reasoning decision
    if response.tool_calls:
        tool_names = [tc.get('name') for tc in response.tool_calls]
        print(f" REASONING: Calling tools {tool_names} to advance the plan")
    else:
        print(" REASONING: Providing final answer - plan complete")
    
    return {"messages": [response], "next": "tools" if response.tool_calls else "end"}

def get_recent_tool_results(messages):
    """Extract recent tool results for context"""
    recent_results = []
    for msg in reversed(messages[:10]):  # Last 10 messages
        if isinstance(msg, ToolMessage):
            result_preview = str(msg.content)[:200] + "..." if len(str(msg.content)) > 200 else str(msg.content)
            recent_results.append(f"Tool Result: {result_preview}")
        elif isinstance(msg, AIMessage) and msg.tool_calls:
            recent_results.append(f"Tool Called: {[tc.get('name') for tc in msg.tool_calls]}")
    
    return "\n".join(recent_results[-3:]) if recent_results else "No recent tool results"





def tool_node(state: AgentState) -> dict:
    """Execute the tools that the agent called and update the state correctly."""
    
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [], "next": "end"}

    last_message = messages[-1]
    tool_results = []
    state_updates = {}


    # Loop over tool_calls produced by the agent's AIMessage (if any)
    for tool_call in getattr(last_message, "tool_calls", []) or []:
        #  VALIDATE tool_call structure BEFORE processing
        if not isinstance(tool_call, dict):
            print(f"⚠️ Skipping non-dict tool_call: {tool_call}")
            continue
            
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id")

        #  CRITICAL: Ensure args is always a valid dict
        if tool_args is None:
            tool_args = {}
        elif not isinstance(tool_args, dict):
            print(f" Converting non-dict args to dict for tool {tool_name}")
            tool_args = {}

        if not tool_name:
            print(f" Skipping tool_call without name: {tool_call}")
            continue
            
        if not tool_call_id:
            tool_call_id = f"call_{uuid.uuid4().hex[:8]}"

        print(f" Executing tool: {tool_name}")
        print(f" Tool arguments: {tool_args}")

        result = None
        
        try:
            #  CREATE FULL TOOL CALL STRUCTURE for tools that need it
            full_tool_call = {
                "name": tool_name,
                "args": tool_args,
                "type": "tool_call",
                "id": tool_call_id
            }

            #  FIXED: Use full tool call structure for tools that require InjectedToolCallId
            if tool_name == "execute_python_query":
                result = execute_python_query.invoke(full_tool_call)

            elif tool_name == "find_properties_tool":
                result = find_properties_tool.invoke(full_tool_call)
                
            elif tool_name == "google_maps_link_tool":
                result = google_maps_link_tool.invoke(full_tool_call)
                
            elif tool_name == "nearby_places_tool":
                result = nearby_places_tool.invoke(full_tool_call)
            
            elif tool_name == "get_project_info_tool":
                result = get_project_info_tool.invoke(full_tool_call)
            
            elif tool_name == "compare_projects_tool":
                result = compare_projects_tool.invoke(full_tool_call)

            elif tool_name == "search_egyptian_real_estate_tavily":
                result = search_egyptian_real_estate_tavily.invoke(full_tool_call)
            
            elif tool_name == "search_market_intelligence":
                result = search_market_intelligence.invoke(full_tool_call)
            
            elif tool_name == "analyze_egyptian_neighborhood_advanced":
                result = analyze_egyptian_neighborhood_advanced.invoke(full_tool_call)
            elif tool_name == "get_project_details":
                result = get_project_details.invoke(full_tool_call)
            elif tool_name == "semantic_project_search":
                result = semantic_project_search.invoke(full_tool_call)
            elif tool_name == "intelligent_project_matcher":
                result = intelligent_project_matcher.invoke(full_tool_call)
            elif tool_name == "get_project_availability":
                result = get_project_availability.invoke(full_tool_call)

                
            else:
                result = f"Unknown tool: {tool_name}"
                
            

        except Exception as e:
            result = f"Error executing tool {tool_name}: {str(e)}"
            print(f" Tool error: {e}")

        # Handle result
        if isinstance(result, Command):
            print(" Tool returned Command - extracting state updates")
            if hasattr(result, 'update') and result.update:
                for key, value in result.update.items():
                    if key == "messages":
                        tool_results.extend(value)
                    elif key == "saved_plots":
                        #  CRITICAL: Properly accumulate plots
                        if key not in state_updates:
                            state_updates[key] = []
                        state_updates[key].extend(value)
                        print(f" Added {len(value)} plot(s) to state updates")
                    else:
                        state_updates[key] = value

        


        else:
            tool_message = ToolMessage(
                content=str(result), 
                tool_call_id=tool_call_id
            )
            tool_results.append(tool_message)

   

    

    # Build response
    response = {
        "messages": tool_results,
        "next": "agent"
    }
    response.update(state_updates)
    
    return response

# Define routing logic
def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Determine whether to continue to tools or end"""
    return state.get("next", "end")

async def setup_postgres_checkpointer(
    connection_string: str = "postgresql://postgres:123456@localhost:5432/langgraph_db"
):
    """
    Setup ASYNC PostgreSQL checkpointer for CopilotKit
    """
    os.add_dll_directory(r"C:\Program Files\PostgreSQL\16\bin")
    
    #  Use AsyncConnectionPool (not ConnectionPool)
    pool = AsyncConnectionPool(
        conninfo=connection_string,
        max_size=20,
        kwargs={"autocommit": True, "prepare_threshold": 0}
    )
    
    #  Create ASYNC checkpointer
    checkpointer = AsyncPostgresSaver(pool)
    
    #  Await setup
    #await checkpointer.setup()
    
    print(" PostgreSQL checkpointer initialized successfully")
    
    return checkpointer


async def build_agent(llm,verbose: bool = True,use_postgres: bool = True):
    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes with verbose wrapper if needed
    if verbose:
        #workflow.add_node("profiler", lambda state: verbose_wrapper(user_profiling_node, state, "profiler"))
        workflow.add_node("planner", lambda state: verbose_wrapper(planning_node, state, "planner"))
        workflow.add_node("reasoning_agent", lambda state: verbose_wrapper(reasoning_agent_node, state, "reasoning_agent"))
        workflow.add_node("tools", lambda state: verbose_wrapper(tool_node, state, "tools"))
    else:
        
        #workflow.add_node("profiler", user_profiling_node)
        workflow.add_node("planner", planning_node)  # Replace router with planner
        workflow.add_node("reasoning_agent", reasoning_agent_node)  # Enhanced agent
        workflow.add_node("tools", tool_node)

    
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "reasoning_agent")
    workflow.add_conditional_edges(
        "reasoning_agent",
      should_continue,
    {"tools": "tools", "end": END}
)
    workflow.add_edge("tools", "reasoning_agent") 
    # workflow.add_edge(START, "profiler")
    # workflow.add_edge("profiler", "planner")
    # workflow.add_edge("planner", "reasoning_agent")
    # workflow.add_conditional_edges(
    #     "reasoning_agent",
    #     should_continue,
    #     {"tools": "tools", "end": END}
    # )
    # workflow.add_edge("tools", "reasoning_agent")


    #  Use PostgreSQL checkpointer
    # if use_postgres and connection_string:
    #     print(" Using PostgreSQL checkpointer")
    #     checkpointer =  await setup_postgres_checkpointer(connection_string)
    #     #  Add verification
    #     print(" Verifying database connection...")
    #     try:
    #         # Test connection
    #         import psycopg
    #         conn = psycopg.connect(connection_string)
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT COUNT(*) FROM checkpoints")
    #         count = cursor.fetchone()[0]
    #         print(f" Database accessible - {count} existing checkpoints")
    #         cursor.close()
    #         conn.close()
    #     except Exception as e:
    #         print(f" Database verification failed: {e}")
        
    # else:
    #     print(" Using in-memory checkpointer (no persistence)")
    #     print(use_postgres, connection_string)
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer,store=memory_store)




#     return result
def verbose_wrapper(node_func, state, node_name):
    """Wrapper to add verbose logging to node execution"""
    print(f"\n{'─'*80}")
    print(f" NODE: {node_name.upper()}")
    print(f"{'─'*80}")
    config = None
    if isinstance(state, tuple) and len(state) == 2:
        state, config = state
    elif hasattr(state, 'config'):
        config = state.config
    
    # Execute the actual node with config if available
    # 🆕 EXECUTE WITH CONFIG IF AVAILABLE
    if config and node_func.__code__.co_argcount == 2:
        # Node function expects (state, config)
        result = node_func(state, config)
    else:
        # Node function expects only state
        result = node_func(state)

    #  Handle Command return type first
    if isinstance(result, Command):
        print(f"🪄 Node '{node_name}' returned a Command object")

        # Try to inspect the Command contents safely
        update = getattr(result, "update", None)
        if isinstance(update, dict):
            messages = update.get("messages", [])
        else:
            messages = []

        if messages:
            print(f" Command contains {len(messages)} messages")
        else:
            print(" Command returned with no messages (state update only).")

        # Important: return Command to LangGraph unchanged
        return result

    
    elif isinstance(result, dict):
        messages = result.get("messages", [])
    else:
        print(f" Unexpected return type from node '{node_name}': {type(result)}")
        return result

   
    if node_name == "agent":
        if messages:
            last_msg = messages[-1]

            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                print(" Agent Decision: CALL TOOL")
                for tool_call in last_msg.tool_calls:
                    tool_name = tool_call.get('name', 'unknown')
                    tool_args = tool_call.get('args', {})
                    
                    print(f"\n Tool: {tool_name}")
                    
                    # ✅ FIXED: Display arguments based on tool type
                    if tool_name == "execute_python_query":
                        print(f" Code to execute:")
                        print("─" * 40)
                        print(tool_args.get("code", "N/A"))
                        print("─" * 40)
                    else:
                        # For other tools, display their arguments
                        print(f" Arguments:")
                        print("─" * 40)
                        for key, value in tool_args.items():
                            print(f"  {key}: {value}")
                        print("─" * 40)
            else:
                print(" Agent Decision: PROVIDE ANSWER")
                if hasattr(last_msg, "content") and last_msg.content:
                    print(f"\n💬 Response: {last_msg.content}")

    elif node_name == "tools":
        if messages:
            print("  Tool Execution Results:")
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    print("─" * 40)
                    print(msg.content)
                    print("─" * 40)

    return result











def clean_messages_for_groq(messages):
    """
    Clean messages for CopilotKit compatibility and reduce token usage.
    Keeps the last user message, the last AI message, and ALL tool outputs
    after that user message (so multi-step reasoning is preserved).
    """
    if not messages:
        return []

    # Find index of the last HumanMessage
    last_user_idx = next(
        (i for i in reversed(range(len(messages))) if isinstance(messages[i], HumanMessage)),
        None
    )

    if last_user_idx is None:
        return messages[-3:]  # fallback

    # Keep all messages since last user message (to preserve full reasoning chain)
    cleaned = messages[last_user_idx:]

    # Clean up AI tool_calls structure for safety
    final_cleaned = []
    for msg in cleaned:
        if isinstance(msg, AIMessage):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                fixed_tool_calls = []
                for idx, call in enumerate(msg.tool_calls):
                    if not isinstance(call, dict):
                        continue
                    fixed_call = {
                        "name": call.get("name"),
                        "id": call.get("id", f"call_{idx}"),
                        "args": call.get("args", {}) if isinstance(call.get("args"), dict) else {},
                        "type": call.get("type"),
                    }
                    fixed_tool_calls.append(fixed_call)
                msg.tool_calls = fixed_tool_calls
        final_cleaned.append(msg)

    print(f"✅ Reduced {len(messages)} → {len(final_cleaned)} (kept messages since last user input)")
    return final_cleaned




































