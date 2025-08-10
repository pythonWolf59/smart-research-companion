# main.py (Updated with new extract_insights logic)

from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from typing import List, Union
import os
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import logging
import uuid
import requests
import json
import numpy as np

# Configure logging for the FastAPI app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Assuming these imports are correct and accessible
from app.pdf_parser import parse_pdf_pages_generator
from app.rag_qa import ask_question, get_mistral_embedding
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources
from app.extract_from_url import extract_initial_summary_from_url, ask_question_from_url
from app.pgvector_handler import PGVectorHandler
from app.startup import mistral_api  # Now also import the API function for insights

app = FastAPI(title="Smart Research Assistant")


# --- Helper Functions for Database and API Interaction ---

def get_db_handler():
    """
    Creates and returns a new PGVectorHandler instance.
    """
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if not all([db_host, db_user, db_password]):
        raise HTTPException(status_code=500, detail="Database credentials are not set in environment variables.")

    return PGVectorHandler(db_host=db_host, db_user=db_user, db_password=db_password)


def extract_title(file: UploadFile) -> str:
    filename = os.path.splitext(file.filename)[0]
    return filename


def get_full_document_text(title: str) -> str:
    """
    Retrieves the full text of a document from the database.
    """
    db_handler = get_db_handler()
    doc_id = db_handler.get_document_id_by_title(title)
    if not doc_id:
        db_handler.close()
        raise HTTPException(status_code=404, detail=f"Document with title '{title}' not found.")

    full_text_chunks = db_handler.get_all_chunks_for_document(doc_id)
    db_handler.close()
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
        response = mistral_api(prompt)
        # Assuming the API returns a clean JSON string
        return response
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


# --- Re-implemented Endpoints ---

@app.post("/upload/")
async def upload_paper(file: UploadFile = File(...)):
    try:
        db_handler = get_db_handler()

        contents = await file.read()
        title = extract_title(file)
        doc_tag = str(uuid.uuid4())

        doc_id = db_handler.add_document_metadata(doc_tag, title)

        text_generator = parse_pdf_pages_generator(contents)
        chunk_texts = [page_text for page_text in text_generator]

        embeddings = [get_mistral_embedding(text) for text in chunk_texts]

        db_handler.add_chunks_with_embeddings(chunk_texts, embeddings, doc_id)
        db_handler.close()

        return {"doc_title": title, "message": "PDF uploaded and indexed."}
    except Exception as e:
        logging.error(f"Error during PDF upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during upload: {e}")


@app.post("/upload_multiple/")
async def upload_multiple_pdfs(files: List[UploadFile] = File(...)):
    titles = []
    db_handler = get_db_handler()
    for file in files:
        try:
            contents = await file.read()
            title = extract_title(file)
            doc_tag = str(uuid.uuid4())

            doc_id = db_handler.add_document_metadata(doc_tag, title)

            text_generator = parse_pdf_pages_generator(contents)
            chunk_texts = [page_text for page_text in text_generator]
            embeddings = [get_mistral_embedding(text) for text in chunk_texts]
            db_handler.add_chunks_with_embeddings(chunk_texts, embeddings, doc_id)
            titles.append(title)
        except Exception as e:
            titles.append(f"Error processing {file.filename}: {e}")
            logging.error(f"Error processing {file.filename}: {e}", exc_info=True)
    db_handler.close()
    return {"doc_titles": titles, "message": f"{len(titles)} PDFs uploaded and indexed. Some may have failed."}


@app.post("/ask/")
def question(request: AskRequest):
    try:
        logging.info(f"Received question request for title '{request.title}': {request.question}")
        db_handler = get_db_handler()

        doc_id = db_handler.get_document_id_by_title(request.title)
        if not doc_id:
            db_handler.close()
            raise HTTPException(status_code=404, detail=f"Document with title '{request.title}' not found.")

        query_embedding = get_mistral_embedding(request.question)
        if not query_embedding:
            db_handler.close()
            raise HTTPException(status_code=500, detail="Failed to generate embedding for the query.")

        context_chunks = db_handler.search_similar_chunks(query_embedding, doc_id=doc_id)
        db_handler.close()

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

        # Call the function to get the raw response from Mistral AI
        raw_response = extract_insights(title)

        return raw_response

    except Exception as e:
        logging.error(f"Error extracting insights for title '{title}': {e}", exc_info=True)


@app.get("/get_all_titles/")
def get_all_titles():
    try:
        logging.info("Received request to get all document titles.")
        db_handler = get_db_handler()
        titles = db_handler.get_all_document_titles()
        db_handler.close()
        return JSONResponse(content={"titles": sorted(titles)}, status_code=200)
    except Exception as e:
        logging.error(f"Error getting all titles: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/citations/")
def get_citations(request: CitationRequest):
    try:
        logging.info(f"Received citation request for title '{request.title}' in style: {request.style}")
        db_handler = get_db_handler()

        doc_id = db_handler.get_document_id_by_title(request.title)
        if not doc_id:
            db_handler.close()
            return JSONResponse(content={"citations": f"No content found for '{request.title}' to generate citations."},
                                status_code=200)

        full_text_chunks = db_handler.get_all_chunks_for_document(doc_id)
        db_handler.close()
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
