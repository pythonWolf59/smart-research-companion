from fastapi import FastAPI, File, UploadFile, Form, Query
from typing import List, Union

from app.pdf_parser import parse_pdf
from app.rag_qa import ask_question
from app.extractor import extract_insights
from app.chroma_handler import add_to_chroma, collection
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources

app = FastAPI(title="Smart Research Assistant")


@app.post("/upload/")
async def upload_paper(file: UploadFile = File(...)):
    text = parse_pdf(file)
    doc_id = add_to_chroma(text)
    return {"doc_id": doc_id, "message": "PDF uploaded and indexed."}


@app.post("/upload_multiple/")
async def upload_multiple_pdfs(files: List[UploadFile] = File(...)):
    doc_ids = []
    for file in files:
        text = parse_pdf(file)
        doc_id = add_to_chroma(text)
        doc_ids.append(doc_id)
    return {"doc_ids": doc_ids, "message": f"{len(doc_ids)} PDFs uploaded and indexed."}


@app.post("/ask/")
def question(doc_id: Union[str, List[str]] = Form(...), question: str = Form(...)):
    if isinstance(doc_id, str):
        doc_id = [doc_id]  # wrap single ID into list
    answers = []
    for did in doc_id:
        try:
            ans = ask_question(did, question)
            if ans:
                answers.append(ans)
        except Exception as e:
            answers.append(f"[Error for doc_id={did}]: {e}")
    final_answer = "\n\n".join(answers) if answers else "No response available."
    return {"answer": final_answer}  # ✅ Fixed to return dict


@app.get("/extract/")
def extract(doc_id: List[str] = Query(...)):
    insights_list = [extract_insights(did).get("extracted_info", "") for did in doc_id]
    return {"extracted_info": "\n\n".join(insights_list)}


@app.post("/citations/")
def get_citations(doc_id: str = Form(...), style: str = Form("APA")):
    results = collection.get()
    full_text = "\n".join(results['documents'])
    refs = extract_references(full_text)
    formatted = format_references(refs, style=style)
    return {"citations": formatted}


@app.get("/search_papers/")
def search_papers(query: str, max_results: int = 5):
    return search_all_sources(query, max_results)
