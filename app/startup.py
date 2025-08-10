import os
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
model = "ministral-8b-2410"

client = Mistral(api_key=api_key)

def mistral_api(prompt):
    chat_response = client.chat.complete(
    model= model,
    messages = [
        {
            "role": "system",
            "content":  "You are an expert academic assistant. Your task is to provide responses as per user request. You will strictly structure your response in Markdown format. End your response with: ### END",
            
            "role": "user",
            "content": f"{prompt}",
        },
    ]
    )

    return(chat_response.choices[0].message.content)