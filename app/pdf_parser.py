# app/pdf_parser.py
import fitz  # PyMuPDF

def parse_pdf_pages_generator(pdf_bytes: bytes):
    """
    Parses a PDF from bytes and yields text content page by page.
    This avoids holding the entire document's text in memory at once.
    """
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            yield page.get_text()
    finally:
        if doc:
            doc.close() # Ensure the document is closed even if an error occurs

