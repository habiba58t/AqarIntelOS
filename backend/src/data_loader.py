# from langchain.document_loaders import PyPDFLoader, CSVLoader
from langchain_community.document_loaders import PyPDFLoader, CSVLoader
def load_pdfs(path):
    loader = PyPDFLoader(path)
    return loader.load()

def load_csv(path):
    loader = CSVLoader(path, encoding="utf-8")
    return loader.load()
