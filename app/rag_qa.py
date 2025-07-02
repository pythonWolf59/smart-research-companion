# app/rag_qa.py
from app.chroma_handler import get_similar_chunks
from app.startup import mistral_api

def ask_question(doc_id, question):
    context = "\n".join(get_similar_chunks(question))
    prompt = f"Answer the following question based on the context:\n\nContext:\n{context}\n\nQuestion: {question}"
    return mistral_api(prompt)
