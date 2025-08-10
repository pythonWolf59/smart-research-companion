from app.startup import mistral_api

def extract_references(text: str) -> list[str]:
    """
    Extract reference entries from the end of a research paper.
    """
    prompt = f"""
You are an AI trained to extract citations from academic texts.

Extract and list all references from the following research paper text.
Only include the references — no explanations or summaries.

Paper:
\"\"\"
{text}
\"\"\"

Output:
- Reference 1
- Reference 2
- ...
"""
    output = mistral_api(prompt)
    # Split output by lines or bullets
    references = [line.strip("-• \n") for line in output.strip().splitlines() if line.strip()]
    return references


def format_references(references: list[str], style: str = "APA") -> str:
    """
    Format references in the given style: APA or BibTeX.
    """
    
    style = style.upper()
    joined_refs = "\n".join(references)

    if style == "BIBTEX":
        prompt = f"""
You are a BibTeX generator.

Convert the following raw reference list into properly formatted BibTeX entries.

References:
\"\"\"
{joined_refs}
\"\"\"

Output:
"""
    else:  # default to APA
        prompt = f"""
You are an expert citation formatter.

Format the following references in {style} citation style.

References:
\"\"\"
{joined_refs}
\"\"\"

Output:
"""

    return mistral_api(prompt).strip()
