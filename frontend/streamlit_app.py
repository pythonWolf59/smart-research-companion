# Frontend for Smart Research Companion
import streamlit as st
import requests
from streamlit_option_menu import option_menu

st.set_page_config(page_title="AI Research Assistant", page_icon="🧠", layout="wide")

# --- Sidebar Navigation ---
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Search Papers", "Upload PDF & QA", "Citation Manager"],
        icons=["house", "search", "file-earmark-arrow-up", "bookmarks"],
        menu_icon="cast",
        default_index=0,
    )

# --- Header ---
st.markdown("""
    <style>
        .title {
            font-size: 2.5em;
            font-weight: bold;
            color: #4F8BF9;
            margin-bottom: 10px;
        }
        .section {
            padding: 1em;
            border-radius: 10px;
            background-color: #f5f7fa;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .paper-block {
            border-left: 4px solid #4F8BF9;
            padding: 1em;
            margin: 10px 0;
            background: white;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">AI Research Assistant 🧠</div>', unsafe_allow_html=True)

# --- Home ---
if selected == "Home":
    st.markdown("""
        Welcome to your local AI-powered Research Assistant.

        - 🔍 Search academic papers across arXiv, Semantic Scholar, CORE, and PubMed
        - 📚 Upload PDF and ask questions
        - 🔎 Extract research objectives, variables, and core ideas
        - 🔖 Generate citations in multiple styles
    """)

# --- Search Papers ---
elif selected == "Search Papers":
    st.subheader("🔍 Multi-Source Academic Search")
    query = st.text_input("Enter your research topic", placeholder="e.g. generative AI in medicine")
    search_btn = st.button("Search")

    if search_btn and query:
        with st.spinner("Searching papers across sources..."):
            try:
                response = requests.get("http://localhost:8000/search_papers/", params={"query": query, "max_results": 25})
                results = response.json()

                for source, papers in results.items():
                    st.markdown(f"### 🌐 {source.title()}")
                    for paper in papers:
                        with st.container():
                            st.markdown(f"""
                                <div class='paper-block'>
                                    <strong>{paper['title']}</strong><br>
                                    <a href="{paper['url']}" target="_blank">View Paper</a><br>
                                    <p style='color:#444'>{paper['summary'][:500]}...</p>
                                </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error fetching papers: {e}")

# --- Upload PDF and Ask Questions ---
elif selected == "Upload PDF & QA":
    st.subheader("📄 Upload PDF & Ask Questions")
    uploaded_file = st.file_uploader("Upload a research PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Uploading and processing PDF..."):
            files = {"file": uploaded_file.getvalue()}
            response = requests.post("http://localhost:8000/upload/", files=files)
            doc_id = response.json().get("doc_id")
            st.success("File uploaded and indexed.")

            st.markdown("---")
            st.subheader("💬 Ask a Question")
            question = st.text_input("Ask something about the uploaded paper")
            if st.button("Get Answer") and question:
                with st.spinner("Generating answer..."):
                    resp = requests.post("http://localhost:8000/ask/", data={"doc_id": doc_id, "question": question})
                    st.info(resp.json().get("answer"))

            st.markdown("---")
            st.subheader("🔍 Extract Research Insights")
            if st.button("Extract Info"):
                with st.spinner("Analyzing paper..."):
                    resp = requests.get(f"http://localhost:8000/extract/?doc_id={doc_id}")
                    st.success(resp.json().get("extracted_info"))

# --- Citation Manager ---
elif selected == "Citation Manager":
    st.subheader("🔖 Generate and Format Citations")
    title = st.text_input("Paper Title")
    authors = st.text_input("Authors (comma-separated)")
    year = st.text_input("Year")
    url = st.text_input("URL")
    style = st.selectbox("Citation Style", ["APA", "BibTeX", "Chicago"])

    if st.button("Generate Citation"):
        if style == "APA":
            authors_formatted = authors.split(",")[0] + (" et al." if "," in authors else "")
            citation = f"{authors_formatted} ({year}). {title}. {url}"
        elif style == "BibTeX":
            citation = f"""@article{{custom,
  title={{ {title} }},
  author={{ {authors.replace(',', ' and ')} }},
  year={{ {year} }},
  url={{ {url} }}
}}"""
        elif style == "Chicago":
            citation = f"{authors} ({year}). \"{title}.\" Accessed {year}. {url}"

        st.code(citation, language="text")
