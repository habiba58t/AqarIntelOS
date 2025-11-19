"""
FastAPI server exposing a LangGraph agent for querying the GIU Admin Policy PDF.

This application uses:
- FastAPI for the web server
- LangGraph for agent orchestration with tool calling
- CopilotKit for frontend integration
- OpenAI embeddings for vectorization
- In-memory vector store for document retrieval
- Tool-calling pattern where the LLM decides when to query the PDF
"""

import os
from typing import Annotated, Any
from contextlib import asynccontextmanager
import logging

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class State(TypedDict):
    """State schema for the conversational agent."""
    messages: Annotated[list, add_messages]
    retrieved_chunks: list[dict[str, Any]]  # Store retrieved document chunks


def load_and_index_pdf(pdf_path: str):
    """
    Load PDF, split into chunks, and create a vector store with embeddings.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        A retriever object for querying the indexed documents
    """
    logger.info(f"Loading PDF from: {pdf_path}")

    # Load the PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    logger.info(f"Loaded {len(documents)} pages from PDF")

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    splits = text_splitter.split_documents(documents)

    logger.info(f"Split into {len(splits)} chunks")

    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = DocArrayInMemorySearch.from_documents(
        documents=splits,
        embedding=embeddings
    )

    logger.info("Vector store created successfully")

    # Create and return retriever
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 3}  # Retrieve top 3 most relevant chunks
    )

    return retriever


def create_agent_graph(retriever):
    """
    Create a LangGraph agent with tool-calling capability.

    Args:
        retriever: The retriever for querying the PDF

    Returns:
        Compiled LangGraph agent graph
    """
    # Create retrieval tool
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_policy_info",
        "Search and retrieve information from the GIU Admin Policy document. "
        "Use this tool to answer questions about GIU administrative policies, "
        "procedures, regulations, and guidelines."
    )

    tools = [retriever_tool]

    # Initialize LLM with tool binding
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # Define the chatbot node
    def chatbot(state: State):
        """
        Main agent node that decides whether to use tools or respond directly.
        """
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    # Define a custom tool node that captures retrieved chunks
    def retrieve_and_store(state: State):
        """
        Custom tool node that executes retrieval and stores chunks in state.
        """
        # Get the last message (which should have tool calls)
        last_message = state["messages"][-1]

        # Execute the tool calls
        tool_node = ToolNode(tools=tools)
        result = tool_node.invoke(state)

        # Extract retrieved chunks if the retrieval tool was called
        retrieved_chunks = []
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                if tool_call.get("name") == "retrieve_policy_info":
                    # Get the query that was used
                    query = tool_call.get("args", {}).get("query", "")

                    # Retrieve documents to get chunk details
                    docs = retriever.invoke(query)

                    # Format chunks for frontend display
                    for i, doc in enumerate(docs):
                        chunk_info = {
                            "content": doc.page_content,
                            "page": doc.metadata.get("page", "Unknown"),
                            "source": doc.metadata.get("source", "GIU Policy"),
                            "index": i + 1,
                        }
                        retrieved_chunks.append(chunk_info)

        return {
            "messages": result.get("messages", []),
            "retrieved_chunks": retrieved_chunks
        }

    # Build the graph
    graph_builder = StateGraph(State)

    # Add nodes
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", retrieve_and_store)

    # Add edges
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
            # If LLM makes a tool call, go to tools; otherwise END
    )
    graph_builder.add_edge("tools", "chatbot")  # After tools, return to chatbot

    # Compile with memory for conversation persistence
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    return graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI.
    Initializes the agent on startup.
    """
    # Startup
    # Validate OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in a .env file or export it."
        )

    logger.info("\n" + "=" * 60)
    logger.info("Starting GIU Admin Policy QA Agent API")
    logger.info("=" * 60 + "\n")

    # Path to the PDF file
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "docs", "GIU policy_ Admin.pdf")

    # Load and index the PDF
    retriever = load_and_index_pdf(pdf_path)

    # Create the agent graph
    graph = create_agent_graph(retriever)

    # Create CopilotKit Remote Endpoint with our LangGraph agent
    sdk = CopilotKitRemoteEndpoint(
        agents=[
            LangGraphAgent(
                name="policy_qa_agent",
                description="An agent that answers questions about the GIU Admin Policy document",
                graph=graph,
            )
        ],
    )

    # Add the CopilotKit endpoint to our FastAPI app
    add_fastapi_endpoint(app, sdk, "/copilotkit")

    logger.info("\n✅ Agent initialized and ready at /copilotkit")
    logger.info("🏥 Health check available at /health\n")

    yield

    # Shutdown (cleanup if needed)
    logger.info("Shutting down...")


# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="GIU Policy QA Agent API",
    description="API for querying the GIU Admin Policy document using a conversational agent",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default
        "http://localhost:3001",  # Alternative port
        "https://localhost:3000",
        "https://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "policy_qa_agent"}


def main():
    """Run the FastAPI server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
