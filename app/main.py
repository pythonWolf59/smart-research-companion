from fastapi import FastAPI, File, UploadFile, Form, Query
from typing import List, Union
import os

from app.pdf_parser import parse_pdf
from app.rag_qa import ask_question
from app.extractor import extract_insights
from app.chroma_handler import ChromaHandler, collection
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources

app = FastAPI(title="Smart Research Assistant")

chroma = ChromaHandler(collection)

def extract_title(file: UploadFile) -> str:
    filename = os.path.splitext(file.filename)[0]
    return filename

@app.post("/upload/")
async def upload_paper(file: UploadFile = File(...)):
    contents = await file.read()
    text = parse_pdf(contents)
    doc_tag = chroma._generate_doc_tag(contents)
    title = extract_title(file)
    title_slug = chroma.add_document(text, doc_tag, title)
    return {"doc_title": title_slug, "message": "PDF uploaded and indexed."}

@app.post("/upload_multiple/")
async def upload_multiple_pdfs(files: List[UploadFile] = File(...)):
    titles = []
    for file in files:
        contents = await file.read()
        text = parse_pdf(contents)
        doc_tag = chroma._generate_doc_tag(contents)
        title = extract_title(file)
        title_slug = chroma.add_document(text, doc_tag, title)
        titles.append(title_slug)
    return {"doc_titles": titles, "message": f"{len(titles)} PDFs uploaded and indexed."}

@app.post("/ask/")
def question(doc_title: str = Form(...), question: str = Form(...)):
    try:
        answer = ask_question(doc_title, question)
        return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}

@app.get("/extract/")
def extract(doc_title: str = Query(...)):
    try:
        insights = extract_insights(doc_title)
        return insights
    except Exception as e:
        return {"error": str(e)}

@app.post("/citations/")
def get_citations(doc_title: str = Form(...), style: str = Form("APA")):
    try:
        results = collection.get(where={"doc_title": doc_title})
        full_text = "\n".join(results['documents'])
        refs = extract_references(full_text)
        formatted = format_references(refs, style=style)
        return {"citations": formatted}
    except Exception as e:
        return {"error": str(e)}

@app.get("/search_papers/")
def search_papers(query: str, max_results: int = 5):
    return search_all_sources(query, max_results)
