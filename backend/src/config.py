import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
api_key=os.getenv("GROQ_API_KEY")
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")



# os.environ["LANGSMITH_TRACING"] = "true"
# os.environ["LANGSMITH_PROJECT"] = "AqarIntelOS"
# os.environ["LANGSMITH_API_KEY"] = "LANGSMITH_API_KEY"
import os

os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "AqarIntelOS"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"



# from langsmith import Client
# from datetime import datetime
# client = Client()


# client.update_run(
#     "702e14bd-761a-4d74-997a-0ff1703beb84", 
#     end_time=datetime.now(), 
#     error="Manually stopped"
# )









