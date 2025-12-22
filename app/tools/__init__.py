"""
OpenManus Tools - Reorganized Structure

Tools are now organized into categories:
- core: Python, Bash, File operations, Editor
- web: Browser, Search, Crawl
- ai: Audio, Memory, Planning, Chat
- interaction: AskHuman, Terminate
- visualization: Charts
- sandbox: Sandbox operations
"""

# Base classes
from app.tools.base import BaseTool
from app.tools.collection import ToolCollection
from app.tools.core.bash import Bash

# Core tools
from app.tools.core.python_execute import PythonExecute
from app.tools.core.str_replace_editor import StrReplaceEditor

# Web tools
from app.tools.web.browser_use import BrowserUseTool
from app.tools.web.web_search import WebSearch

try:
    from app.tools.web.crawl4ai import Crawl4AITool
except ImportError:
    Crawl4AITool = None

# AI tools
from app.tools.ai.audio_transcription import AudioTool
from app.tools.ai.chat_completion import CreateChatCompletion
from app.tools.ai.memory import MemoryTool
from app.tools.ai.planning import PlanningTool

# Interaction tools
from app.tools.interaction.ask_human import AskHuman
from app.tools.interaction.terminate import Terminate

# MCP tools
try:
    from app.tools.mcp_tool import MCPClientTool
except ImportError:
    MCPClientTool = None

# Computer use
try:
    from app.tools.computer_use import ComputerUseTool
except ImportError:
    ComputerUseTool = None

__all__ = [
    # Base
    "BaseTool",
    "ToolCollection",
    # Core
    "PythonExecute",
    "Bash",
    "StrReplaceEditor",
    # Web
    "BrowserUseTool",
    "WebSearch",
    "Crawl4AITool",
    # AI
    "AudioTool",
    "MemoryTool",
    "PlanningTool",
    "CreateChatCompletion",
    # Interaction
    "AskHuman",
    "Terminate",
    # MCP
    "MCPClientTool",
    # Computer
    "ComputerUseTool",
]
