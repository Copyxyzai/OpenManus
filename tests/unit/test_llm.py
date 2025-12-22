import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("MANUS_OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

print("Checking SDK capabilities...")
if hasattr(client, "responses"):
    print("SDK supports client.responses! (New API found)")
else:
    print("SDK does NOT support client.responses. (Standard API only)")

print("\nTesting model 'gpt-5.2' with standard ChatCompletion...")
try:
    response = client.chat.completions.create(
        model="gpt-5.2", messages=[{"role": "user", "content": "Hello"}], max_tokens=10
    )
    print("Success! Model exists.")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Failed to use gpt-5.2: {e}")

print("\nTesting baseline 'gpt-4o'...")
try:
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "Hello"}], max_tokens=10
    )
    print("Success with gpt-4o.")
except Exception as e:
    print(f"Failed to use gpt-4o: {e}")
