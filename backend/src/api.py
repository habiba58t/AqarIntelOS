#Add this at the TOP of your file, before any imports
import sys
from unittest.mock import patch

# Patch pydantic to be more lenient with None args
def lenient_validate(self, data, **kwargs):
    # Fix tool_calls with None args
    if isinstance(data, dict) and "tool_calls" in data:
        if data["tool_calls"]:
            for tc in data["tool_calls"]:
                if isinstance(tc, dict) and tc.get("args") is None:
                    tc["args"] = {}
    return original_validate(self, data, **kwargs)

# Apply before importing langchain/copilotkit
try:
    from pydantic.main import BaseModel
    original_validate = BaseModel.__pydantic_validator__.validate_python
    BaseModel.__pydantic_validator__.validate_python = lenient_validate
except:
    pass

from fastapi import FastAPI, Request, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import asyncio
import pandas as pd
import uuid
from typing import Optional

from src.agent import build_agent
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from src.config import api_key, OPENAI_API_KEY

from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


from src.agent import build_agent
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from src.config import api_key

from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from contextlib import asynccontextmanager
from typing import Optional, List, Any, Dict

from src.Auth.database import get_async_db, create_auth_tables
from src.Auth.auth_schemas import UserCreate, UserLogin, Token, UserResponse
from src.Auth.auth_service import AuthService
from src.Auth.auth_utils import create_access_token
from src.Auth import auth_models
from starlette.middleware.base import BaseHTTPMiddleware



# Initialize LLM
llm = ChatOpenAI(model_name="gpt-4o", temperature=0.3, api_key=OPENAI_API_KEY)
#llm = ChatGroq(model_name="llama-3.1-8b-instant",temperature=0,api_key=api_key)
#llm = ChatGroq(model_name="llama-3.3-70b-versatile",temperature=0,api_key=api_key)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create auth tables on startup
    await create_auth_tables()
    
    # Build the agent (we'll use it dynamically per user)
    connection_string = "postgresql://postgres:123456@localhost:5432/langgraph_db"
    graph = await build_agent(llm)

    # Create a default agent for the base endpoint
    sdk = CopilotKitRemoteEndpoint(
        agents=[
            LangGraphAgent(
                name="policy_qa_agent",
                description="you are a real estate assistnt that has tools to helo answer user inquries ",
                graph=graph,
            )
        ],
    )

    add_fastapi_endpoint(app, sdk, "/copilotkit")
    print("✅ Default CopilotKit endpoint added")
    yield


app = FastAPI(lifespan=lifespan) 
import json
from fastapi import Request
from starlette.requests import Request as StarletteRequest
import traceback


@app.middleware("http")
async def sanitize_outgoing_responses(request: Request, call_next):
    """
    Sanitize responses GOING TO CopilotKit frontend
    """
    response = await call_next(request)
    
    # Only process copilotkit responses
    if "/copilotkit" in request.url.path:
        # For streaming responses, we need to read and fix the stream
        if isinstance(response, StreamingResponse):
            async def sanitized_stream():
                async for chunk in response.body_iterator:
                    try:
                        # Try to parse as JSON
                        if chunk:
                            data = json.loads(chunk)
                            
                            # Fix messages in the response
                            if isinstance(data, dict) and 'messages' in data:
                                for msg in data.get('messages', []):
                                    if isinstance(msg, dict) and 'tool_calls' in msg:
                                        for tc in msg.get('tool_calls', []):
                                            if isinstance(tc, dict) and tc.get('args') is None:
                                                tc['args'] = {}
                                                print("🔧 Fixed None args in outgoing response")
                            
                            # Re-encode and yield
                            yield json.dumps(data).encode()
                    except:
                        # If not JSON, pass through
                        yield chunk
            
            return StreamingResponse(
                sanitized_stream(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
    
    return response
    
    # For non-CopilotKit requests or no fixes needed, proceed normally

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Helper Function for Auth
# ==============================

async def get_current_user_from_header(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_db)
):
    """Extract and verify user from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    user = await AuthService.get_current_user(db, token)
    
    # Ensure user has thread_id - create one if missing
    if not user.thread_id:
        user.thread_id = str(uuid.uuid4())
        await db.commit()
        await db.refresh(user)
        print(f"🆕 Created thread_id for user {user.email}: {user.thread_id}")
    
    return user

# ==============================
# Helper Functions for Message Formatting
# ==============================

# def format_message_for_display(msg):
#     """Format a LangChain message object for frontend display"""
#     from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
    
#     msg_type = type(msg).__name__
    
#     # Handle different message types
#     if isinstance(msg, HumanMessage):
#         return {
#             "role": "user",
#             "content": msg.content,
#             "type": "human"
#         }
#     elif isinstance(msg, AIMessage):
#         # Check if it's a tool call or regular response
#         if hasattr(msg, 'tool_calls') and msg.tool_calls:
#             return {
#                 "role": "assistant",
#                 "content": f"[Executing tool: {msg.tool_calls[0]['name']}]",
#                 "type": "tool_call",
#                 "tool_calls": msg.tool_calls
#             }
#         else:
#             return {
#                 "role": "assistant",
#                 "content": msg.content,
#                 "type": "ai"
#             }
#     elif isinstance(msg, ToolMessage):
#         return {
#             "role": "system",
#             "content": msg.content,
#             "type": "tool_result"
#         }
#     elif isinstance(msg, SystemMessage):
#         return {
#             "role": "system",
#             "content": msg.content,
#             "type": "system"
#         }
#     else:
#         # Fallback for unknown types
#         return {
#             "role": "unknown",
#             "content": str(msg),
#             "type": msg_type.lower()
#         }



# ==============================
# Authentication Routes
# ==============================

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """Register new user with automatic thread_id creation"""
    user = await AuthService.register_user(db, user_data)
    
    # Create thread_id if not exists
    if not user.thread_id:
        user.thread_id = str(uuid.uuid4())
        await db.commit()
        await db.refresh(user)
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            thread_id=user.thread_id,
            created_at=user.created_at
        )
    )

@app.post("/api/auth/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_async_db)):
    """Login user and return existing thread_id"""
    user = await AuthService.authenticate_user(db, login_data.email, login_data.password)
    
    # Ensure thread_id exists
    if not user.thread_id:
        user.thread_id = str(uuid.uuid4())
        await db.commit()
        await db.refresh(user)
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            thread_id=user.thread_id,
            created_at=user.created_at
        )
    )

@app.post("/api/auth/logout")
async def logout():
    """Logout endpoint (token invalidation handled on frontend)"""
    return {"message": "Successfully logged out"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_endpoint(
    user = Depends(get_current_user_from_header),
    db: AsyncSession = Depends(get_async_db)
):
    """Get current authenticated user"""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        thread_id=user.thread_id,
        created_at=user.created_at
    )

@app.post("/api/auth/refresh")
async def refresh_token(
    user = Depends(get_current_user_from_header),
    db: AsyncSession = Depends(get_async_db)
):
    """Refresh access token"""
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ==============================
# Clear Chat History
# ==============================

@app.post("/api/user/chat/clear")
async def clear_chat_history(
    user = Depends(get_current_user_from_header),
    db: AsyncSession = Depends(get_async_db)
):
    """Clear user's chat history by creating a new thread_id"""
    old_thread_id = user.thread_id
    new_thread_id = str(uuid.uuid4())
    
    user.thread_id = new_thread_id
    await db.commit()
    await db.refresh(user)
    
    print(f"🗑️ Cleared chat history for {user.email}")
    print(f"   Old thread: {old_thread_id}")
    print(f"   New thread: {new_thread_id}")
    
    return {
        "message": "Chat history cleared",
        "old_thread_id": old_thread_id,
        "new_thread_id": new_thread_id
    }
# ==============================
# Recommended projects 
# ==============================
import psycopg2
import requests
import psycopg2.extras  # ✅ Add this line

# @app.get("/api/projects/recommended")
# def get_recommended_projects():
#     try:
#         conn = psycopg2.connect(
#                 "dbname=langgraph_db user=postgres password=123456 host=localhost"
#             )
#         cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
#         query = """
#             SELECT 
#                 name,
#                 location_name AS location,
#                 min_price,
#                 max_price,
#                 thumbnail_url AS image
#             FROM recommended_projects
#             ORDER BY min_price DESC
#             LIMIT 6;
#         """
        
#         cur.execute(query)
#         projects = cur.fetchall()

#         cur.close()
#         conn.close()
#         return projects

#     except Exception as e:
#         print("Error fetching recommended projects:", e)
#         return {"error": str(e)}

# Database connection string

# Add this endpoint to fetch projects with coordinates
@app.get("/api/projects/map")
async def get_projects_for_map():
    """
    Fetch all projects with their coordinates for map display
    """
    try:
        conn = psycopg2.connect(
            "dbname=langgraph_db user=postgres password=123456 host=localhost"
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Query to get projects with coordinates
        query = """
            SELECT 
                l.name,
                l.location_name AS location,
                l.min_price,
                l.max_price,
                l.thumbnail_url AS image,
                l.description,
                p.latitude,
                p.longitude
            FROM properties p
            Inner  JOIN recommended_projects l ON p.name = l.name
            WHERE p.latitude IS NOT NULL 
              AND p.longitude IS NOT NULL;
        """
        
        cur.execute(query)
        projects = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Convert to list of dicts
        projects_list = [dict(project) for project in projects]
        
        return {
            "success": True,
            "count": len(projects_list),
            "projects": projects_list
        }
        
    except Exception as e:
        print("❌ Error fetching projects for map:", e)
        return {
            "success": False,
            "error": str(e),
            "projects": []
        }

@app.get("/api/projects/recommended/{email}")
def get_personalized_recommendations(email: str):
    """
    Returns personalized project recommendations for a user using vector similarity (based on email).
    """
    try:
        conn = psycopg2.connect(
            "dbname=langgraph_db user=postgres password=123456 host=localhost"
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1️⃣ Get user embedding by email
        cur.execute("SELECT embedding FROM users WHERE email = %s AND embedding IS NOT NULL", (email,))
        user_row = cur.fetchone()

        if not user_row or not user_row["embedding"]:
            return {"error": "User embedding not found. Please generate embeddings first."}

        user_embedding = user_row["embedding"]

        # 2️⃣ Get top similar projects by cosine distance
        query = """
            SELECT 
                name,
                location_name AS location,
                min_price,
                max_price,
                thumbnail_url AS image,
                1 - (embedding <=> %s::vector) AS similarity
            FROM recommended_projects
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 6;
        """

        cur.execute(query, (user_embedding, user_embedding))
        projects = cur.fetchall()

        cur.close()
        conn.close()

        # 3️⃣ Sort by similarity (optional)
        projects.sort(key=lambda x: x['similarity'], reverse=True)

        return {"email": email, "recommended_projects": projects}

    except Exception as e:
        print("❌ Error fetching personalized recommendations:", e)
        return {"error": str(e)}















from pydantic import BaseModel
from typing import List, Optional
import psycopg
from psycopg.rows import dict_row
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/langgraph_db"

class UserProfile(BaseModel):
    email: str
    name: str
    preferredLocations: List[str] = []
    averageBudget: int = 0
    # preferredUnitType: List[str] = []

class UserProfileUpdate(BaseModel):
    preferredLocations: Optional[List[str]] = None
    averageBudget: Optional[int] = None
    # preferredUnitType: Optional[List[str]] = None
    
# ✅ GET user profile
@app.get("/api/user/profile", response_model=UserProfile)
async def get_user_profile(email: str):
    """
    Fetch user profile and preferences from database
    """
    print(email)
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT 
                        email,
                        name,
                        preferred_locations as "preferredLocations",
                        budget as "averageBudget",
                        family_size,
                        is_investor
                    FROM users
                    WHERE email = %s
                """, (email,))
                
                user = cur.fetchone()
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Convert PostgreSQL array to Python list
                return UserProfile(
                    email=user["email"],
                    name=user["name"],
                    preferredLocations=user.get("preferredLocations") or [],
                    averageBudget=user.get("averageBudget") or 0,
                    family_size=user.get("family_size") or 0,
                    is_investor=user.get("is_investor") or False
                    
                )
                
    except psycopg.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ✅ UPDATE user profile
@app.put("/api/user/profile")
async def update_user_profile(email: str, profile: UserProfileUpdate):
    """
    Update user preferences
    """
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Build dynamic update query
                update_fields = []
                values = []
                
                if profile.preferredLocations is not None:
                    update_fields.append("preferred_locations = %s")
                    values.append(profile.preferredLocations)
                
                if profile.averageBudget is not None:
                    update_fields.append("average_budget = %s")
                    values.append(profile.averageBudget)

                if profile.family_size is not None:
                    update_fields.append("family_size = %s")
                    values.append(profile.family_size)

                if profile.is_investor is not None:
                    update_fields.append("is_investor = %s")
                    values.append(profile.is_investor)
                
                
                # if profile.preferredUnitType is not None:
                #     update_fields.append("preferred_unit_type = %s")
                #     values.append(profile.preferredUnitType)
                
                if not update_fields:
                    raise HTTPException(status_code=400, detail="No fields to update")
                
                values.append(email)
                
                query = f"""
                    UPDATE users
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE email = %s
                    RETURNING email
                """
                
                cur.execute(query, values)
                result = cur.fetchone()
                
                if not result:
                    raise HTTPException(status_code=404, detail="User not found")
                
                conn.commit()
                
                return {"message": "Profile updated successfully"}
                
    except psycopg.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/api/projects/all")
async def get_all_projects():
    try:
        conn = psycopg2.connect(
            "dbname=langgraph_db user=postgres password=123456 host=localhost"
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        query = """
            SELECT 
                name,
                location_name AS location,
                min_price,
                max_price,
                thumbnail_url AS image,
                description,
                developer_name as developer,
                payment_plans
            FROM recommended_projects
            order by max_price
            limit 40
        """
        
        cur.execute(query)
        projects = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(projects),
            "projects": [dict(p) for p in projects]
        }
    except Exception as e:
        return {"success": False, "error": str(e), "projects": []}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)