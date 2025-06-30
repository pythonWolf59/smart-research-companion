from app.ollama_runner import call_phi
from app.chroma_handler import get_similar_chunks

def extract_insights(doc_id):
    context = "\n".join(get_similar_chunks("research paper analysis"))
    prompt = f"""
Given the following research paper excerpt, extract:
- Research Objectives
- Research Questions
- Constructs/Variables
- Relationships
- Core Idea

Text:
{context}

Respond in bullet points with headings.
"""
    return {"extracted_info": call_phi(prompt)}
