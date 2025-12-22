from typing import List, Optional

from pydantic import PrivateAttr

from app.llm import LLM
from app.memory.vector_store import SimpleVectorStore
from app.tools.base import BaseTool


class MemoryTool(BaseTool):
    name: str = "memory"
    description: str = """Access to long-term memory. Use this to save important information, user preferences, or context that should be remembered for future tasks, or to recall information from the past.
    Actions:
    - save: Store a text snippet in memory.
    - recall: Search memory for relevant information using a query.
    """
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["save", "recall"],
                "description": "The action to perform: 'save' to store info, 'recall' to retrieve info.",
            },
            "content": {
                "type": "string",
                "description": "For 'save': The text content to remember. For 'recall': The search query.",
            },
        },
        "required": ["action", "content"],
    }

    _store: SimpleVectorStore = PrivateAttr()
    _llm: LLM = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._store = SimpleVectorStore()
        # Initialize LLM for embeddings
        self._llm = LLM()

    async def execute(self, action: str, content: str, **kwargs) -> str:
        try:
            if action == "save":
                # Generate embedding
                embedding = await self._llm.get_embedding(content)
                if not embedding:
                    return "Error: Could not generate embedding for content."

                self._store.add(content, embedding)
                return f"Successfully saved to memory: '{content}'"

            elif action == "recall":
                # Generate embedding for query
                query_embedding = await self._llm.get_embedding(content)
                if not query_embedding:
                    return "Error: Could not generate embedding for query."

                results = self._store.search(query_embedding, k=3)

                if not results:
                    return "No relevant information found in memory."

                response = f"Found {len(results)} relevant items in memory:\n"
                for i, res in enumerate(results, 1):
                    # Format: 1. [Similarity: 0.85] Text content...
                    response += (
                        f"{i}. [Similarity: {res['similarity']:.2f}] {res['text']}\n"
                    )

                return response

            else:
                return f"Unknown action: {action}"

        except Exception as e:
            return f"Memory tool error: {str(e)}"
