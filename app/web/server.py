"""Minimal FastAPI server exposing the Manus agent over HTTP."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "Pydantic is required to run the OpenManus web server. Install it with "
        "'pip install pydantic' or via 'pip install -r requirements.txt'."
    ) from exc

from app.agent.manus import Manus
from app.logger import logger

try:  # pragma: no cover - exercised during runtime import
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, Response
    from fastapi.staticfiles import StaticFiles
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    FastAPI = None  # type: ignore[assignment]
    CORSMiddleware = None  # type: ignore[assignment]
    FileResponse = None  # type: ignore[assignment]
    Response = None  # type: ignore[assignment]
    StaticFiles = None  # type: ignore[assignment]

    class HTTPException(Exception):  # type: ignore[override]
        """Fallback HTTPException when FastAPI is unavailable."""

        def __init__(self, status_code: int, detail: str | None = None) -> None:
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail or f"HTTP {status_code}")

    FASTAPI_IMPORT_ERROR: ModuleNotFoundError | None = exc
else:
    FASTAPI_IMPORT_ERROR = None


STATIC_DIR = Path(__file__).resolve().parent / "static"


class MessageEnvelope(BaseModel):
    """Serializable representation of a chat message."""

    role: str = Field(pattern=r"^(user|assistant)$")
    content: str


class MessageRequest(BaseModel):
    """Incoming user message payload."""

    text: str = Field(..., min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    """Response returned after the agent processes a message."""

    chat_id: str
    reply: str
    steps: List[str]
    messages: List[MessageEnvelope]
    title: str | None = None


class CreateChatRequest(BaseModel):
    """Optional payload when creating a chat session."""

    title: str | None = None


class CreateChatResponse(BaseModel):
    """Response payload containing a new chat identifier."""

    chat_id: str


class ChatDetailResponse(BaseModel):
    """Full representation of a chat session."""

    chat_id: str
    title: str | None = None
    messages: List[MessageEnvelope]


@dataclass
class ChatSession:
    """In-memory representation of a chat session."""

    chat_id: str = field(default_factory=lambda: uuid4().hex)
    title: str | None = None
    agent: Manus | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    messages: List[MessageEnvelope] = field(default_factory=list)

    def clone_messages(self) -> List[MessageEnvelope]:
        """Return a deep copy of stored messages to avoid shared references."""

        return [message.model_copy(deep=True) for message in self.messages]

    def snapshot(self) -> ChatDetailResponse:
        """Produce a serializable representation of the chat session."""

        return ChatDetailResponse(
            chat_id=self.chat_id,
            title=self.title,
            messages=self.clone_messages(),
        )

    async def ensure_agent(self) -> Manus:
        """Instantiate the Manus agent lazily for the session."""

        if self.agent is None:
            logger.info("Creating Manus agent for chat %s", self.chat_id)
            self.agent = await Manus.create()
        return self.agent

    async def handle_message(self, text: str) -> tuple[str, List[str]]:
        """Append the user message, invoke the agent and store the reply."""

        self.messages.append(MessageEnvelope(role="user", content=text))
        if not self.title:
            snippet = text.strip()
            if snippet:
                self.title = snippet[:30] + ("..." if len(snippet) > 30 else "")
        agent = await self.ensure_agent()

        try:
            summary = await agent.run(text)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to run Manus for chat %s", self.chat_id)
            raise HTTPException(status_code=500, detail="Agent execution failed") from exc

        summary = summary or ""

        assistant_messages = [
            msg.content
            for msg in agent.memory.messages
            if msg.role == "assistant" and msg.content
        ]
        reply = assistant_messages[-1] if assistant_messages else summary
        self.messages.append(MessageEnvelope(role="assistant", content=reply))

        steps = [line.strip() for line in summary.splitlines() if line.strip()]
        return reply, steps

    async def close(self) -> None:
        """Dispose of agent resources associated with the chat."""

        if self.agent is not None:
            try:
                await self.agent.cleanup()
            except Exception:  # pragma: no cover - best effort cleanup
                logger.exception("Error cleaning up Manus for chat %s", self.chat_id)
            finally:
                self.agent = None


def _create_application() -> "FastAPI":
    """Build the FastAPI application used to expose the HTTP interface."""

    if FASTAPI_IMPORT_ERROR is not None:  # pragma: no cover - import guard
        raise RuntimeError(
            "FastAPI is required to run the web server. Install dependencies with "
            "'pip install -r requirements.txt' or 'pip install fastapi uvicorn'."
        ) from FASTAPI_IMPORT_ERROR

    sessions: Dict[str, ChatSession] = {}
    sessions_lock = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            # Ensure all sessions release resources when the server stops.
            async with sessions_lock:
                pending_sessions = list(sessions.values())
                sessions.clear()

            for session in pending_sessions:
                await session.close()

    app = FastAPI(title="OpenManus Server", version="1.0.0", lifespan=lifespan)

    # Allow usage from local tooling without additional reverse proxies.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.post("/api/chats", response_model=CreateChatResponse)
    async def create_chat(request: CreateChatRequest | None = None) -> CreateChatResponse:
        session = ChatSession(title=(request.title if request else None))
        async with sessions_lock:
            sessions[session.chat_id] = session
        logger.info("Created chat %s", session.chat_id)
        return CreateChatResponse(chat_id=session.chat_id)

    @app.get("/api/chats", response_model=List[ChatDetailResponse])
    async def list_chats() -> List[ChatDetailResponse]:
        async with sessions_lock:
            snapshot = list(sessions.values())

        return [session.snapshot() for session in snapshot]

    @app.get("/api/chats/{chat_id}", response_model=ChatDetailResponse)
    async def get_chat(chat_id: str) -> ChatDetailResponse:
        async with sessions_lock:
            session = sessions.get(chat_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        return session.snapshot()

    @app.delete("/api/chats/{chat_id}", status_code=204)
    async def delete_chat(chat_id: str) -> Response:
        async with sessions_lock:
            session = sessions.pop(chat_id, None)
        if session is None:
            return Response(status_code=204)
        await session.close()
        logger.info("Deleted chat %s", chat_id)
        return Response(status_code=204)

    @app.post("/api/chats/{chat_id}/messages", response_model=MessageResponse)
    async def post_message(chat_id: str, payload: MessageRequest) -> MessageResponse:
        async with sessions_lock:
            session = sessions.get(chat_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Chat not found")

        async with session.lock:
            reply, steps = await session.handle_message(payload.text)
            return MessageResponse(
                chat_id=chat_id,
                reply=reply,
                steps=steps,
                messages=session.clone_messages(),
                title=session.title,
            )

    @app.get("/")
    async def index() -> FileResponse:
        if not STATIC_DIR.exists():
            raise HTTPException(status_code=404, detail="Static assets missing")
        return FileResponse(STATIC_DIR / "index.html")

    return app


if FASTAPI_IMPORT_ERROR is None:
    app = _create_application()
else:

    async def app(scope, receive, send):  # type: ignore[override]
        """ASGI placeholder that informs users about missing FastAPI."""

        raise RuntimeError(
            "FastAPI is not installed. Install dependencies with 'pip install fastapi "
            "uvicorn' or via requirements.txt before running the web server."
        )


def main(argv: list[str] | None = None) -> None:
    """Entry point used to launch the FastAPI server with uvicorn."""

    import argparse

    if FASTAPI_IMPORT_ERROR is not None:
        raise SystemExit(
            "FastAPI is not available. Install it with 'pip install fastapi uvicorn' "
            "or run 'pip install -r requirements.txt' before starting the server."
        )

    parser = argparse.ArgumentParser(description="Run the OpenManus web server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable autoreload (development only)",
    )
    args = parser.parse_args(argv)

    import uvicorn

    uvicorn.run(
        "app.web.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


__all__ = ["app", "main"]


if __name__ == "__main__":
    main()
