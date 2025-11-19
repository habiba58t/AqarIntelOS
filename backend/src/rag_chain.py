from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from src.config import api_key
from langsmith import trace


def build_rag(vectordb):
  with trace("build_rag"):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",  # or "llama-3.1-70b-versatile" if you want more reasoning
        api_key=api_key
    )
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectordb.as_retriever(),
        return_source_documents=False
    )
    return qa

def build_rag2(vectordb):
  with trace("build_rag"):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",  # or "llama-3.1-70b-versatile" if you want more reasoning
        api_key=api_key
    )
    qa2 = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectordb.as_retriever(),
        return_source_documents=False
    )
    return qa2