"""
DEPRECATED: This module has been reorganized to app.tools
Import from new locations for future compatibility.

Backward compatibility shims - will be removed in future version.
"""
import warnings

# Core tools
from app.tools.core.python_execute import PythonExecute
from app.tools.core.bash import Bash
from app.tools.core.file_operators import *
from app.tools.core.str_replace_editor import StrReplaceEditor

# Web tools
from app.tools.web.browser_use import BrowserUseTool
from app.tools.web.crawl4ai import *
from app.tools.web.web_search import *

# AI tools
from app.tools.ai.audio_transcription import AudioTool
from app.tools.ai.memory import MemoryTool
from app.tools.ai.planning import *
from app.tools.ai.chat_completion import *

# Interaction
from app.tools.interaction.ask_human import AskHuman
from app.tools.interaction.terminate import Terminate

# Base
from app.tools.base import BaseTool
from app.tools.collection import ToolCollection

# MCP
from app.tools.mcp_tool import *

warnings.warn(
    "Importing from 'app.tool' is deprecated. "
    "Use 'app.tools.category.module' instead. "
    "This compatibility layer will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    'PythonExecute', 'Bash', 'StrReplaceEditor',
    'BrowserUseTool', 'AudioTool', 'MemoryTool',
    'AskHuman', 'Terminate', 'BaseTool', 'ToolCollection'
]
