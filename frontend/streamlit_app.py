import streamlit as st
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# ✅ Step 1: Centralized base URL
BASE_URL = "https://smart-research-companion.onrender.com"

st.set_page_config(page_title="Smart Research Assistant", layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>🧠 Smart Research Assistant</h1>", unsafe_allow_html=True)
st.markdown("---")

# Initialize session state
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Home Section
with st.sidebar:
    menu = st.radio("Navigate", ["🏠 Home", "🔍 Search Papers", "📄 Upload & QA", "📚 Citation Manager"])

if menu == "🏠 Home":
    st.subheader("Welcome!")
    st.write("This tool helps you:")
    st.markdown("""
    - Upload research papers (PDF)
    - Ask questions from the paper
    - Extract research insights
    - Search from multiple sources
    - Generate citations in different styles
    """)

elif menu == "🔍 Search Papers":
    st.subheader("🔍 Search Research Papers")
    query = st.text_input("Enter your topic")

    if st.button("Search"):
        with st.spinner("Searching..."):
            try:
                res = requests.get(f"{BASE_URL}/search_papers/", params={"query": query, "max_results": 10})
                data = res.json()
                st.success("Papers fetched successfully!")

                for source, papers in data.items():
                    if not papers:
                        continue

                    st.markdown(f"## 🔹 Source: {source.capitalize()}")
                    for paper in papers:
                        st.markdown(f"**{paper['title']}**")
                        st.markdown(f"📝 *Summary:* {paper['summary'][:500]}...")
                        st.markdown(f"[🔗 View]({paper['url']})", unsafe_allow_html=True)
                        st.markdown("---")

            except Exception as e:
                st.error(f"Error: {e}")

elif menu == "📄 Upload & QA":
    st.subheader("📄 Upload PDF & Ask Questions")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="file_uploader_qa")

    if uploaded_file and st.button("Upload"):
        with st.spinner("Uploading and processing..."):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            try:
                res = requests.post(f"{BASE_URL}/upload/", files=files)
                result = res.json()
                st.session_state.doc_id = result.get("doc_id")
                st.session_state.chat_history = []
                st.success("Uploaded and indexed successfully.")
                st.code(f"Document ID: {st.session_state.doc_id}")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.doc_id:
        st.markdown("### 🤖 Interact with the Paper")
        col1, col2 = st.columns([1, 1])

        with col1:
            ask_clicked = st.button("💬 Ask Questions")
        with col2:
            extract_clicked = st.button("🧠 Extract Research Insights")

        if ask_clicked or st.session_state.get("show_chat", False):
            st.session_state.show_chat = True
            st.markdown("#### 💬 Chat with the AI")

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            user_query = st.chat_input("Ask something about the paper...")
            if user_query:
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.markdown(user_query)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            res = requests.post(f"{BASE_URL}/ask/", data={
                                "doc_id": st.session_state.doc_id,
                                "question": user_query
                            })
                            answer = res.json().get("answer", "No response")
                            st.markdown(answer)
                            st.session_state.chat_history.append({"role": "assistant", "content": answer})
                        except Exception as e:
                            st.error(f"Error: {e}")

            # ✅ Export Chat with ReportLab
            if st.session_state.chat_history:
                if st.button("📥 Export Chat as PDF"):
                    buffer = BytesIO()
                    c = canvas.Canvas(buffer, pagesize=letter)
                    textobject = c.beginText(40, 750)
                    textobject.setFont("Helvetica", 11)

                    for msg in st.session_state.chat_history:
                        lines = f"{msg['role'].capitalize()}: {msg['content']}".split("\n")
                        for line in lines:
                            textobject.textLine(line)
                        textobject.textLine("")  # Blank line between messages

                    c.drawText(textobject)
                    c.showPage()
                    c.save()
                    buffer.seek(0)

        # ✅ Extract Insights
        if extract_clicked:
            with st.spinner("Extracting insights..."):
                try:
                    res = requests.get(f"{BASE_URL}/extract/", params={"doc_id": st.session_state.doc_id})
                    info = res.json().get("extracted_info")
                    with st.expander("🔍 View Extracted Insights"):
                        st.markdown(info, unsafe_allow_html=True)

                    if st.button("📤 Export Insights as PDF"):
                        buffer = BytesIO()
                        c = canvas.Canvas(buffer, pagesize=letter)
                        text = info or "No insights found"
                        textobject = c.beginText(40, 750)
                        textobject.setFont("Helvetica", 11)

                        for line in text.split("\n"):
                            textobject.textLine(line)

                        c.drawText(textobject)
                        c.showPage()
                        c.save()
                        buffer.seek(0)

                        st.download_button("⬇️ Download Insights PDF", data=buffer, file_name="insights.pdf", mime="application/pdf")

                except Exception as e:
                    st.error(f"Error: {e}")

elif menu == "📚 Citation Manager":
    st.subheader("📚 Citation Manager")

    doc_id = st.text_input("Enter Document ID", value=st.session_state.doc_id or "")
    style = st.selectbox("Citation Style", ["APA", "BibTeX", "Chicago", "Harvard"])

    if st.button("Generate Citations"):
        with st.spinner("Formatting citations..."):
            try:
                res = requests.post(f"{BASE_URL}/citations/", data={
                    "doc_id": doc_id,
                    "style": style
                })
                citations = res.json().get("citations")
                st.markdown("### 📄 Formatted Citations")
                st.code(citations, language="text")

                if st.button("📤 Export Citations as .txt"):
                    citation_txt = BytesIO(citations.encode("utf-8"))
                    st.download_button("⬇️ Download Citations", data=citation_txt, file_name="citations.txt", mime="text/plain")

            except Exception as e:
                st.error(f"Error: {e}")
