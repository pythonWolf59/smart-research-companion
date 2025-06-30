import re

# Basic regex to detect reference-like patterns (you can improve this later)
REFERENCE_REGEX = r"(.*?)\.\s\((\d{4})\)\.\s(.*?)(?:\.|\?|!)\s(.+?)(?:\n|$)"

def extract_references(text: str):
    """
    Extracts references from raw text using regex.
    Returns list of dicts with 'authors', 'year', 'title', 'source'.
    """
    references = []
    for match in re.finditer(REFERENCE_REGEX, text):
        authors, year, title, source = match.groups()
        references.append({
            "authors": authors.strip(),
            "year": year.strip(),
            "title": title.strip(),
            "source": source.strip()
        })
    return references


def format_apa(ref):
    return f"{ref['authors']} ({ref['year']}). {ref['title']}. {ref['source']}"

def format_mla(ref):
    return f"{ref['authors']}. \"{ref['title']}.\" {ref['source']}, {ref['year']}."

def format_chicago(ref):
    return f"{ref['authors']}. \"{ref['title']}.\" {ref['source']}, {ref['year']}."

def format_bibtex(ref, i):
    return f"""@article{{ref{i},
  title={{ {ref['title']} }},
  author={{ {ref['authors']} }},
  journal={{ {ref['source']} }},
  year={{ {ref['year']} }}
}}"""

def format_references(refs, style="APA"):
    formatter = {
        "APA": format_apa,
        "MLA": format_mla,
        "Chicago": format_chicago,
        "BibTeX": lambda ref, i: format_bibtex(ref, i)
    }[style]

    if style == "BibTeX":
        return "\n\n".join([formatter(r, i) for i, r in enumerate(refs)])
    return "\n\n".join([formatter(r) for r in refs])
