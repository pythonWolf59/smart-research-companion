from app.chroma_handler import ChromaHandler, collection
from app.startup import mistral_api

chroma = ChromaHandler(collection)

def ask_question(doc_title: str, question: str):
    chunks = chroma.get_similar_chunks(question, title_slug=doc_title)
    context = "\n".join(chunks["chunks"])
    prompt = f"Answer the following question based on the context:\n\nContext:\n{context}\n\nQuestion: {question}"
    return mistral_api(prompt)
