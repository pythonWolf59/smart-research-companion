from app.chroma_handler import ChromaHandler, collection
from app.startup import mistral_api

chroma = ChromaHandler(collection)

def enforce_markdown_structure(text):
    required_fields = [
        "**Title**", "**Abstract**", "**Research Objectives or Questions**",
        "**Variables**", "**Constructs**", "**Relationships**", "**Gaps or Future Research Directions**"
    ]
    for field in required_fields:
        if field not in text:
            text += f"\n{field}: \n"
    return text.strip()

def extract_insights(doc_ids: list[str]):
    # Get top relevant chunks from all selected documents
    chunks = chroma.get_similar_chunks("research paper analysis", doc_tags=doc_ids)
    
    if not chunks:
        return {"extracted_info": "No relevant content found in the selected documents."}

    context = "\n".join(chunks)

    prompt = f"""
You are an expert academic assistant.

Your task is to extract structured information from multiple research papers using the exact markdown format below:

---
###**Title**:  
###**Abstract**:  
###**Research Objectives or Questions**:  
###**Variables** (only if it’s quantitative):  
###**Constructs** (only if it’s qualitative):  
###**Relationships** (between variables or constructs):  
###**Gaps or Future Research Directions**:
---

Below is a combined content sample from several research papers:

\"\"\" 
{context} 
\"\"\"

Now extract and summarize the required information as one coherent overview. Format it strictly using the markdown template above. End your response with: ### END
"""

    response = mistral_api(prompt)
    extracted = response.split("### END")[0].strip()
    extracted = enforce_markdown_structure(extracted)

    return {"extracted_info": extracted}
