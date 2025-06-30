from app.ollama_runner import call_phi
from app.chroma_handler import get_similar_chunks

def ask_question(doc_id, question):
    context = "\n".join(get_similar_chunks(question))
    prompt = f"Answer the following question based on the context:\n\nContext:\n{context}\n\nQuestion: {question}"
    return call_phi(prompt)
