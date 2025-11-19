from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any
import psycopg2
import psycopg2.extras

class EmbeddingService:
    def __init__(self):
        # Using a lightweight model (384 dimensions)
        # You can use 'all-MiniLM-L6-v2' or 'all-mpnet-base-v2' (768 dims)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")
    
    def generate_project_embedding(self, project: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a project based on its features
        """
        # Combine project features into a text description
        text_parts = []
        
        if project.get('name'):
            text_parts.append(f"Project: {project['name']}")
        
        if project.get('location'):
            text_parts.append(f"Location: {project['location']}")
        
        if project.get('developer'):
            text_parts.append(f"Developer: {project['developer']}")
        
        if project.get('min_price') and project.get('max_price'):
            price_range = f"Price range: {project['min_price']} to {project['max_price']}"
            text_parts.append(price_range)
        
        if project.get('description'):
            text_parts.append(project['description'])
        
        # Join all parts
        text = ". ".join(text_parts)
        
        # Generate embedding
        embedding = self.model.encode(text, normalize_embeddings=True)
        
        return embedding.tolist()
    
    def generate_user_embedding(self, user_preferences: Dict[str, Any]) -> List[float]:
     """
     Generate embedding for user preferences, similar to project embeddings
     """
     text_parts = []

    # Locations
     if user_preferences.get('preferred_locations'):
        locations = ", ".join(user_preferences['preferred_locations'])
        text_parts.append(f"Preferred locations: {locations}")

    # Budget
     if user_preferences.get('budget'):
        text_parts.append(f"Estimated budget: {user_preferences['budget']:,} EGP")

    # Unit types
     if user_preferences.get('preferred_unit_types'):
        types = ", ".join(user_preferences['preferred_unit_types'])
        text_parts.append(f"Preferred unit types: {types}")

    # Amenities
     if user_preferences.get('preferred_amenities'):
        amenities = ", ".join(user_preferences['preferred_amenities'])
        text_parts.append(f"Desired amenities: {amenities}")

    # Developer
     if user_preferences.get('preferred_developer'):
        text_parts.append(f"Preferred developer: {user_preferences['preferred_developer']}")

    # Combine into one descriptive text
     text = ". ".join(text_parts)

    # Generate and normalize the embedding
     embedding = self.model.encode(text, normalize_embeddings=True)

     return embedding.tolist()


# Initialize global instance
embedding_service = EmbeddingService()








# def generate_all_project_embeddings():
#     """
#     Generate embeddings for all projects in the database
#     """
#     try:
#         conn = psycopg2.connect(
#             "dbname=langgraph_db user=postgres password=123456 host=localhost"
#         )
#         cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
#         # Fetch all projects
#         cur.execute("""
#             SELECT name, location_name as location, developer_name as developer, 
#                    min_price, max_price, description
#             FROM recommended_projects
#         """)
#         projects = cur.fetchall()
        
#         print(f"📊 Found {len(projects)} projects")
        
#         # Generate embeddings for each project
#         for i, project in enumerate(projects, 1):
#             print(f"Processing {i}/{len(projects)}: {project['name']}")
            
#             # Generate embedding
#             embedding = embedding_service.generate_project_embedding(project)
            
#             # Update database
#             cur.execute("""
#                 UPDATE recommended_projects 
#                 SET embedding = %s
#                 WHERE name = %s
#             """, (embedding, project['name']))
        
#         conn.commit()
#         print("✅ All project embeddings generated successfully!")
        
#         cur.close()
#         conn.close()
        
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         import traceback
#         traceback.print_exc()
import json

def generate_all_user_embeddings():
    """
    Generate embeddings for all existing users in the database
    """
    try:
        conn = psycopg2.connect(
            "dbname=langgraph_db user=postgres password=123456 host=localhost"
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Fetch all users with preference data
        cur.execute("""
            SELECT id,preferred_locations, budget, 
                   preferred_amenities, preferred_developer
            FROM users
        """)
        users = cur.fetchall()
        
        print(f"👤 Found {len(users)} users")

        for i, user in enumerate(users, 1):
            print(f"Processing user {i}/{len(users)}: {user['id']}")
            
            # Convert JSON/arrays (if stored as text)
            user_preferences = {
                "preferred_locations": user.get("preferred_locations") or [],
                "budget": user.get("budget"),
                # "preferred_unit_types": user.get("preferred_unit_types") or [],
                "preferred_amenities": user.get("preferred_amenities") or [],
                "preferred_developer": user.get("preferred_developer")
            }

            # Ensure lists (PostgreSQL JSON/text may return strings)
            for key in ["preferred_locations", "preferred_amenities"]:
                if isinstance(user_preferences[key], str):
                    try:
                        user_preferences[key] = json.loads(user_preferences[key])
                    except:
                        user_preferences[key] = [user_preferences[key]]

            # Generate user embedding
            embedding = embedding_service.generate_user_embedding(user_preferences)

            # Update user record
            cur.execute("""
                UPDATE users 
                SET embedding = %s
                WHERE id = %s
            """, (embedding, user["id"]))
        
        conn.commit()
        print("✅ All user embeddings generated successfully!")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_all_user_embeddings()