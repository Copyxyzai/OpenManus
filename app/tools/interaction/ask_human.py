from app.tools import BaseTool


class AskHuman(BaseTool):
    """Add a tool to ask human for help."""

    name: str = "ask_human"
    description: str = "Use this tool to ask human for help."
    parameters: str = {
        "type": "object",
        "properties": {
            "inquire": {
                "type": "string",
                "description": "The question you want to ask human.",
            }
        },
        "required": ["inquire"],
    }

    async def execute(self, inquire: str) -> str:
        import os
        import sys

        if os.getenv("OPENMANUS_NON_INTERACTIVE") == "true" or not sys.stdin.isatty():
            return "Human interaction is currently unavailable (non-interactive environment). Please proceed based on your best judgment."
        return input(f"""Bot: {inquire}\n\nYou: """).strip()
