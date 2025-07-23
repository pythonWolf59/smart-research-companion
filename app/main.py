from fastapi import FastAPI, File, UploadFile, Form, Query, HTTPException
from typing import List, Union
import os
from pydantic import BaseModel

from fastapi.responses import JSONResponse

# Assuming these imports are correct and accessible
from app.pdf_parser import parse_pdf_pages_generator # Import the new generator function
from app.rag_qa import ask_question
from app.extractor import extract_insights
from app.chroma_handler import ChromaHandler, collection # Ensure 'collection' is imported correctly
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources

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
        except Exception as e:
            titles.append(f"Error processing {file.filename}: {e}")
    return {"doc_titles": titles, "message": f"{len(titles)} PDFs uploaded and indexed. Some may have failed."}

# --- Pydantic Models for JSON Request Bodies ---
class AskRequest(BaseModel):
    title: str
    question: str

class CitationRequest(BaseModel):
    title: str
    style: str = "APA"

# --- Updated Endpoints to accept JSON ---

@app.post("/ask/")
def question(request: AskRequest): 
    try:
        answer = ask_question(request.title, request.question)
        return {"answer": answer}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/extract/")
def extract(title: str = Query(...)):
    try:
        insights = extract_insights(title)
        if not isinstance(insights, dict) or "extracted_info" not in insights:
            insights = {"extracted_info": str(insights)}
        return JSONResponse(content=insights, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/citations/")
def get_citations(request: CitationRequest):
    try:
        results = collection.get(where={"doc_title": request.title})
        full_text = "\n".join(results['documents']) if results and 'documents' in results and results['documents'] else ""
        
        if not full_text:
            return JSONResponse(content={"citations": f"No content found for '{request.title}' to generate citations."}, status_code=200)

        refs = extract_references(full_text)
        formatted = format_references(refs, style=request.style)
        return JSONResponse(content={"citations": formatted}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/search_papers/")
def search_papers(query: str, max_results: int = 5):
    search_results = search_all_sources(query, max_results)
    return JSONResponse(content=search_results, status_code=200)


@app.get("/get_all_titles/")
def get_all_titles():
    try:
        results = collection.get(include=["metadatas"])
        metadatas = results["metadatas"]
        unique_titles = sorted(set(md["doc_title"] for md in metadatas if "doc_title" in md))

        return JSONResponse(content={"titles": unique_titles}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

