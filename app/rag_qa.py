# rag_qa.py

import os
import requests
import json
from mistralai import Mistral
from app.startup import mistral_api
import os
from dotenv import load_dotenv

load_dotenv()

# Assuming you have a Mistral API key set as an environment variable
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("MISTRAL_API_KEY environment variable must be set.")

# Initialize the Mistral client globally for reusability
client = Mistral(api_key=api_key)


def get_mistral_embedding(text: str) -> list:
    """
    Generates a vector embedding for a given text using the Mistral API client.

    Args:
        text (str): The text to embed.

    Returns:
        list: The 1024-dimensional vector embedding.
    """
    try:
        embeddings_batch_response = client.embeddings.create(
            model="mistral-embed",
            inputs=[text]
        )
        return embeddings_batch_response.data[0].embedding
    except Exception as e:
        print(f"Error getting Mistral embedding: {e}")
        return None


def ask_question(context: str, question: str):
    """
    Answers a question by generating a response with the Mistral API.

    Args:
        context (str): The retrieved context from the vector store.
        question (str): The user's question.

    Returns:
        str: The AI-generated answer.
    """
    # Create the full prompt for the Mistral API
    prompt = f"Answer the following question based on the context:\n\nContext:\n{context}\n\nQuestion: {question}"

    # Use the client to make a chat completion API call
    try:
        chat_response = mistral_api(prompt)
        return chat_response
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        return f"Error calling Mistral API: {e}"