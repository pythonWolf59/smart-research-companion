from fastapi import FastAPI, File, UploadFile, Form

from app.pdf_parser import parse_pdf
from app.rag_qa import ask_question
from app.extractor import extract_insights
from app.chroma_handler import add_to_chroma, collection
from app.citation_manager import format_references, extract_references
from app.paper_search import search_all_sources


app = FastAPI(title="Smart Research Assistant")


@app.post("/upload/")
async def upload_paper(file: UploadFile = File(...)):
    # Step 1: Read and parse
    contents = await file.read()
    text = parse_pdf(contents)

    # Step 2: Use filename (or timestamp) as unique doc_tag
    doc_tag = file.filename.replace(" ", "_")  # Or use hash(contents)

    # Step 3: Add to Chroma with cleanup
    add_to_chroma(text, doc_tag=doc_tag)

    return {"doc_id": doc_tag, "message": "PDF uploaded and indexed."}



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
