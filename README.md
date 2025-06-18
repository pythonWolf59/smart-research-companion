# 🧠 AI Research Assistant MVP

A smart, minimal AI-powered tool designed to help researchers, MS/PhD students, and academics save time during literature reviews by summarizing papers, finding relevant research, and generating citation formats.

---

## 🚀 Features (MVP)

### 📄 1. PDF Summarizer
- Upload a research paper (max 2MB, PDF).
- AI automatically extracts the key insights, highlighting:
  - Abstract
  - Methods
  - Findings
  - Limitations & future work

### 🔍 2. Research Topic to Paper Finder
- Enter a research topic (e.g., *"Applications of GANs in Medicine"*).
- The tool searches open-access research databases (like arXiv).
- Outputs:
  - Title
  - Summary
  - URL to full paper

### 🧾 3. Citation Formatter
- Generates citation formats:
  - BibTeX
  - APA
  - MLA
- Based on metadata or search results.

---

## 🛠️ Tech Stack

- **Platform**: Google Colab (interactive prototype)
- **Language**: Python
- **AI Model**: Gemini Pro (via Google Generative AI API)
- **PDF Parsing**: PyMuPDF (fitz)
- **Search Engine**: arXiv API

---

## 🔐 Setup

1. **Create Gemini API Key**
   - Visit: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   - Copy and save your API key securely.

2. **Run Notebook**
   - Open the Colab notebook.
   - Paste your API key when prompted.
   - Start using the tool with PDF uploads or research topics.

---

## 💡 Future Plans

- 🧾 Batch summarization of multiple papers
- 🧠 Chat with uploaded PDFs
- 🕵️‍♂️ Research trend analysis and topic evolution
- 🌐 Streamlit-based web interface

---

## 👨‍💻 Author
**Hamza** – Python Backend Engineer & ML Practitioner

---

## 📜 License
MIT License – Use, share, and contribute freely.
`
