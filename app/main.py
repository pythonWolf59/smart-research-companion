from fastapi import FastAPI, File, UploadFile, Form
from contextlib import asynccontextmanager

from app.startup import ensure_model_ready
from app.pdf_parser import parse_pdf
from app.rag_qa import ask_question
from app.extractor import extract_insights
from app.chroma_handler import add_to_chroma, collection
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model once at startup
    model = ensure_model_ready()
    app.state.model = model
    yield
    # Add shutdown logic here if needed


app = FastAPI(title="Smart Research Assistant", lifespan=lifespan)


@app.post("/upload/")
async def upload_paper(file: UploadFile = File(...)):
    text = parse_pdf(file)
    doc_id = add_to_chroma(text)
    return {"doc_id": doc_id, "message": "PDF uploaded and indexed."}


@app.post("/ask/")
def question(doc_id: str = Form(...), question: str = Form(...)):
    answer = ask_question(doc_id, question)
    return {"answer": answer}


@app.get("/extract/")
def extract(doc_id: str):
    return extract_insights(doc_id)


@app.post("/citations/")
def get_citations(doc_id: str = Form(...), style: str = Form("APA")):
    # Fetch all docs from chroma collection
    results = collection.get()
    full_text = "\n".join(results['documents'])
    refs = extract_references(full_text)
    formatted = format_references(refs, style=style)
    return {"citations": formatted}


@app.get("/search_papers/")
def search_papers(query: str, max_results: int = 5):
    return search_all_sources(query, max_results)
