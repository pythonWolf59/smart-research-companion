import hashlib
import os
import re

import chromadb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

chroma_client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant=os.getenv("CHROMA_TENANT"),
    database=os.getenv("CHROMA_DATABASE"),
)

collection = chroma_client.get_or_create_collection("papers")


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



