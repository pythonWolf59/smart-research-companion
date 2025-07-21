import streamlit as st
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE_URL = "https://smart-research-companion.onrender.com"
st.set_page_config(page_title="Smart Research Assistant", layout="wide")

# Initialize session state
st.session_state.setdefault("doc_titles", [])
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("show_chat", False)
st.session_state.setdefault("show_insights", False)
st.session_state.setdefault("selected_title", "")

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

# ========== SEARCH ==========
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
                        st.markdown(f"📜 *Summary:* {paper['summary'][:500]}...")
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
                st.session_state.doc_titles.clear()
                for file in uploaded_files:
                    files = {"file": (file.name, file, "application/pdf")}
                    res = requests.post(f"{BASE_URL}/upload/", files=files)
                    doc_title = res.json().get("doc_title")
                    if doc_title:
                        st.session_state.doc_titles.append(doc_title)
                st.session_state.chat_history.clear()
                st.success(f"Uploaded {len(st.session_state.doc_titles)} PDF(s) successfully.")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.doc_titles:
        st.session_state.selected_title = st.text_input(
            "Enter the title (first 5 words used during chunking):",
            value=st.session_state.selected_title
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💬 Ask Questions"):
                st.session_state.show_chat = True
        with col2:
            if st.button("🧠 Extract Research Insights"):
                st.session_state.show_insights = True

        # 💬 Chat Interface
        if st.session_state.show_chat:
            st.markdown("#### 💬 Chat with the AI")

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            user_query = st.chat_input("Ask something about the uploaded paper...")
            if user_query:
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.markdown(user_query)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            res = requests.post(f"{BASE_URL}/ask/", data={
                                "title": st.session_state.selected_title,
                                "question": user_query
                            })
                            print(st.session_state.selected_title)
                            answer = res.json().get("answer", "No response")
                            st.markdown(answer)
                            st.session_state.chat_history.append({"role": "assistant", "content": answer})
                        except Exception as e:
                            st.error(f"Error: {e}")

            if st.session_state.chat_history:
                if st.button("📅 Export Chat as PDF"):
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

        if st.session_state.show_insights:
            with st.spinner("Extracting insights..."):
                try:
                    res = requests.get(f"{BASE_URL}/extract/", params={"title": st.session_state.selected_title})
                    json_data = res.json()
                    print(res.text)
                    if "extracted_info" in json_data:
                        info = json_data["extracted_info"]
                        with st.expander("🔍 View Extracted Insights"):
                            st.markdown(info, unsafe_allow_html=True)

                        if st.button("📄 Export Insights as PDF"):
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
                    else:
                        st.warning("No insights found in the response.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ========== CITATION MANAGER ==========
elif menu == "📚 Citation Manager":
    st.subheader("📚 Citation Manager")

    selected_title = st.text_input("Enter document title (first 5 words):")
    style = st.selectbox("Citation Style", ["APA", "BibTeX", "Chicago", "Harvard"])

    if st.button("Generate Citations"):
        with st.spinner("Formatting citations..."):
            try:
                res = requests.post(f"{BASE_URL}/citations/", data={
                    "title": selected_title,
                    "style": style
                })
                citations = res.json().get("citations")
                st.markdown("### 📜 Formatted Citations")
                st.code(citations, language="text")

                if citations and st.button("📄 Export Citations as .txt"):
                    citation_txt = BytesIO(citations.encode("utf-8"))
                    st.download_button("⬇️ Download Citations", data=citation_txt, file_name="citations.txt", mime="text/plain")
            except Exception as e:
                st.error(f"Error: {e}")
