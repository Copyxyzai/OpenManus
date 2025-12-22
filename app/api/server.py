import asyncio
import warnings
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent.manus import Manus
from app.logger import logger

# Suppress Pydantic V2 warnings from dependencies
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2")
# Suppress Pydub warnings about ffmpeg
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv")


app = FastAPI(title="OpenManus API")


@app.get("/")
async def root():
    return {
        "message": "Welcome to OpenManus API",
        "endpoints": {
            "/chat": "POST - Chat with the agent",
            "/health": "GET - Check server status",
            "/docs": "GET - API documentation",
        },
    }


# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global agent instance to avoid re-initialization overhead
_agent: Optional[Manus] = None


async def get_agent():
    global _agent
    if _agent is None:
        logger.info("Initializing global Manus agent...")
        _agent = await Manus.create()
    return _agent


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    message: str
    success: bool


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Empty prompt")

    try:
        agent = await get_agent()
        logger.info(f"Processing request: {request.prompt}")

        # Run the agent
        result = await agent.run(request.prompt)

        return ChatResponse(message=str(result), success=True)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return ChatResponse(message=str(e), success=False)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
