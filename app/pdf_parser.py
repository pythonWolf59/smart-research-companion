import fitz  # PyMuPDF

def parse_pdf(file):
    doc = fitz.open(stream=file.file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    return text
