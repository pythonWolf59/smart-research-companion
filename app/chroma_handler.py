import hashlib
import os
import re

import chromadb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# The Chroma server host and port must be set as environment variables
# in your App Runner service configuration. The host is the public IP
# address of the EC2 instance you launched.
chroma_host = os.getenv("CHROMA_SERVER_HOST")
chroma_port = os.getenv("CHROMA_SERVER_PORT", "8000")

# Ensure the host is set before attempting to create the client.
# This check prevents the application from crashing if the environment variable is missing.
if not chroma_host:
    raise ValueError(
        "CHROMA_SERVER_HOST environment variable is not set. Please set it to the public IP of your EC2 instance.")

# Use HttpClient to connect to the remote ChromaDB server.
# This client will communicate with the Chroma instance running on your EC2 machine.
# This code handles potential connection errors.
try:
    client = chromadb.HttpClient(
        host=chroma_host,
        port=int(chroma_port)
    )
    print(f"Successfully connected to ChromaDB at http://{chroma_host}:{chroma_port}")
except Exception as e:
    # If the connection fails, log the error and re-raise it to halt the application.
    # This is important for App Runner's health checks to detect a failed startup.
    print(f"Failed to connect to ChromaDB at http://{chroma_host}:{chroma_port}. Error: {e}")
    raise ConnectionError(f"Could not connect to ChromaDB: {e}")

# Get or create the collection for storing your papers.
collection = client.get_or_create_collection("papers")


class ChromaHandler:
    def __init__(self):
        self.collection = collection

    def _generate_title_slug(self, title: str):
        words = re.findall(r'\w+', title)[:5]
        return "_".join(words).lower()

    def add_chunks_with_embeddings_to_chroma(self, chunks: list, embeddings: list, doc_title: str):
        """
        Adds a document's chunks and pre-computed embeddings to the Chroma collection.
        This method assumes the chunks are already generated.
        """
        title_slug = self._generate_title_slug(doc_title)

        # Delete existing documents with the same title to avoid duplicates.
        existing_docs = self.collection.get(where={"doc_title": title_slug})
        if existing_docs:
            self.collection.delete(where={"doc_title": title_slug})

        ids = [f"{title_slug}_chunk_{i}" for i in range(len(chunks))]
        metadata = [{"doc_title": title_slug} for _ in chunks]

        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            ids=ids,
            metadatas=metadata
        )
        return title_slug

    def get_similar_chunks(self, query_embedding, doc_title=None, n_results=5):
        """
        Finds and returns the most similar chunks based on a query embedding.
        """
        where_filter = {"doc_title": doc_title} if doc_title else {}
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )
        return results["documents"][0] if results["documents"] else []

    def get_all_titles(self):
        """
        Retrieves all unique document titles from the collection.
        """
        results = self.collection.get(include=["metadatas"])
        titles = set()
        for metadata in results.get("metadatas", []):
            if metadata and "doc_title" in metadata:
                titles.add(metadata["doc_title"])
        return list(titles)

    def get_all_chunks_for_document(self, doc_title):
        """
        Retrieves all chunks for a given document title.
        """
        results = self.collection.get(
            where={"doc_title": doc_title},
            include=["documents"]
        )
        chunks_with_ids = list(zip(results["ids"], results["documents"]))
        chunks_with_ids.sort(key=lambda x: int(x[0].split('_')[-1]))
        return [chunk for id, chunk in chunks_with_ids]

    def delete_document(self, doc_title):
        self.collection.delete(where={"doc_title": doc_title})
        return f"Deleted all chunks for document title: {doc_title}"
