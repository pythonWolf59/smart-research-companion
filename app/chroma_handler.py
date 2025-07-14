import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import os
import uuid
import hashlib

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

    def _chunk_text(self, text, max_chunk_size=500, max_total_bytes=16000):
        paragraphs = text.split("\n\n")
        chunks, chunk = [], ""
        total_bytes = 0

        for para in paragraphs:
            candidate_chunk = chunk + para + "\n"
            encoded = candidate_chunk.strip().encode("utf-8")

            if len(encoded) > max_chunk_size:
                continue

            if total_bytes + len(encoded) > max_total_bytes:
                break

            chunk = candidate_chunk
            if len(chunk.encode("utf-8")) >= max_chunk_size or para == paragraphs[-1]:
                final = chunk.strip()
                chunks.append(final)
                total_bytes += len(final.encode("utf-8"))
                chunk = ""

        return chunks

    def _generate_doc_tag(self, content_bytes):
        return hashlib.sha1(content_bytes).hexdigest()

    def add_document(self, text, doc_tag):
        # Delete existing entries for this doc
        self.collection.delete(where={"doc_tag": doc_tag})

        chunks = self._chunk_text(text)
        ids = [f"{doc_tag}_chunk_{i}" for i in range(len(chunks))]
        metadata = [{"doc_tag": doc_tag} for _ in chunks]

        self.collection.add(documents=chunks, ids=ids, metadatas=metadata)
        return doc_tag

    def get_similar_chunks(self, query, doc_tags=None, n_results=5):
        if doc_tags:
            where_filter = {"doc_tag": {"$in": doc_tags}}
        else:
            where_filter = {}

        results = self.collection.query(query_texts=[query], n_results=n_results, where=where_filter)

        return {
                "chunks": results["documents"][0],
                "metadatas": results["metadatas"][0],
                }

    def delete_document(self, doc_tag):
        self.collection.delete(where={"doc_tag": doc_tag})
        return f"Deleted all chunks with tag: {doc_tag}"

# Usage
# handler = ChromaHandler(collection)
# handler.add_document(text, doc_tag="some_id")
# similar = handler.get_similar_chunks("deep learning")
# handler.delete_document("some_id")
