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
    def __init__(self, collection):
        self.collection = collection

    def _generate_chunks(self, text_segments_generator, max_chunk_size=1000, overlap_size=200, max_total_bytes=1000000): # Increased to 1MB (approx. 1,000,000 bytes)
        """
        Generates chunks from an iterable of text segments (e.g., pages from a PDF parser),
        respecting chunk size, overlap, and total byte limits.
        This avoids building the entire document text in memory.
        """
        chunks = []
        current_chunk_buffer = ""
        total_bytes_processed = 0

        for segment in text_segments_generator:
            sentences = re.split(r'(?<=[.!?])\s+', segment.strip())
            
            for sentence in sentences:
                sentence_with_space = sentence + " "
                
                # Check if adding the current sentence would exceed max_chunk_size
                if len(current_chunk_buffer) + len(sentence_with_space) > max_chunk_size:
                    # If buffer is not empty, finalize it as a chunk
                    if current_chunk_buffer.strip():
                        chunk_to_add = current_chunk_buffer.strip()
                        encoded_chunk = chunk_to_add.encode("utf-8")

                        # Check if adding this chunk would exceed the total byte limit
                        if total_bytes_processed + len(encoded_chunk) > max_total_bytes:
                            return chunks # Stop and return chunks collected so far
                        
                        chunks.append(chunk_to_add)
                        total_bytes_processed += len(encoded_chunk)

                        # Prepare overlap for the next chunk
                        # Take the last `overlap_size` characters from the added chunk
                        overlap_text = chunk_to_add[-overlap_size:] if len(chunk_to_add) > overlap_size else chunk_to_add
                        
                        # Find the last space in the overlap to avoid cutting words in half
                        last_space = overlap_text.rfind(' ')
                        if last_space != -1:
                            current_chunk_buffer = overlap_text[last_space+1:] # Start new buffer from after last space
                        else:
                            current_chunk_buffer = overlap_text # If no space, take whole overlap_text
                        current_chunk_buffer += " " # Add space for next sentence
                    else:
                        # This case handles a single sentence larger than max_chunk_size.
                        # We add it as its own chunk and reset the buffer.
                        chunk_to_add = sentence.strip()
                        encoded_chunk = chunk_to_add.encode("utf-8")
                        if total_bytes_processed + len(encoded_chunk) > max_total_bytes:
                            return chunks
                        chunks.append(chunk_to_add)
                        total_bytes_processed += len(encoded_chunk)
                        current_chunk_buffer = "" # Reset buffer after adding large sentence

                current_chunk_buffer += sentence_with_space

        # Add any remaining content in the buffer as a final chunk
        if current_chunk_buffer.strip():
            final_chunk = current_chunk_buffer.strip()
            encoded_final = final_chunk.encode("utf-8")
            if total_bytes_processed + len(encoded_final) <= max_total_bytes:
                chunks.append(final_chunk)

        return chunks

    def _generate_doc_tag(self, content_bytes):
        return hashlib.sha1(content_bytes).hexdigest()

    def _generate_title_slug(self, title: str):
        words = re.findall(r'\w+', title)[:5]
        return "_".join(words).lower()

    def add_document(self, text_generator, doc_tag: str, title: str): # Accepts generator
        """
        Adds a document to the Chroma collection by processing text from a generator.
        """
        title_slug = self._generate_title_slug(title)
        self.collection.delete(where={"doc_tag": doc_tag})

        # Pass the generator to _generate_chunks
        chunks = self._generate_chunks(text_generator)
        if not chunks:
            # Raise a more specific error for clarity
            raise ValueError(f"Document '{title}' is too large or resulted in no valid chunks after processing. Max total bytes allowed: {self._generate_chunks.__defaults__[2]} bytes.")

        ids = [f"{title_slug}_chunk_{i}" for i in range(len(chunks))]
        metadata = [{"doc_tag": doc_tag, "doc_title": title_slug} for _ in chunks]

        # Add documents to ChromaDB
        self.collection.add(documents=chunks, ids=ids, metadatas=metadata)
        return title_slug

    def get_similar_chunks(self, query, title_slug=None, n_results=5):
        where_filter = {"doc_title": title_slug} if title_slug else {}
        results = self.collection.query(query_texts=[query], n_results=n_results, where=where_filter)
        return {
            "chunks": results["documents"][0],
            "metadatas": results["metadatas"][0],
        }

    def delete_document(self, doc_tag):
        self.collection.delete(where={"doc_tag": doc_tag})
        return f"Deleted all chunks with tag: {doc_tag}"

