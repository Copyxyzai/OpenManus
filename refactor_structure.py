#!/usr/bin/env python3
"""
OpenManus Project Structure Refactoring Script
Reorganizes tools, tests, and scripts for better maintainability.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# Define the project root
PROJECT_ROOT = Path(__file__).parent

# Tool reorganization mapping (old_path -> new_path)
TOOL_MOVES = {
    # Base files
    "app/tool/base.py": "app/tools/base.py",
    "app/tool/tool_collection.py": "app/tools/collection.py",
    # Core tools
    "app/tool/python_execute.py": "app/tools/core/python_execute.py",
    "app/tool/bash.py": "app/tools/core/bash.py",
    "app/tool/file_operators.py": "app/tools/core/file_operators.py",
    "app/tool/str_replace_editor.py": "app/tools/core/str_replace_editor.py",
    # Web tools
    "app/tool/browser_use_tool.py": "app/tools/web/browser_use.py",
    "app/tool/crawl4ai.py": "app/tools/web/crawl4ai.py",
    "app/tool/web_search.py": "app/tools/web/web_search.py",
    "app/tool/search": "app/tools/web/search",  # directory
    # AI tools
    "app/tool/audio_tool.py": "app/tools/ai/audio_transcription.py",
    "app/tool/memory_tool.py": "app/tools/ai/memory.py",
    "app/tool/planning.py": "app/tools/ai/planning.py",
    "app/tool/create_chat_completion.py": "app/tools/ai/chat_completion.py",
    # Interaction tools
    "app/tool/ask_human.py": "app/tools/interaction/ask_human.py",
    "app/tool/terminate.py": "app/tools/interaction/terminate.py",
    # Visualization
    "app/tool/chart_visualization": "app/tools/visualization/chart",  # directory
    # Sandbox
    "app/tool/sandbox": "app/tools/sandbox",  # directory
    # Other tools
    "app/tool/mcp.py": "app/tools/mcp_tool.py",
    "app/tool/computer_use_tool.py": "app/tools/computer_use.py",
}

# Import replacements (old_import -> new_import)
IMPORT_REPLACEMENTS = {
    "from app.tools.ai.audio_transcription import": "from app.tools.ai.audio_transcription import",
    "from app.tools.ai.memory import": "from app.tools.ai.memory import",
    "from app.tools.core.python_execute import": "from app.tools.core.python_execute import",
    "from app.tools.interaction.ask_human import": "from app.tools.interaction.ask_human import",
    "from app.tools.web.browser_use import": "from app.tools.web.browser_use import",
    "from app.tools.core.str_replace_editor import": "from app.tools.core.str_replace_editor import",
    "from app.tools import": "from app.tools import",
    "from app.tools.mcp_tool import": "from app.tools.mcp_tool import",
    "from app.tools.ai.planning import": "from app.tools.ai.planning import",
    "from app.tools.interaction.terminate import": "from app.tools.interaction.terminate import",
}

# Test file moves
TEST_MOVES = {
    "test_browser.py": "tests/integration/test_browser.py",
    "test_whisper.py": "tests/integration/test_whisper.py",
    "test_memory_init.py": "tests/unit/test_memory.py",
    "test_new_model.py": "tests/unit/test_llm.py",
    "test_responses_api.py": "tests/unit/test_llm_responses.py",
}

# Script moves
SCRIPT_MOVES = {
    "debug_env.py": "scripts/dev/debug_env.py",
    "debug_output.txt": "scripts/dev/debug_output.txt",
    "debug_responses_input.py": "scripts/dev/debug_responses_input.py",
    "debug_responses_input_v2.py": "scripts/dev/debug_responses_input_v2.py",
    "debug_responses_stream.py": "scripts/dev/debug_responses_stream.py",
    "debug_stream_output.txt": "scripts/dev/debug_stream_output.txt",
    "run_flow.py": "scripts/run_flow.py",
    "run_mcp.py": "scripts/run_mcp.py",
    "run_mcp_server.py": "scripts/run_mcp_server.py",
    "sandbox_main.py": "scripts/sandbox_main.py",
}


def create_directories(moves: Dict[str, str]):
    """Create all necessary directories for target paths."""
    for target in moves.values():
        target_path = PROJECT_ROOT / target
        if not target.endswith(".py"):  # It's a directory
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created {len(set(Path(t).parent for t in moves.values()))} directories")


def move_files(moves: Dict[str, str], dry_run: bool = False):
    """Move files from old locations to new locations."""
    moved = 0
    for source, target in moves.items():
        source_path = PROJECT_ROOT / source
        target_path = PROJECT_ROOT / target

        if not source_path.exists():
            print(f"⚠️  Source not found: {source}")
            continue

        if dry_run:
            print(f"📋 Would move: {source} -> {target}")
        else:
            if source_path.is_dir():
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            else:
                shutil.copy2(source_path, target_path)
            moved += 1
            print(f"✅ Moved: {source} -> {target}")

    print(f"✅ Moved {moved} items")
    return moved


def update_imports_in_file(file_path: Path, replacements: Dict[str, str]) -> int:
    """Update imports in a single file."""
    if not file_path.suffix == ".py":
        return 0

    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        for old, new in replacements.items():
            content = content.replace(old, new)

        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return 1
    except Exception as e:
        print(f"⚠️  Error updating {file_path}: {e}")

    return 0


def update_all_imports(replacements: Dict[str, str], dry_run: bool = False):
    """Update imports across all Python files in the project."""
    updated = 0
    python_files = list(PROJECT_ROOT.rglob("*.py"))

    for py_file in python_files:
        # Skip venv and __pycache__
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue

        if dry_run:
            print(f"📋 Would check: {py_file.relative_to(PROJECT_ROOT)}")
        else:
            if update_imports_in_file(py_file, replacements):
                updated += 1
                print(f"✅ Updated imports in: {py_file.relative_to(PROJECT_ROOT)}")

    print(f"✅ Updated {updated} files")
    return updated


def create_init_files():
    """Create __init__.py files in new directories."""
    init_files = [
        "app/tools/__init__.py",
        "app/tools/core/__init__.py",
        "app/tools/web/__init__.py",
        "app/tools/ai/__init__.py",
        "app/tools/interaction/__init__.py",
        "app/tools/visualization/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "scripts/__init__.py",
        "scripts/dev/__init__.py",
    ]

    for init_file in init_files:
        init_path = PROJECT_ROOT / init_file
        init_path.parent.mkdir(parents=True, exist_ok=True)
        if not init_path.exists():
            init_path.write_text("# Auto-generated\n")
            print(f"✅ Created: {init_file}")


def create_backward_compat_shim():
    """Create backward compatibility shim in old app/tool/__init__.py"""
    shim_content = '''"""
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
'''
    shim_path = PROJECT_ROOT / "app" / "tool" / "__init__.py"
    shim_path.write_text(shim_content)
    print("✅ Created backward compatibility shim at app/tool/__init__.py")


def main():
    print("=" * 60)
    print("OpenManus Project Structure Refactoring")
    print("=" * 60)

    # Ask for confirmation
    print("\nThis script will:")
    print("1. Reorganize app/tool/ -> app/tools/ with categories")
    print("2. Move test files from root -> tests/")
    print("3. Move utility scripts -> scripts/")
    print("4. Update all imports across the project")
    print("5. Create backward compatibility shims")

    response = input("\nProceed with refactoring? (yes/no): ").strip().lower()
    if response not in ("yes", "y"):
        print("❌ Refactoring cancelled")
        return

    print("\n" + "=" * 60)
    print("Starting refactoring...")
    print("=" * 60 + "\n")

    # Phase 1: Create directories
    print("📁 Phase 1: Creating directory structure...")
    create_directories(TOOL_MOVES)
    create_directories(TEST_MOVES)
    create_directories(SCRIPT_MOVES)
    create_init_files()

    # Phase 2: Move files
    print("\n📦 Phase 2: Moving tool files...")
    move_files(TOOL_MOVES)

    print("\n📦 Phase 3: Moving test files...")
    move_files(TEST_MOVES)

    print("\n📦 Phase 4: Moving script files...")
    move_files(SCRIPT_MOVES)

    # Phase 3: Update imports
    print("\n🔄 Phase 5: Updating imports across project...")
    update_all_imports(IMPORT_REPLACEMENTS)

    # Phase 4: Create backward compatibility
    print("\n🔗 Phase 6: Creating backward compatibility shim...")
    create_backward_compat_shim()

    print("\n" + "=" * 60)
    print("✅ Refactoring complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test the application: python main.py --help")
    print("2. Run tests: pytest tests/")
    print("3. Review changes and commit")


if __name__ == "__main__":
    main()
