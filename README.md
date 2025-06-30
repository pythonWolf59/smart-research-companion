# 🧠 Local AI Research Assistant (FastAPI + Ollama + ChromaDB)

This project is a **fully local, offline-compatible AI research assistant** that allows you to:
- Upload and summarize research papers (PDF)
- Ask questions using Retrieval-Augmented Generation (RAG)
- Store document vectors in **ChromaDB**
- Run local LLMs like Mistral or Gemma using **Ollama**
- Serve via **FastAPI**
- (Optional) Interface with **Streamlit** frontend

---

## 🛠 Tech Stack

- **FastAPI** – for backend API
- **Ollama** – run LLMs locally (Mistral/Gemma/etc.)
- **ChromaDB** – vector database
- **PyMuPDF** – PDF text extraction
- **LlamaIndex** or **Haystack** – for document-based QA
- **Supabase** – for auth/data (optional)
- **Streamlit** – for optional frontend

---

## 📦 Project Structure

```bash
ai_research_assistant/
├── app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── models/
├── rag/
├── frontend/
├── ollama/
├── requirements.txt
└── README.md

---

# 🚀 Getting Started

1.  **Install Ollama & a Model**

    ```bash
    curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
    ollama run mistral
    ```

2.  **Install Python Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Run FastAPI App**

    ```bash
    uvicorn app.main:app --reload
    ```

4.  **(Optional) Run Streamlit UI**

    ```bash
    streamlit run frontend/streamlit_app.py
    ```

# 🧪 Features

* Local PDF summarization
* Vector store with ChromaDB
* FastAPI endpoints
* Local LLM integration
* Supabase user management
* Semantic search across docs
* Frontend dashboard (optional)

# 💡 Future Ideas

* Multi-file indexing
* Paper-to-slide converter
* Citation auto-extraction
* Academic question-answering bot

# ⚖️ License

MIT — free to use and extend.
