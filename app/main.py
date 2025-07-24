from fastapi import FastAPI, File, UploadFile, Form, Query, HTTPException
from typing import List, Union
import os
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import logging

# Configure logging for the FastAPI app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Assuming these imports are correct and accessible
from app.pdf_parser import parse_pdf_pages_generator # Import the new generator function
from app.rag_qa import ask_question
from app.extractor import extract_insights
from app.chroma_handler import ChromaHandler, collection # Ensure 'collection' is imported correctly
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources
# Import the new functions from the extract_from_url module
from app.extract_from_url import extract_initial_summary_from_url, ask_question_from_url

app = FastAPI(title="Smart Research Assistant")

chroma = ChromaHandler(collection)

def extract_title(file: UploadFile) -> str:
    filename = os.path.splitext(file.filename)[0]
    return filename

@app.post("/upload/")
async def upload_paper(file: UploadFile = File(...)):
    try:
        contents = await file.read() # Still read full file bytes to pass to fitz
        
        # Use the generator function to get page texts
        text_generator = parse_pdf_pages_generator(contents) 
        
        doc_tag = chroma._generate_doc_tag(contents)
        title = extract_title(file)
        
        # Pass the generator to add_document
        title_slug = chroma.add_document(text_generator, doc_tag, title) 
        return {"doc_title": title_slug, "message": "PDF uploaded and indexed."}
    except ValueError as ve:
        # Catch the specific ValueError from add_document (e.g., "Document too large...")
        raise HTTPException(status_code=413, detail=str(ve))
    except Exception as e:
        # Catch any other unexpected errors during upload/processing
        logging.error(f"Error during PDF upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during upload: {e}")


@app.post("/upload_multiple/")
async def upload_multiple_pdfs(files: List[UploadFile] = File(...)):
    titles = []
    for file in files:
        try:
            contents = await file.read()
            text_generator = parse_pdf_pages_generator(contents) # Use generator here too
            doc_tag = chroma._generate_doc_tag(contents)
            title = extract_title(file)
            title_slug = chroma.add_document(text_generator, doc_tag, title) # Pass generator
            titles.append(title_slug)
        except ValueError as ve:
            titles.append(f"Error processing {file.filename}: {ve}")
            logging.warning(f"ValueError processing {file.filename}: {ve}")
        except Exception as e:
            titles.append(f"Error processing {file.filename}: {e}")
            logging.error(f"Error processing {file.filename}: {e}", exc_info=True)
    return {"doc_titles": titles, "message": f"{len(titles)} PDFs uploaded and indexed. Some may have failed."}

# --- Pydantic Models for JSON Request Bodies ---
class AskRequest(BaseModel):
    title: str
    question: str

class CitationRequest(BaseModel):
    title: str
    style: str = "APA"

# New Pydantic model for URL requests
class UrlRequest(BaseModel):
    url: str
    question: Union[str, None] = None # Optional question for follow-up

# --- Updated Endpoints to accept JSON ---

@app.post("/ask/")
def question(request: AskRequest): 
    try:
        logging.info(f"Received question request for title '{request.title}': {request.question}")
        answer = ask_question(request.title, request.question)
        return {"answer": answer}
    except Exception as e:
        logging.error(f"Error asking question for title '{request.title}': {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/extract/")
def extract(title: str = Query(...)):
    try:
        logging.info(f"Received extract insights request for title: {title}")
        insights = extract_insights(title)
        if not isinstance(insights, dict) or "extracted_info" not in insights:
            insights = {"extracted_info": str(insights)}
        return JSONResponse(content=insights, status_code=200)
    except Exception as e:
        logging.error(f"Error extracting insights for title '{title}': {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/citations/")
def get_citations(request: CitationRequest):
    try:
        logging.info(f"Received citation request for title '{request.title}' in style: {request.style}")
        results = collection.get(where={"doc_title": request.title})
        full_text = "\n".join(results['documents']) if results and 'documents' in results and results['documents'] else ""
        
        if not full_text:
            logging.warning(f"No content found for '{request.title}' to generate citations.")
            return JSONResponse(content={"citations": f"No content found for '{request.title}' to generate citations."}, status_code=200)

        refs = extract_references(full_text)
        formatted = format_references(refs, style=request.style)
        return JSONResponse(content={"citations": formatted}, status_code=200)
    except Exception as e:
        logging.error(f"Error generating citations for title '{request.title}': {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/search_papers/")
def search_papers(query: str, max_results: int = 5):
    try:
        logging.info(f"Received paper search request for query: '{query}' with max_results: {max_results}")
        search_results = search_all_sources(query, max_results)
        return JSONResponse(content=search_results, status_code=200)
    except Exception as e:
        logging.error(f"Error searching papers for query '{query}': {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_all_titles/")
def get_all_titles():
    try:
        logging.info("Received request to get all document titles.")
        results = collection.get(include=["metadatas"])
        metadatas = results["metadatas"]
        unique_titles = sorted(set(md["doc_title"] for md in metadatas if "doc_title" in md))
        return JSONResponse(content={"titles": unique_titles}, status_code=200)
    except Exception as e:
        logging.error(f"Error getting all titles: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

# --- NEW ENDPOINTS FOR URL-BASED EXTRACTION AND Q&A ---

@app.post("/extract_from_url/")
async def extract_url_content(request: UrlRequest):
    """
    Endpoint to extract initial summary/insights from a document URL using Mistral AI.
    """
    try:
        logging.info(f"Received request to extract from URL: {request.url}")
        summary = extract_initial_summary_from_url(request.url)
        if "Error:" in summary: # Check for error messages returned by the helper
            raise HTTPException(status_code=500, detail=summary)
        return JSONResponse(content={"summary": summary}, status_code=200)
    except HTTPException as he:
        # Re-raise HTTPException to be handled by FastAPI's default handler
        raise he
    except Exception as e:
        logging.error(f"Error extracting content from URL '{request.url}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract content from URL: {e}")

@app.post("/ask_url_paper/")
async def ask_question_url_paper(request: UrlRequest):
    """
    Endpoint to ask a question about a document at a given URL using Mistral AI.
    Assumes `request.url` and `request.question` are provided.
    """
    if not request.url or not request.question:
        raise HTTPException(status_code=400, detail="URL and question are required.")
    
    try:
        logging.info(f"Received question '{request.question}' for URL: {request.url}")
        answer = ask_question_from_url(request.url, request.question)
        if "Error:" in answer: # Check for error messages returned by the helper
            raise HTTPException(status_code=500, detail=answer)
        return JSONResponse(content={"answer": answer}, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error asking question about URL '{request.url}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get answer from URL: {e}")

