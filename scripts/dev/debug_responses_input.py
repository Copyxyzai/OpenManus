import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("MANUS_OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"},
]

print(f"Testing client.responses with list input: {messages}")
try:
    response = client.responses.create(model="gpt-4o", input=messages)
    print("Success!")
    print(response)
except Exception as e:
    print(f"Failed: {e}")
