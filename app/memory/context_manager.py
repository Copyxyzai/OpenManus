from datetime import datetime
from typing import Dict, List, Optional

from app.llm import LLM
from app.memory.memory_extractor import MemoryExtractor
from app.memory.user_manager import UserManager
from app.memory.vector_store import SimpleVectorStore


class ContextManager:
    """
    Manages automatic long-term context for conversations with user-specific categorized memory.
    """

    def __init__(self, storage_path: str = "workspace/memory/chroma_db"):
        self.store = SimpleVectorStore(storage_path=storage_path)
        self.llm = LLM()
        self.extractor = MemoryExtractor()
        self.user_manager = UserManager()

    async def save_conversation(
        self,
        session_id: str,
        messages: List[Dict],
        tools_used: Optional[List[str]] = None,
    ):
        """
        Save conversation summary with embeddings (backward compatible).
        """
        user_id = self.user_manager.get_current_user_id()
        await self.save_user_context(user_id, session_id, messages, tools_used)

    async def save_user_context(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict],
        tools_used: Optional[List[str]] = None,
    ):
        """
        Extract and save categorized user context.

        Args:
            user_id: User identifier
            session_id: Session identifier
            messages: Conversation messages
            tools_used: Tools used in session
        """
        # 1. Save conversation summary (existing behavior)
        summary = await self.generate_summary(messages)
        embedding = await self.llm.get_embedding(summary)

        metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message_count": str(len(messages)),
            "tools_used": ",".join(tools_used) if tools_used else "",
        }

        # Save to user-specific conversation collection
        collection_name = f"{user_id}_conversations"
        self.store.add_to_collection(collection_name, summary, embedding, metadata)

        # 2. Extract and save categorized information
        extracted = await self.extractor.extract(messages)

        # Save preferences
        for pref in extracted.get("preferences", []):
            if pref.strip():
                pref_embedding = await self.llm.get_embedding(pref)
                self.store.add_to_collection(
                    f"{user_id}_preferences",
                    pref,
                    pref_embedding,
                    {"category": "preference", "user_id": user_id},
                )

        # Save facts
        for fact in extracted.get("facts", []):
            if fact.strip():
                fact_embedding = await self.llm.get_embedding(fact)
                self.store.add_to_collection(
                    f"{user_id}_facts",
                    fact,
                    fact_embedding,
                    {"category": "fact", "user_id": user_id},
                )

        # Save projects
        for project in extracted.get("projects", []):
            if project.strip():
                project_embedding = await self.llm.get_embedding(project)
                self.store.add_to_collection(
                    f"{user_id}_projects",
                    project,
                    project_embedding,
                    {"category": "project", "user_id": user_id},
                )

    async def load_relevant_context(self, current_prompt: str, k: int = 3) -> str:
        """
        Load relevant historical context (backward compatible).
        """
        user_id = self.user_manager.get_current_user_id()
        return await self.load_user_context(user_id, current_prompt, k)

    async def load_user_context(
        self, user_id: str, current_prompt: str, k: int = 3
    ) -> str:
        """
        Load comprehensive user context including all categories.

        Args:
            user_id: User identifier
            current_prompt: Current user prompt
            k: Number of items per category to retrieve

        Returns:
            Formatted context string
        """
        query_embedding = await self.llm.get_embedding(current_prompt)

        context_lines = [f"# USER PROFILE: {user_id}", ""]

        # Load preferences
        preferences = self.store.search_collection(
            f"{user_id}_preferences", query_embedding, k=k
        )
        if preferences:
            context_lines.append("## Preferences")
            for pref in preferences:
                if pref.get("similarity", 0) > 0.3:
                    context_lines.append(f"- {pref['text']}")
            context_lines.append("")

        # Load personal facts
        facts = self.store.search_collection(f"{user_id}_facts", query_embedding, k=k)
        if facts:
            context_lines.append("## Personal Facts")
            for fact in facts:
                if fact.get("similarity", 0) > 0.3:
                    context_lines.append(f"- {fact['text']}")
            context_lines.append("")

        # Load projects
        projects = self.store.search_collection(
            f"{user_id}_projects", query_embedding, k=k
        )
        if projects:
            context_lines.append("## Active Projects")
            for proj in projects:
                if proj.get("similarity", 0) > 0.3:
                    context_lines.append(f"- {proj['text']}")
            context_lines.append("")

        # Load recent conversations
        conversations = self.store.search_collection(
            f"{user_id}_conversations", query_embedding, k=2
        )
        if conversations:
            context_lines.append("## Recent Relevant Conversations")
            for i, conv in enumerate(conversations, 1):
                if conv.get("similarity", 0) > 0.3:
                    meta = conv.get("metadata", {})
                    timestamp = meta.get("timestamp", "unknown")
                    context_lines.append(
                        f"### Session {i} (Similarity: {conv['similarity']:.2f}, Date: {timestamp})"
                    )
                    context_lines.append(conv["text"])
                    context_lines.append("")

        return "\n".join(context_lines)

    async def generate_summary(self, messages: List[Dict]) -> str:
        """
        Generate a concise summary of the conversation.
        """
        if not messages:
            return "Empty conversation"

        # Extract user prompts and assistant responses
        conversation_text = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                conversation_text.append(f"User: {content}")
            elif role == "assistant":
                truncated = content[:500] + "..." if len(content) > 500 else content
                conversation_text.append(f"Assistant: {truncated}")

        full_text = "\n".join(conversation_text)

        # Use LLM to create summary
        summary_prompt = f"""Summarize this conversation in 2-3 sentences, focusing on key facts, decisions, and topics discussed:

{full_text}

Summary:"""

        try:
            summary = await self.llm.ask(
                messages=[{"role": "user", "content": summary_prompt}], stream=False
            )
            return summary
        except Exception as e:
            # Fallback: simple text summary
            return (
                f"Conversation with {len(messages)} messages. Topics: {full_text[:200]}"
            )
