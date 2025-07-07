import streamlit as st
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE_URL = "https://smart-research-companion.onrender.com"
st.set_page_config(page_title="Smart Research Assistant", layout="wide")

# Initialize session state
st.session_state.setdefault("doc_ids", [])
st.session_state.setdefault("chat_history", [])

# UI Layout
st.markdown("<h1 style='text-align: center;'>🧠 Smart Research Assistant</h1>", unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    menu = st.radio("Navigate", ["🏠 Home", "🔍 Search Papers", "📄 Upload & QA", "📚 Citation Manager"])

# ========== HOME ==========
if menu == "🏠 Home":
    st.subheader("Welcome!")
    st.markdown("""
    - Upload multiple research papers (PDF)
    - Ask questions from all papers
    - Extract research insights from all
    - Search from multiple sources
    - Generate citations in different styles
    """)

# ========== SEARCH PAPERS ==========
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

# ========== UPLOAD & QA ==========
elif menu == "📄 Upload & QA":
    st.subheader("📄 Upload PDF(s) & Interact")

    uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

    if uploaded_files and st.button("Upload"):
        with st.spinner("Uploading and indexing..."):
            try:
                st.session_state.doc_ids.clear()
                for file in uploaded_files:
                    files = {"file": (file.name, file, "application/pdf")}
                    res = requests.post(f"{BASE_URL}/upload/", files=files)
                    doc_id = res.json().get("doc_id")
                    if doc_id:
                        st.session_state.doc_ids.append(doc_id)
                st.session_state.chat_history.clear()
                st.success(f"Uploaded {len(st.session_state.doc_ids)} PDF(s) successfully.")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.doc_ids:
        col1, col2 = st.columns([1, 1])
        with col1:
            ask_clicked = st.button("💬 Ask Questions")
        with col2:
            extract_clicked = st.button("🧠 Extract Research Insights")

        # 🔸 Chat Interface
        if ask_clicked or st.session_state.get("show_chat", False):
            st.session_state.show_chat = True
            st.markdown("#### 💬 Chat with the AI")

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            user_query = st.chat_input("Ask something about the uploaded papers...")
            if user_query:
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.markdown(user_query)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            res = requests.post(f"{BASE_URL}/ask/", data={
                                "doc_id": st.session_state.doc_ids,
                                "question": user_query
                            })
                            answer = res.json().get("answer", "No response")
                            st.markdown(answer)
                            st.session_state.chat_history.append({"role": "assistant", "content": answer})
                        except Exception as e:
                            st.error(f"Error: {e}")

            if st.session_state.chat_history:
                if st.button("📥 Export Chat as PDF"):
                    buffer = BytesIO()
                    c = canvas.Canvas(buffer, pagesize=letter)
                    textobject = c.beginText(40, 750)
                    textobject.setFont("Helvetica", 11)

                    for msg in st.session_state.chat_history:
                        for line in f"{msg['role'].capitalize()}: {msg['content']}".split("\n"):
                            textobject.textLine(line)
                        textobject.textLine("")
                    c.drawText(textobject)
                    c.showPage()
                    c.save()
                    buffer.seek(0)
                    st.download_button("⬇️ Download Chat PDF", data=buffer, file_name="chat_history.pdf", mime="application/pdf")

        # 🔸 Insights Interface
        if extract_clicked:
            with st.spinner("Extracting insights from all PDFs..."):
                try:
                    # ✅ Properly pass multiple doc_id as query params
                    res = requests.get(f"{BASE_URL}/extract/", params=[("doc_id", doc_id) for doc_id in st.session_state.doc_ids])
                    info = res.json().get("extracted_info")
                    with st.expander("🔍 View Extracted Insights"):
                        st.markdown(info, unsafe_allow_html=True)

                    if st.button("📤 Export Insights as PDF"):
                        buffer = BytesIO()
                        c = canvas.Canvas(buffer, pagesize=letter)
                        textobject = c.beginText(40, 750)
                        textobject.setFont("Helvetica", 11)

                        for line in info.split("\n"):
                            textobject.textLine(line)

                        c.drawText(textobject)
                        c.showPage()
                        c.save()
                        buffer.seek(0)

                        st.download_button("⬇️ Download Insights PDF", data=buffer, file_name="insights.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Error: {e}")

# ========== CITATION MANAGER ==========
elif menu == "📚 Citation Manager":
    st.subheader("📚 Citation Manager")

    doc_id = st.text_input("Enter Document ID", value=st.session_state.doc_ids[0] if st.session_state.doc_ids else "")
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

                if citations and st.button("📤 Export Citations as .txt"):
                    citation_txt = BytesIO(citations.encode("utf-8"))
                    st.download_button("⬇️ Download Citations", data=citation_txt, file_name="citations.txt", mime="text/plain")
            except Exception as e:
                st.error(f"Error: {e}")
