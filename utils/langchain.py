import openai
from dotenv import load_dotenv
import os
load_dotenv()


openai.api_key = os.getenv("OPENAI_API")

def process_message_with_langchain(message: str):
    response = openai.Completion.create(
        engine="text-davinci-003",  # или "gpt-3.5-turbo"
        prompt=message,
        max_tokens=100
    )
    return response.choices[0].text.strip()