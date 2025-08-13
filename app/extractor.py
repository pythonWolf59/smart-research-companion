# extractor.py

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_and_chunk_text(text_generator):
    """
    Chunks text from a generator using LangChain's RecursiveCharacterTextSplitter.

    Args:
        text_generator: An iterable (like a generator) of text segments.

    Returns:
        list: A list of text chunks.
    """
    full_text = " ".join(text_generator)

    # Use a recursive text splitter which is good for general text.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.create_documents([full_text])
    chunk_texts = [chunk.page_content for chunk in chunks]
    return chunk_texts

