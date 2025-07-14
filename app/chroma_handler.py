import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import os
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
            candidate = (chunk + para + "\n").strip()
            encoded = candidate.encode("utf-8")

            if len(encoded) > max_chunk_size:
                continue  # skip large paragraphs

            if total_bytes + len(encoded) > max_total_bytes:
                break

            chunk = candidate
            chunks.append(chunk)
            total_bytes += len(encoded)
            chunk = ""  # reset for next chunk

        # Fallback: if no chunk made it
        if not chunks and text:
            encoded_text = text.encode("utf-8")
            if len(encoded_text) <= max_total_bytes:
                chunks.append(text.strip())
            else:
                chunks.append(encoded_text[:max_total_bytes].decode("utf-8", errors="ignore"))

        return chunks

    def _generate_doc_tag(self, content_bytes):
        return hashlib.sha1(content_bytes).hexdigest()

    def add_document(self, text, doc_tag):
        self.collection.delete(where={"doc_tag": doc_tag})
        chunks = self._chunk_text(text)

        if not chunks:
            raise ValueError("No valid chunks could be created from the document.")

        ids = [f"{doc_tag}_chunk_{i}" for i in range(len(chunks))]
        metadata = [{"doc_tag": doc_tag} for _ in chunks]

        self.collection.add(documents=chunks, ids=ids, metadatas=metadata)
        return doc_tag

    def get_similar_chunks(self, query, doc_tags=None, n_results=5):
        where_filter = {"doc_tag": {"$in": doc_tags}} if doc_tags else {}

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        return {
            "chunks": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        }

    def delete_document(self, doc_tag):
        self.collection.delete(where={"doc_tag": doc_tag})
        return f"Deleted all chunks with tag: {doc_tag}"
