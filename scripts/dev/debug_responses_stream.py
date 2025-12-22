import asyncio
import os
import sys

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Redirect output to file
sys.stdout = open("debug_stream_output.txt", "w")
sys.stderr = sys.stdout

load_dotenv()
api_key = os.getenv("MANUS_OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)


async def test_stream():
    print("Starting streaming debug...")
    try:
        response = await client.responses.create(
            model="gpt-4o", input="Count to 3", stream=True
        )
        print("Response object created. Iterating...")

        async for chunk in response:
            print(f"Chunk type: {type(chunk)}")
            print(f"Chunk dir: {dir(chunk)}")
            print(f"Chunk raw: {chunk}")

            # Simulate my current logic to see if it works
            chunk_message = ""
            if hasattr(chunk, "delta") and hasattr(chunk.delta, "content"):
                print("Found chunk.delta.content")
            elif hasattr(chunk, "output_text_delta"):
                print("Found chunk.output_text_delta")

            # Stop after a few chunks to avoid huge logs
            # break # Actually let's see a few to be sure

    except Exception as e:
        print(f"Streaming failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_stream())
