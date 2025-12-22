import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

# Redirect output to file to ensure capture
sys.stdout = open("debug_output.txt", "w")
sys.stderr = sys.stdout

load_dotenv()
api_key = os.getenv("MANUS_OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

print("Starting debug...")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"},
]

print(f"1. Testing List input: {messages}")
try:
    response = client.responses.create(model="gpt-4o", input=messages)
    print("Success (List)!")
    print(response)
except Exception as e:
    print(f"Failed (List): {e}")

print("\n2. Testing String input: 'Hello'")
try:
    response = client.responses.create(model="gpt-4o", input="Hello")
    print("Success (String)!")
    if hasattr(response, "output_text"):
        print(f"Output: {response.output_text}")
    else:
        print(response)
except Exception as e:
    print(f"Failed (String): {e}")

print("Debug complete.")
