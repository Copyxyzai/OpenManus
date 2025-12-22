import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("MANUS_OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

print("Checking SDK capabilities...")
if hasattr(client, "responses"):
    print("SDK supports client.responses!")
else:
    print("SDK does NOT support client.responses. Exiting.")
    exit()

print("\nTesting 'gpt-4o' with new Responses API...")
try:
    response = client.responses.create(
        model="gpt-4o",
        input="Hello, this is a test of the Responses API compatibility.",
    )
    print("Success! gpt-4o works with Responses API.")
    # Attempt to print output based on expected structure
    if hasattr(response, "output_text"):
        print(f"Output: {response.output_text}")
    else:
        print(f"Response object: {response}")
except Exception as e:
    print(f"Failed to use gpt-4o with Responses API: {e}")
