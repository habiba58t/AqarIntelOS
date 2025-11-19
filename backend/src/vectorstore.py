from langchain.text_splitter import RecursiveCharacterTextSplitter

# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain.vectorstores import FAISS

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

def build_vectorstore(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": device},  # change to "cuda" if you have GPU
    encode_kwargs={"batch_size": 32}  # split large input into batches
)
    #vectordb = FAISS.from_documents(chunks, embeddings)
    #vectordb.save_local("faiss_index2")
    vectordb = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    return vectordb

def build_vectorstore2(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": device},  # change to "cuda" if you have GPU
    encode_kwargs={"batch_size": 32}  # split large input into batches
)
    vectordb2 = FAISS.from_documents(chunks, embeddings)
    vectordb2.save_local("faiss_index2")
   # vectordb = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    return vectordb2
