import chromadb
from chromadb.config import Settings

chroma_client = chromadb.Client(Settings(
    persist_directory="./chroma_store",
    anonymized_telemetry=False
))

collection = chroma_client.get_or_create_collection("papers")

def add_to_chroma(text):
    chunks = text.split("\n\n")  # Simple chunking
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids)
    return "papers"

def get_similar_chunks(query):
    results = collection.query(query_texts=[query], n_results=5)
    return results['documents'][0]
