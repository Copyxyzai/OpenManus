import asyncio
import os

from browser_use import Agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


async def main():
    api_key = os.getenv("MANUS_OPENAI_API_KEY")
    if not api_key:
        print("API Key not found!")
        return

    llm = ChatOpenAI(model="gpt-4o", api_key=api_key)

    # Simple task to verify browser interaction
    agent = Agent(
        task="Go to google.com and search for 'OpenManus'",
        llm=llm,
    )

    print("Starting agent...")
    result = await agent.run()
    print("Agent finished")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
