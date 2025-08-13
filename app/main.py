# main.py
from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from typing import List, Union
import os
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import logging
import uuid
import psycopg2

# Configure logging for the FastAPI app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- New Imports for ChromaDB and LangChain ---
from app.chroma_handler import ChromaHandler
from app.extractor import extract_and_chunk_text
from app.pdf_parser import parse_pdf_pages_generator
from app.rag_qa import ask_question, get_mistral_embedding
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources
from app.extract_from_url import extract_initial_summary_from_url, ask_question_from_url
from app.startup import mistral_api as startup_mistral_api  # Renamed to avoid conflicts
from dotenv import load_dotenv

app = FastAPI(title="Scholar Chat AI")
load_dotenv()

# Initialize ChromaHandler globally
chroma_handler = ChromaHandler()


# --- Helper Functions (Updated) ---

def extract_title(file: UploadFile) -> str:
    filename = os.path.splitext(file.filename)[0]
    return filename


def get_full_document_text(title: str) -> str:
    """
    Retrieves the full text of a document from the database using ChromaHandler.
    """
    full_text_chunks = chroma_handler.get_all_chunks_for_document(title)
    if not full_text_chunks:
        raise HTTPException(status_code=404, detail=f"Document with title '{title}' not found.")

    return "\n".join(full_text_chunks)


def extract_insights(title: str) -> dict:
    """
    Extracts key insights from a document by retrieving its full text
    and using a Mistral API call.
    """
    full_text = get_full_document_text(title)
    prompt = f"""
You are an expert research assistant.
Read the following paper text and extract the key insights, findings, and contributions.
Format the output in markdown format

Paper text:
\"\"\"
{full_text}
\"\"\"

Output:
"""
    try:
        response = startup_mistral_api(prompt)
        return {"extracted_info": response}
    except Exception as e:
        logging.error(f"Error extracting insights from Mistral API: {e}")
        return {"extracted_info": "Failed to extract insights."}


# --- Pydantic Models for JSON Request Bodies ---
class AskRequest(BaseModel):
    title: str
    question: str


class CitationRequest(BaseModel):
    title: str
    style: str = "APA"


class UrlRequest(BaseModel):
    url: str
    question: Union[str, None] = None


# --- Re-implemented Endpoints (Updated) ---
@app.post("/upload/")
async def upload_paper(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        title = extract_title(file)

        # Use a generator to parse the PDF, then chunk the text with LangChain.
        text_generator = parse_pdf_pages_generator(contents)
        chunks = extract_and_chunk_text(text_generator)

        if not chunks:
            raise HTTPException(status_code=400, detail="Document could not be chunked or is empty.")

        # Get embeddings for all chunks from Mistral
        embeddings = [get_mistral_embedding(text) for text in chunks]

        # Add the chunks and embeddings to ChromaDB
        chroma_handler.add_chunks_with_embeddings_to_chroma(chunks, embeddings, title)

        return {"doc_title": title, "message": "PDF uploaded and indexed."}
    except Exception as e:
        logging.error(f"Error during PDF upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during upload: {e}")


@app.post("/upload_multiple/")
async def upload_multiple_pdfs(files: List[UploadFile] = File(...)):
    titles = []
    for file in files:
        try:
            contents = await file.read()
            title = extract_title(file)

            # Use a generator to parse the PDF, then chunk the text with LangChain.
            text_generator = parse_pdf_pages_generator(contents)
            chunks = extract_and_chunk_text(text_generator)

            if not chunks:
                logging.error(f"Error processing {file.filename}: Document could not be chunked or is empty.")
                titles.append(f"Error processing {file.filename}: Document could not be chunked or is empty.")
                continue

            # Get embeddings for all chunks from Mistral
            embeddings = [get_mistral_embedding(text) for text in chunks]

            # Add the chunks and embeddings to ChromaDB
            chroma_handler.add_chunks_with_embeddings_to_chroma(chunks, embeddings, title)

            titles.append(title)
        except Exception as e:
            titles.append(f"Error processing {file.filename}: {e}")
            logging.error(f"Error processing {file.filename}: {e}", exc_info=True)

    return {"doc_titles": titles, "message": f"{len(titles)} PDFs uploaded and indexed. Some may have failed."}


@app.post("/ask/")
def question(request: AskRequest):
    try:
        logging.info(f"Received question request for title '{request.title}': {request.question}")

        # Generate embedding for the query
        query_embedding = get_mistral_embedding(request.question)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding for the query.")

        # Search for similar chunks in ChromaDB
        context_chunks = chroma_handler.get_similar_chunks(query_embedding, doc_title=request.title)

        if not context_chunks:
            return JSONResponse(
                content={"answer": f"No relevant information found for the question in document '{request.title}'."},
                status_code=200)

        context_string = "\n".join(context_chunks)
        answer = ask_question(context_string, request.question)

        return {"answer": answer}
    except Exception as e:
        logging.error(f"Error asking question for title '{request.title}': {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/extract/")
def extract(title: str = Query(...)):
    """
    Extracts insights from a document and returns them in Markdown format.
    """
    try:
        logging.info(f"Received extract insights request for title: {title}")
        raw_response = extract_insights(title)
        return raw_response
    except Exception as e:
        logging.error(f"Error extracting insights for title '{title}': {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_all_titles/")
def get_all_titles():
    try:
        logging.info("Received request to get all document titles.")
        titles = chroma_handler.get_all_titles()
        return JSONResponse(content={"titles": sorted(titles)}, status_code=200)
    except Exception as e:
        logging.error(f"Error getting all titles: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/citations/")
def get_citations(request: CitationRequest):
    try:
        logging.info(f"Received citation request for title '{request.title}' in style: {request.style}")

        full_text_chunks = chroma_handler.get_all_chunks_for_document(request.title)

        if not full_text_chunks:
            return JSONResponse(content={"citations": f"No content found for '{request.title}' to generate citations."},
                                status_code=200)

        full_text = "\n".join(full_text_chunks)

        if not full_text:
            logging.warning(f"No content found for '{request.title}' to generate citations.")
            return JSONResponse(content={"citations": f"No content found for '{request.title}' to generate citations."},
                                status_code=200)

        refs = extract_references(full_text)
        formatted = format_references(refs, style=request.style)
        return JSONResponse(content={"citations": formatted}, status_code=200)
    except Exception as e:
        logging.error(f"Error generating citations for title '{request.title}': {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


# --- OLD ENDPOINTS (UNMODIFIED) ---
@app.get("/search_papers/")
def search_papers(query: str, max_results: int = 5):
    try:
        logging.info(f"Received paper search request for query: '{query}' with max_results: {max_results}")
        search_results = search_all_sources(query, max_results)
        return JSONResponse(content=search_results, status_code=200)
    except Exception as e:
        logging.error(f"Error searching papers for query '{query}': {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/extract_from_url/")
async def extract_url_content(request: UrlRequest):
    try:
        logging.info(f"Received request to extract from URL: {request.url}")
        summary = extract_initial_summary_from_url(request.url)
        if "Error:" in summary:
            raise HTTPException(status_code=500, detail=summary)
        return JSONResponse(content={"summary": summary}, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error extracting content from URL '{request.url}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract content from URL: {e}")


@app.post("/ask_url_paper/")
async def ask_question_url_paper(request: UrlRequest):
    if not request.url or not request.question:
        raise HTTPException(status_code=400, detail="URL and question are required.")

    try:
        logging.info(f"Received question '{request.question}' for URL: {request.url}")
        answer = ask_question_from_url(request.url, request.question)
        if "Error:" in answer:
            raise HTTPException(status_code=500, detail=answer)
        return JSONResponse(content={"answer": answer}, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error asking question about URL '{request.url}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get answer from URL: {e}")
