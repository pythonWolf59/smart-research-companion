from app.chroma_handler import get_similar_chunks
from app.startup import get_model

def enforce_markdown_structure(text):
    required_fields = [
        "**Title**", "**Abstract**", "**Research Objectives or Questions**",
        "**Variables**", "**Constructs**", "**Relationships**", "**Gaps or Future Research Directions**"
    ]
    for field in required_fields:
        if field not in text:
            text += f"\n{field}: \n"
    return text.strip()

def extract_insights(doc_id):
    context = "\n".join(get_similar_chunks("research paper analysis"))

    prompt = f"""
You are an expert academic assistant.

Your task is to extract structured information from an academic research paper using the exact markdown format below:

---
###**Title**:  
###**Abstract**:  
###**Research Objectives or Questions**:  
###**Variables** (only if it’s quantitative):  
###**Constructs** (only if it’s qualitative):  
###**Relationships** (between variables or constructs):  
###**Gaps or Future Research Directions**:
---

Below is the content of the research paper:

\"\"\" 
{context} 
\"\"\"

Now extract the required information from the paper and format it strictly using the markdown template above. Fill in all sections where applicable. End your response with: ### END
"""

    model = get_model()
    response = model.generate(
        prompt=prompt,
        max_tokens=4096
    )

    extracted = response.split("### END")[0].strip()
    extracted = enforce_markdown_structure(extracted)

    return {"extracted_info": extracted}
