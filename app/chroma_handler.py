import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

chroma_client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant=os.getenv("CHROMA_TENANT"),
    database=os.getenv("CHROMA_DATABASE"),
)

collection = chroma_client.get_or_create_collection("papers")

def add_to_chroma(text, doc_tag="default_doc"):
    # Delete any existing chunks related to this document
    collection.delete(where={"doc_tag": doc_tag})

    chunks = text.split("\n\n")  # You can improve chunking later
    ids = [f"{doc_tag}_chunk_{i}" for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=[{"doc_tag": doc_tag} for _ in chunks]
    )
    return doc_tag

def get_similar_chunks(query):
    results = collection.query(query_texts=[query], n_results=5)
    return results['documents'][0]
