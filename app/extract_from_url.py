from mistralai import Mistral
import logging
from app.startup import client  # Assuming client is initialized in startup.py

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


MODEL_NAME = "mistral-small-latest" # As per your example

def _call_mistral_chat_api(messages: list[dict]) -> str:
    """
    Helper function to call the Mistral AI chat completion API.
    """
    if not client:
        return "Error: Mistral AI client not initialized. MISTRAL_API_KEY might be missing."

    try:
        logging.info(f"Calling Mistral AI with messages: {messages}")
        chat_response = client.chat.complete(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.0 # Keep temperature low for factual extraction
        )
        content = chat_response.choices[0].message.content
        logging.info(f"Mistral AI response: {content}")
        return content
    except Exception as e:
        logging.error(f"Error calling Mistral AI API: {e}")
        return f"An error occurred while communicating with Mistral AI: {e}"

def extract_initial_summary_from_url(url: str) -> str:
    """
    Extracts an initial summary or key information from a document at a given URL
    using Mistral AI's Document QnA capability.
    """
    if not url:
        return "Error: URL cannot be empty."

    logging.info(f"Attempting to extract initial summary from URL: {url}")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Please provide a concise summary and key insights from this document."},
                {"type": "document_url", "document_url": url}
            ]
        }
    ]
    return _call_mistral_chat_api(messages)

def ask_question_from_url(url: str, question: str) -> str:
    """
    Asks a question about the content of a document at a given URL
    using Mistral AI's Document QnA capability.
    """
    if not url or not question:
        return "Error: URL and question cannot be empty."

    logging.info(f"Asking question '{question}' about URL: {url}")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "document_url", "document_url": url}
            ]
        }
    ]
    return _call_mistral_chat_api(messages)

