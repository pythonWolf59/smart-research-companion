from fastapi import FastAPI, File, UploadFile, Form, Query
from typing import List, Union

from app.pdf_parser import parse_pdf
from app.rag_qa import ask_question
from app.extractor import extract_insights
from app.chroma_handler import ChromaHandler, collection
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources

app = FastAPI(title="Smart Research Assistant")

chroma = ChromaHandler(collection)

@app.post("/upload/")
async def upload_paper(file: UploadFile = File(...)):
    contents = await file.read()
    text = parse_pdf(contents)
    doc_tag = chroma._generate_doc_tag(contents)
    chroma.add_document(text, doc_tag)
    return {"doc_id": doc_tag, "message": "PDF uploaded and indexed."}


@app.post("/upload_multiple/")
async def upload_multiple_pdfs(files: List[UploadFile] = File(...)):
    doc_ids = []
    for file in files:
        contents = await file.read()
        text = parse_pdf(contents)
        doc_tag = chroma._generate_doc_tag(contents)
        chroma.add_document(text, doc_tag)
        doc_ids.append(doc_tag)
    return {"doc_ids": doc_ids, "message": f"{len(doc_ids)} PDFs uploaded and indexed."}


@app.post("/ask/")
def question(doc_id: Union[str, List[str]] = Form(...), question: str = Form(...)):
    doc_ids = [doc_id] if isinstance(doc_id, str) else doc_id
    try:
        answer = ask_question(doc_ids, question)
        return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}


@app.get("/extract/")
def extract(doc_id: List[str] = Query(...)):
    try:
        insights = extract_insights(doc_id)  # accepts list[str]
        return insights
    except Exception as e:
        return {"error": str(e)}


@app.post("/citations/")
def get_citations(doc_id: str = Form(...), style: str = Form("APA")):
    try:
        results = collection.get(where={"doc_tag": doc_id})
        full_text = "\n".join(results['documents'])
        refs = extract_references(full_text)
        formatted = format_references(refs, style=style)
        return {"citations": formatted}
    except Exception as e:
        return {"error": str(e)}


@app.get("/search_papers/")
def search_papers(query: str, max_results: int = 5):
    return search_all_sources(query, max_results)
