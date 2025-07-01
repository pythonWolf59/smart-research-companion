import streamlit as st
import requests
import time

st.set_page_config(page_title="Smart Research Assistant", layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>🧠 Smart Research Assistant</h1>", unsafe_allow_html=True)
st.markdown("---")

# Initialize session state
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None

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
                res = requests.get("http://localhost:8000/search_papers/", params={"query": query, "max_results": 10})
                data = res.json()
                st.success("Papers fetched successfully!")

                for source, papers in data.items():
                    if not papers:
                        continue  # Skip empty sources

                    st.markdown(f"## 🔹 Source: {source.capitalize()}")
                    for paper in papers:
                        st.markdown(f"**{paper['title']}**")
                        st.markdown(f"[🔗 Read on Source]({paper['url']})")
                        st.markdown(f"📝 *Summary:* {paper['summary']}")
                        st.markdown("---")

            except Exception as e:
                st.error(f"Error: {e}")


elif menu == "📄 Upload & QA":
    st.subheader("📄 Upload PDF & Ask Questions")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file and st.button("Upload"):
        with st.spinner("Uploading and processing..."):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            try:
                res = requests.post("http://localhost:8000/upload/", files=files)
                result = res.json()
                st.session_state.doc_id = result.get("doc_id")
                st.success("Uploaded and indexed successfully.")
                st.code(f"Document ID: {st.session_state.doc_id}")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.doc_id:
        question = st.text_input("Ask a question about the paper")
        if st.button("Ask"):
            with st.spinner("Thinking..."):
                try:
                    res = requests.post("http://localhost:8000/ask/", data={
                        "doc_id": st.session_state.doc_id,
                        "question": question
                    })
                    st.markdown("**Answer:**")
                    st.write(res.json().get("answer"))
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.button("Extract Research Insights"):
            with st.spinner("Extracting insights..."):
                try:
                    res = requests.get("http://localhost:8000/extract/", params={"doc_id": st.session_state.doc_id})
                    info = res.json().get("extracted_info")
                    with st.expander("🔍 View Extracted Insights"):
                        st.markdown(info, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

elif menu == "📚 Citation Manager":
    st.subheader("📚 Citation Manager")

    doc_id = st.text_input("Enter Document ID", value=st.session_state.doc_id or "")
    style = st.selectbox("Citation Style", ["APA", "BibTeX", "Chicago", "Harvard"])

    if st.button("Generate Citations"):
        with st.spinner("Formatting citations..."):
            try:
                res = requests.post("http://localhost:8000/citations/", data={
                    "doc_id": doc_id,
                    "style": style
                })
                citations = res.json().get("citations")
                st.markdown("### 📄 Formatted Citations")
                st.code(citations, language="text")
            except Exception as e:
                st.error(f"Error: {e}")
