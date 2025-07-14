import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import os
import hashlib
import re

# Load environment variables
load_dotenv()

chroma_client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant=os.getenv("CHROMA_TENANT"),
    database=os.getenv("CHROMA_DATABASE"),
)

collection = chroma_client.get_or_create_collection("papers")


class ChromaHandler:
    def __init__(self, collection):
        self.collection = collection

    def _chunk_text(self, text, max_chunk_size=1000, overlap_size=200, max_total_bytes=16000):
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks = []
        current_chunk = ""
        total_bytes = 0
        i = 0

        while i < len(sentences):
            while i < len(sentences) and len(current_chunk) + len(sentences[i]) <= max_chunk_size:
                current_chunk += sentences[i] + " "
                i += 1

            chunk = current_chunk.strip()
            encoded = chunk.encode("utf-8")

            if total_bytes + len(encoded) > max_total_bytes:
                break

            chunks.append(chunk)
            total_bytes += len(encoded)

            # Create overlap
            overlap_tokens = chunk[-overlap_size:].split() if overlap_size else []
            current_chunk = " ".join(overlap_tokens) + " " if overlap_tokens else ""

        # Add last chunk if not added
        if current_chunk.strip():
            encoded = current_chunk.strip().encode("utf-8")
            if total_bytes + len(encoded) <= max_total_bytes:
                chunks.append(current_chunk.strip())

        return chunks

    def _generate_doc_tag(self, content_bytes):
        return hashlib.sha1(content_bytes).hexdigest()

    def add_document(self, text, doc_tag):
        self.collection.delete(where={"doc_tag": doc_tag})
        chunks = self._chunk_text(text)
        if not chunks:
            raise ValueError("Document too large or empty. No chunks generated.")
        ids = [f"{doc_tag}_chunk_{i}" for i in range(len(chunks))]
        metadata = [{"doc_tag": doc_tag} for _ in chunks]
        self.collection.add(documents=chunks, ids=ids, metadatas=metadata)
        return doc_tag

    def get_similar_chunks(self, query, doc_tags=None, n_results=5):
        where_filter = {"doc_tag": {"$in": doc_tags}} if doc_tags else {}
        results = self.collection.query(query_texts=[query], n_results=n_results, where=where_filter)
        return {
            "chunks": results["documents"][0],
            "metadatas": results["metadatas"][0],
        }

    def delete_document(self, doc_tag):
        self.collection.delete(where={"doc_tag": doc_tag})
        return f"Deleted all chunks with tag: {doc_tag}"
