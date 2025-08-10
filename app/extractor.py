# extractor.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_and_chunk_pdf(file_path):
    """
    Loads a PDF, splits its text into chunks, and returns them.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        list: A list of text chunks.
    """
    print(f"Loading and processing PDF: {file_path}")
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(pages)
    chunk_texts = [chunk.page_content for chunk in chunks]
    print(f"Split PDF into {len(chunk_texts)} chunks.")
    return chunk_texts
