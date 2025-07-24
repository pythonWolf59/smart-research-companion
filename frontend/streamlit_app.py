import streamlit as st
import requests
import json

# Base URL for the backend API
# IMPORTANT: For local testing, change this to "http://localhost:8000"
# For deployment, keep it as your deployed backend URL.
BASE_URL = "https://smart-research-companion.onrender.com"

# Set page configuration for a wider layout and title
st.set_page_config(layout="wide", page_title="ScholarChat")

# Custom CSS for styling to match the screenshots
st.markdown("""
<style>
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    .stApp {
        background-color: #f8f0fc; /* Light purple background */
    }
    .sidebar .sidebar-content {
        background-color: #e0d9ed; /* Slightly darker purple for sidebar */
        padding-top: 20px;
        border-radius: 10px;
    }
    .css-1d391kg { /* Streamlit's default sidebar padding */
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .css-1lcbmhc { /* Sidebar navigation text color */
        color: #4a217f;
    }
    .css-1lcbmhc:hover { /* Sidebar navigation hover color */
        color: #6a3abf;
    }
    .css-1lcbmhc.st-selected { /* Selected sidebar item */
        background-color: #c9bfe5;
        border-radius: 5px;
        color: #4a217f;
    }
    /* General button styling */
    .stButton>button {
        background-color: #6a3abf; /* Purple button */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4a217f; /* Darker purple on hover */
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #c9bfe5;
        padding: 10px;
    }
    .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #c9bfe5;
        padding: 10px;
    }
    .stFileUploader>div>div>button {
        background-color: #6a3abf;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stFileUploader>div>div>button:hover {
        background-color: #4a217f;
    }
    .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #c9bfe5;
        padding: 5px 10px;
    }
    /* Styles for the clickable cards on the Home page */
    .card-container {
        position: relative; /* Needed for absolute positioning of the button */
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 10px;
        transition: transform 0.2s ease-in-out;
        height: 180px; /* Fixed height for cards */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer; /* Indicate it's clickable */
    }
    .card-container:hover {
        transform: translateY(-5px);
    }
    .card-icon {
        font-size: 3em;
        color: #6a3abf;
        margin-bottom: 10px;
    }
    .card-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #4a217f;
        margin-bottom: 5px;
    }
    .card-description {
        font-size: 0.9em;
        color: #555;
    }
    /* Style for the transparent overlay button */
    /* This targets the specific button that overlays the card */
    /* Adjusting selector to be more robust for Streamlit button elements */
    .stColumn > div > div > div > button[data-testid="stButton"] {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0) !important; /* Make it transparent */
        color: rgba(0,0,0,0) !important; /* Hide label text */
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        z-index: 10; /* Ensure it's on top of the card content */
        cursor: pointer;
    }
    /* Ensure the parent column allows relative positioning for the button */
    .stColumn {
        position: relative;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #4a217f;
    }
    /* Chat message styling */
    .chat-message-container {
        display: flex;
        align-items: flex-start;
        margin-bottom: 10px;
        padding: 10px;
        border-radius: 10px;
        background-color: #ffffff; /* White background for chat bubbles */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chat-message-icon {
        font-size: 1.5em;
        margin-right: 10px;
        flex-shrink: 0;
    }
    .chat-message-content {
        flex-grow: 1;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for navigation and data
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'selected_title' not in st.session_state:
    st.session_state.selected_title = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'all_titles' not in st.session_state:
    st.session_state.all_titles = []
if 'last_selected_chat_paper' not in st.session_state:
    st.session_state.last_selected_chat_paper = None
if 'chat_mode' not in st.session_state: # New: Tracks if chat is with uploaded paper or URL
    st.session_state.chat_mode = 'uploaded_paper' # 'uploaded_paper' or 'url_paper'
if 'current_url_for_chat' not in st.session_state: # New: Stores the URL for URL-based chat
    st.session_state.current_url_for_chat = None


# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("<h2 class='st-emotion-cache-10o49x4'>ScholarChat</h2>", unsafe_allow_html=True)
    
    page_options = ["Home", "Search Papers", "Chat with Paper", "Extract Insights", "Generate Citations"]
    
    try:
        initial_page_index = page_options.index(st.session_state.page)
    except ValueError:
        initial_page_index = 0

    selection = st.radio(
        "Navigation",
        page_options,
        index=initial_page_index,
        key="main_navigation"
    )
    
    if selection != st.session_state.page:
        st.session_state.page = selection
        # Reset chat mode and URL when navigating away from Chat with Paper
        if st.session_state.page != 'Chat with Paper':
            st.session_state.chat_mode = 'uploaded_paper'
            st.session_state.current_url_for_chat = None
        st.rerun()

# --- Functions for API Calls ---

def fetch_all_titles():
    """Fetches all document titles from the backend."""
    try:
        res = requests.get(f"{BASE_URL}/get_all_titles/")
        res.raise_for_status()
        response_data = res.json()
        
        extracted_titles = []
        if isinstance(response_data, dict) and "titles" in response_data:
            titles_from_response = response_data["titles"]
            if isinstance(titles_from_response, list):
                extracted_titles = titles_from_response
            elif isinstance(titles_from_response, dict):
                extracted_titles = list(titles_from_response.values())
            else:
                st.error("Backend response for 'titles' was not a list or dictionary as expected.")
        else:
            st.error("Backend response for titles was not in the expected format (missing 'titles' key or not a dict).")
        
        st.session_state.all_titles = extracted_titles
        return response_data
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching titles: {e}")
        st.session_state.all_titles = []
        return {}

def search_papers(query, max_results=10):
    """Searches for papers based on a query."""
    try:
        with st.spinner("Searching for papers..."):
            res = requests.get(f"{BASE_URL}/search_papers/", params={"query": query, "max_results": max_results})
            res.raise_for_status()
            data = res.json()
            return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching papers: {e}")
        return {"arxiv": [], "semantic_scholar": [], "core": [], "pubmed": []} # Return expected structure

def upload_paper(file):
    """Uploads a paper to the backend."""
    try:
        files = {'file': (file.name, file.getvalue(), file.type)}
        with st.spinner("Uploading paper..."):
            res = requests.post(f"{BASE_URL}/upload/", files=files)
            res.raise_for_status()
            doc_title = res.json().get("doc_title")
            st.success(f"Paper '{doc_title}' uploaded successfully!")
            fetch_all_titles()
            return doc_title
    except requests.exceptions.RequestException as e:
        st.error(f"Error uploading paper: {e}")
        return None

def ask_question(title, question):
    """Asks a question about a selected paper (uploaded)."""
    if not title or title == "Select a paper" or not question:
        return "Please select a valid paper and enter a question."

    try:
        with st.spinner("Getting response..."):
            json_data = json.dumps({
                "title": title,
                "question": question
            })
            res = requests.post(url=f"{BASE_URL}/ask/", data=json_data, headers={"Content-Type": "application/json"})
            res.raise_for_status()
            response_data = res.json()
            return response_data.get("answer", "No answer received.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error asking question: {e}")
        # Log the full error for debugging
        return f"Error='{e}'"

def extract_insights(title):
    """Extracts insights from a selected paper (uploaded)."""
    try:
        with st.spinner("Extracting insights..."):
            res = requests.get(f"{BASE_URL}/extract/", params={"title": title})
            res.raise_for_status()
            json_data = res.json()
            return json_data
    except requests.exceptions.RequestException as e:
        st.error(f"Error extracting insights: {e}")
        return {"extracted_info": "Error extracting summary."} # Return expected structure

def generate_citations(title, style):
    """Generates citations for a selected paper in a given style."""
    try:
        json_data = json.dumps({
            "title": title,
            "style": style
        })
        with st.spinner(f"Generating citations in {style} style..."):
            res = requests.post(url=f"{BASE_URL}/citations/", data=json_data, headers={"Content-Type": "application/json"})
            res.raise_for_status()
            citation_data = res.json()
            return citation_data.get("citations", "No citation generated.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating citations: {e}")
        return "An error occurred while generating citations."

# --- NEW API CALL FUNCTIONS FOR URL-BASED CONTENT ---

def extract_from_url_backend(url: str):
    """
    Calls the backend to extract initial summary/insights from a document URL.
    """
    try:
        with st.spinner("Extracting content from URL..."):
            json_data = json.dumps({"url": url})
            res = requests.post(url=f"{BASE_URL}/extract_from_url/", data=json_data, headers={"Content-Type": "application/json"})
            res.raise_for_status()
            response_data = res.json()
            return response_data.get("summary", "No summary received from URL.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error extracting from URL: {e}")
        return f"Error: Failed to extract content from URL. {e}"

def ask_question_url_paper_backend(url: str, question: str):
    """
    Calls the backend to ask a question about a document at a given URL.
    """
    try:
        with st.spinner("Getting response from URL content..."):
            json_data = json.dumps({
                "url": url,
                "question": question
            })
            res = requests.post(url=f"{BASE_URL}/ask_url_paper/", data=json_data, headers={"Content-Type": "application/json"})
            res.raise_for_status()
            response_data = res.json()
            return response_data.get("answer", "No answer received from URL.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error asking question about URL: {e}")
        return f"Error: Failed to get answer for URL. {e}"


# --- Page Content ---

if st.session_state.page == 'Home':
    st.title("Welcome to ScholarChat")
    st.write("Your AI-powered research assistant.")

    col1, col2, col3, col4 = st.columns(4)

    # Function to create clickable cards for navigation
    def create_navigation_card(col, icon, title, description, target_page):
        with col:
            # Display the card's visual content using st.markdown
            st.markdown(f"""
                <div class="card-container">
                    <span class="card-icon">{icon}</span>
                    <div class="card-title">{title}</div>
                    <div class="card-description">{description}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Place a transparent Streamlit button over the card for click detection
            # The label is a single space to make the button visible for interaction,
            # but its content will be hidden by CSS.
            if st.button(
                label="Proceed ", # A single space as label
                key=f"home_card_button_{target_page}",
                use_container_width=True # Make button fill its column
            ):
                st.session_state.page = target_page
                st.rerun()

    create_navigation_card(col1, "🔍", "Search Papers", "Find academic papers from a vast database.", "Search Papers")
    create_navigation_card(col2, "💬", "Chat with Paper", "Upload a paper or start a conversation with a URL.", "Chat with Paper")
    create_navigation_card(col3, "💡", "Extract Insights", "Get key insights and summaries from research papers or URLs.", "Extract Insights")
    create_navigation_card(col4, "‟", "Generate Citations", "Create citations in various formats for your bibliography.", "Generate Citations")


elif st.session_state.page == 'Search Papers':
    st.title("Search Papers")
    st.write("Discover academic papers. This is a demo and does not perform a real search.")

    st.header("Paper Search")
    st.write("Enter keywords to find relevant academic literature.")

    search_query = st.text_input("e.g., 'machine learning in biology'", key="search_input")
    if st.button("🔍 Search", key="search_button"):
        if search_query:
            results = search_papers(search_query)
            if results:
                st.subheader("Search Results:")
                found_any_papers = False
                for source, papers in results.items():
                    if papers:
                        st.markdown(f"### From {source.replace('_', ' ').title()}:")
                        for i, paper in enumerate(papers):
                            st.markdown(f"**{i+1}. {paper.get('title', 'N/A')}**")
                            if paper.get('authors'):
                                st.write(f"Authors: {paper['authors']}")
                            if paper.get('year'):
                                st.write(f"Year: {paper['year']}")
                            if paper.get('summary'):
                                st.write(f"Abstract: {paper['summary']}")
                            elif paper.get('abstract'): # Sometimes abstract is used instead of summary
                                st.write(f"Abstract: {paper['abstract']}")
                            else:
                                st.write("Abstract: N/A")

                            if paper.get('url'):
                                st.markdown(f"[Read Paper]({paper['url']})")
                            st.markdown("---")
                            found_any_papers = True
                if not found_any_papers:
                    st.info("No search results found for your query across all sources.")
            else:
                st.info("No search results found or an error occurred.")
        else:
            st.warning("Please enter a search query.")
    else:
        st.info("Search results will appear here...")


elif st.session_state.page == 'Chat with Paper':
    st.title("Chat with Paper")
    st.write("Upload a paper, select an existing one, or provide a URL to start a conversation.")

    # Fetch titles when the page loads
    if not st.session_state.all_titles:
        fetch_all_titles()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Upload or Select Paper")
        uploaded_file = st.file_uploader("Upload Paper", type=["pdf", "txt"], key="chat_upload_file")
        if uploaded_file is not None:
            if st.button("Upload Selected Paper", key=f"process_upload_chat_{uploaded_file.name}"):
                doc_title = upload_paper(uploaded_file)
                if doc_title:
                    st.session_state.selected_title = doc_title
                    st.session_state.chat_history = [{"role": "bot", "content": f"Hello! Paper '{doc_title}' uploaded. How can I help you with it?"}]
                    st.session_state.chat_mode = 'uploaded_paper' # Set mode to uploaded paper
                    st.session_state.current_url_for_chat = None # Clear URL
                    st.rerun()
        else:
            st.info("Select a file above, then click 'Upload Selected Paper'.")

        titles_for_dropdown = ["Select a paper"] + st.session_state.all_titles
        
        selected_title_index = 0
        if st.session_state.selected_title and st.session_state.selected_title in titles_for_dropdown:
            selected_title_index = titles_for_dropdown.index(st.session_state.selected_title)

        current_selected_title_from_dropdown = st.selectbox(
            "Select an existing paper:",
            titles_for_dropdown,
            index=selected_title_index,
            key="paper_select_chat"
        )
        
        # Logic to handle dropdown selection changing the chat context
        if current_selected_title_from_dropdown != st.session_state.selected_title:
            st.session_state.selected_title = current_selected_title_from_dropdown
            if st.session_state.selected_title != "Select a paper":
                st.session_state.chat_history = [{"role": "bot", "content": f"You've selected '{st.session_state.selected_title}'. How can I help you with it?"}]
                st.session_state.chat_mode = 'uploaded_paper' # Set mode to uploaded paper
                st.session_state.current_url_for_chat = None # Clear URL
            else:
                st.session_state.chat_history = [{"role": "bot", "content": "Hello! Upload a paper or select one from the dropdown to start."}]
                st.session_state.chat_mode = 'uploaded_paper' # Default mode
                st.session_state.current_url_for_chat = None # Clear URL
            st.rerun()

        st.markdown("---")
        st.subheader("Chat with URL")
        url_input = st.text_input("Enter Document URL (PDF only):", key="chat_url_input")
        if st.button("Extract from URL", key="extract_from_url_chat_button"):
            if url_input:
                initial_summary = extract_from_url_backend(url_input)
                if "Error:" not in initial_summary:
                    st.session_state.selected_title = f"URL: {url_input}" # Indicate it's a URL
                    st.session_state.current_url_for_chat = url_input # Store the actual URL
                    st.session_state.chat_mode = 'url_paper' # Set chat mode to URL
                    st.session_state.chat_history = [{"role": "bot", "content": f"Content from URL '{url_input}' extracted. Here's an initial summary:\n\n{initial_summary}"}]
                    st.rerun()
                else:
                    st.error(initial_summary) # Display error from backend
            else:
                st.warning("Please enter a URL to extract content.")
        
    with col2:
        st.subheader("Conversation")
        chat_placeholder = st.container()
        with chat_placeholder:
            if not st.session_state.chat_history:
                st.markdown("""
                    <div class="chat-message-container">
                        <span class="chat-message-icon">🤖</span>
                        <div class="chat-message-content">Hello! Upload a paper, select one from the dropdown, or enter a URL to start.</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                for chat_message in st.session_state.chat_history:
                    icon = "👤" if chat_message["role"] == "user" else "🤖"
                    st.markdown(f"""
                        <div class="chat-message-container">
                            <span class="chat-message-icon">{icon}</span>
                            <div class="chat-message-content">{chat_message["content"]}</div>
                        </div>
                    """, unsafe_allow_html=True)

        user_query = st.text_input("Ask a question...", key="user_chat_input")
        if st.button("Send", key="send_chat_button"):
            if user_query:
                if st.session_state.chat_mode == 'uploaded_paper' and st.session_state.selected_title and st.session_state.selected_title != "Select a paper":
                    st.session_state.chat_history.append({"role": "user", "content": user_query})
                    with chat_placeholder:
                        icon = "👤"
                        st.markdown(f"""
                            <div class="chat-message-container">
                                <span class="chat-message-icon">{icon}</span>
                                <div class="chat-message-content">{user_query}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    answer = ask_question(st.session_state.selected_title, user_query)
                    st.session_state.chat_history.append({"role": "bot", "content": answer})
                    st.rerun()
                elif st.session_state.chat_mode == 'url_paper' and st.session_state.current_url_for_chat:
                    st.session_state.chat_history.append({"role": "user", "content": user_query})
                    with chat_placeholder:
                        icon = "👤"
                        st.markdown(f"""
                            <div class="chat-message-container">
                                <span class="chat-message-icon">{icon}</span>
                                <div class="chat-message-content">{user_query}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    answer = ask_question_url_paper_backend(st.session_state.current_url_for_chat, user_query)
                    st.session_state.chat_history.append({"role": "bot", "content": answer})
                    st.rerun()
                else:
                    st.warning("Please upload/select a paper or extract content from a URL first.")
            else:
                st.warning("Please enter a question.")


elif st.session_state.page == 'Extract Insights':
    st.title("Extract Insights")
    st.write("Upload a research paper, select an existing one, or provide a URL to automatically extract key insights and a summary.")

    st.header("Insight Extractor")
    col1, col2 = st.columns([1, 2])

    if not st.session_state.all_titles:
        fetch_all_titles()

    with col1:
        st.subheader("Upload or Select Paper")
        uploaded_file = st.file_uploader("Choose File", type=["pdf", "txt"], key="extract_upload_file")
        if uploaded_file is not None:
            if st.button("Upload Selected Paper", key=f"process_upload_extract_{uploaded_file.name}"):
                doc_title = upload_paper(uploaded_file)
                if doc_title:
                    st.session_state.selected_title = doc_title
                    st.success(f"Paper '{doc_title}' uploaded. You can now extract insights.")
                    st.rerun()
        else:
            st.info("Select a file above, then click 'Upload Selected Paper'.")

        titles_for_dropdown = ["Select a paper"] + st.session_state.all_titles
        
        selected_title_index = 0
        if st.session_state.selected_title and st.session_state.selected_title in titles_for_dropdown:
            selected_title_index = titles_for_dropdown.index(st.session_state.selected_title)

        selected_title_extract = st.selectbox(
            "Select an existing paper to extract insights from:",
            titles_for_dropdown,
            index=selected_title_index,
            key="paper_select_extract"
        )
        # Update session state if dropdown selection changes
        if selected_title_extract != st.session_state.selected_title:
            st.session_state.selected_title = selected_title_extract
            # No rerun here, as extraction is triggered by button click

        st.markdown("---")
        st.subheader("Extract from URL")
        url_input_extract = st.text_input("Enter Document URL (PDF only):", key="extract_url_input")
        if st.button("Extract Summary from URL", key="extract_from_url_extract_button"):
            if url_input_extract:
                summary_from_url = extract_from_url_backend(url_input_extract)
                with col2: # Display in the main content area
                    if "Error:" not in summary_from_url:
                        st.subheader("Extracted Summary from URL:")
                        st.markdown(summary_from_url)
                    else:
                        st.error(summary_from_url)
            else:
                st.warning("Please enter a URL to extract content.")

    with col2:
        insights_placeholder = st.empty()
        insights_placeholder.info("Extracted insights will appear here...")

        if st.button("💡 Extract Insights from Selected Paper", key="extract_button"):
            if st.session_state.selected_title and st.session_state.selected_title != "Select a paper":
                insights = extract_insights(st.session_state.selected_title)
                with insights_placeholder.container():
                    if insights and "extracted_info" in insights:
                        st.subheader("Extracted Insights from Paper:")
                        st.markdown(insights["extracted_info"]) # Render Markdown content
                    else:
                        st.info("No insights extracted or an error occurred.")
            else:
                insights_placeholder.warning("Please upload or select a paper (or use the URL option) to extract insights.")


elif st.session_state.page == 'Generate Citations':
    st.title("Generate Citations")
    st.write("Upload a paper and select a style to generate a citation.")

    st.header("Citation Generator")
    col1, col2, col3 = st.columns([1, 1, 1])

    if not st.session_state.all_titles:
        fetch_all_titles()

    with col1:
        uploaded_file = st.file_uploader("Choose File", type=["pdf", "txt"], key="citations_upload_file")
        if uploaded_file is not None:
            if st.button("Upload Selected Paper", key=f"process_upload_citations_{uploaded_file.name}"):
                doc_title = upload_paper(uploaded_file)
                if doc_title:
                    st.session_state.selected_title = doc_title
                    st.success(f"Paper '{doc_title}' uploaded. You can now generate citations.")
                    st.rerun()
        else:
            st.info("Select a file above, then click 'Upload Selected Paper'.")

    with col2:
        titles_for_dropdown = ["Select a paper"] + st.session_state.all_titles
        
        selected_title_index = 0
        if st.session_state.selected_title and st.session_state.selected_title in titles_for_dropdown:
            selected_title_index = titles_for_dropdown.index(st.session_state.selected_title)

        selected_title_citation = st.selectbox(
            "Select a paper:",
            titles_for_dropdown,
            index=selected_title_index,
            key="paper_select_citation"
        )
        if selected_title_citation != "Select a paper":
            st.session_state.selected_title = selected_title_citation

    with col3:
        citation_style = st.selectbox(
            "Select Style",
            ["APA", "MLA", "Chicago", "Harvard"], # Example styles
            key="citation_style_select"
        )

    citation_placeholder = st.empty()
    citation_placeholder.info("Generated citation will appear here...")

    if st.button("‟ Generate", key="generate_citation_button"):
        if st.session_state.selected_title and st.session_state.selected_title != "Select a paper" and citation_style:
            citation_text = generate_citations(st.session_state.selected_title, citation_style)
            with citation_placeholder.container():
                st.subheader("Generated Citation:")
                st.text_area("Citation:", value=citation_text, height=150, key="citation_output")
        else:
            citation_placeholder.warning("Please upload or select a paper and choose a citation style.")

