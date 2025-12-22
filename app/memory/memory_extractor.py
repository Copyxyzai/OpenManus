import json
from typing import Dict, List

from app.llm import LLM


class MemoryExtractor:
    """
    Extracts structured information from conversations using LLM.
    """

    def __init__(self):
        self.llm = LLM()

    async def extract(self, messages: List[Dict]) -> Dict[str, List[str]]:
        """
        Extract categorized information from conversation messages.

        Args:
            messages: List of conversation messages

        Returns:
            Dict with categories: preferences, facts, projects
        """
        if not messages:
            return {"preferences": [], "facts": [], "projects": []}

        # Build conversation text
        conversation_text = self._build_conversation_text(messages)

        # Create extraction prompt
        extraction_prompt = f"""Analyze this conversation and extract structured information.

Conversation:
{conversation_text}

Extract and categorize the following (output in JSON format):
1. **preferences**: User preferences (tools, languages, settings, technologies they like)
2. **facts**: Personal facts (name, location, role, company, background)
3. **projects**: Project details (name, tech stack, goals, status)

Return ONLY valid JSON in this format:
{{
  "preferences": ["preference 1", "preference 2"],
  "facts": ["fact 1", "fact 2"],
  "projects": ["project 1", "project 2"]
}}

If a category has no information, return an empty list for that category.
"""

        try:
            # Use LLM to extract
            response = await self.llm.ask(
                messages=[{"role": "user", "content": extraction_prompt}], stream=False
            )

            # Parse JSON response
            # Remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            extracted = json.loads(cleaned.strip())

            # Validate structure
            result = {
                "preferences": extracted.get("preferences", []),
                "facts": extracted.get("facts", []),
                "projects": extracted.get("projects", []),
            }

            return result

        except Exception as e:
            # Fallback: return empty categories
            return {"preferences": [], "facts": [], "projects": []}

    def _build_conversation_text(
        self, messages: List[Dict], max_length: int = 2000
    ) -> str:
        """Build conversation text from messages."""
        lines = []
        total_length = 0

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role in ["user", "assistant"]:
                line = f"{role.capitalize()}: {content}"
                if total_length + len(line) > max_length:
                    break
                lines.append(line)
                total_length += len(line)

        return "\n".join(lines)
