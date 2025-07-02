# 🤖 Streamlined AI Research Assistant

An intelligent, cost-effective, and blazing-fast AI research assistant built with **FastAPI**, **Streamlit**, and **Mistral 8B API**, designed for extracting structured insights from academic papers, performing paper Q&A, citation formatting, and multi-source paper search.

> Powered by 🧠 [Mistral AI 8B Instruct](https://docs.mistral.ai) — fast, accurate, and affordable LLM.

---

## 🚀 Features

- ✅ **PDF Upload + Parsing**
  - Extracts text from academic PDFs
  - Automatically indexes content using ChromaDB for retrieval

- 🧠 **Context-Aware Question Answering**
  - Ask questions about the uploaded paper
  - Uses RAG (Retrieval Augmented Generation) for accurate answers

- 📄 **Insight Extraction**
  - Extracts structured research metadata:
    - Abstract
    - Research Objectives or Questions
    - Variables / Constructs
    - Relationships
    - Gaps & Future Directions
  - Output is formatted in **Markdown**

- 🔍 **Multi-Source Paper Search**
  - Searches papers from:
    - arXiv
    - PubMed
    - Semantic Scholar
    - CORE

- 🔖 **Citation Extraction & Formatting**
  - Automatically extracts references from papers
  - Supports formatting in:
    - APA
    - BibTeX

- 🖥️ **Streamlit Frontend**
  - Minimal, clean, and interactive research workflow UI

---

## 🧱 Tech Stack

| Layer       | Tool/Library        |
|------------|---------------------|
| Backend     | [FastAPI](https://fastapi.tiangolo.com) |
| LLM         | [Mistral 8B Instruct API](https://docs.mistral.ai) |
| RAG         | ChromaDB (local persistent vector store) |
| Frontend    | [Streamlit](https://streamlit.io) |
| PDF Parsing | PyMuPDF / pdfminer |
| Citation    | LLM-based formatting using Mistral |
| Paper Search| Official APIs / scraping from arXiv, PubMed, etc. |

---

---


# 🧪 Features

* Search downloadable PDF papers from multiple sources
* Upload Multiple PDF documents
* Extract insights from PDF
* Ask questions about uploaded document
* Generate citations in any format for your uploaded pdf

# 💡 Future Ideas

* Support .docx upload
* Generate Literature Review for uploaded paper
* Research Assistant Chatbot
* UI/UX Improvement
* _I am open to feedback and constructive criticism please write to me at humxazakir11@gmail.com for any suggestions or improvements._

# ⚖️ License

MIT — free to use and extend.
