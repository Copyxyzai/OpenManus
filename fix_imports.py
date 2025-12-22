#!/usr/bin/env python3
"""Fix remaining old imports in moved tool files"""

from pathlib import Path

# Files that need fixing
FILES_TO_FIX = [
    "app/tools/web/web_search.py",
    "app/tools/web/crawl4ai.py",
    "app/tools/web/browser_use.py",
    "app/tools/visualization/chart/data_visualization.py",
    "app/tools/sandbox/sb_vision_tool.py",
    "app/tools/sandbox/sb_shell_tool.py",
    "app/tools/sandbox/sb_files_tool.py",
    "app/tools/sandbox/sb_browser_tool.py",
    "app/tools/mcp_tool.py",
    "app/tools/interaction/terminate.py",
    "app/tools/core/str_replace_editor.py",
    "app/tools/core/python_execute.py",
    "app/tools/core/bash.py",
    "app/tools/computer_use.py",
    "app/tools/ai/planning.py",
    "app/tools/ai/memory.py",
]

PROJECT_ROOT = Path(__file__).parent


def fix_file(filepath: str):
    """Fix imports in a single file"""
    file_path = PROJECT_ROOT / filepath
    if not file_path.exists():
        print(f"⚠️  Not found: {filepath}")
        return False

    content = file_path.read_text(encoding="utf-8")
    original = content

    # Replace old imports
    content = content.replace("from app.tool.base import", "from app.tools.base import")
    content = content.replace("from app.tool import", "from app.tools import")

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"✅ Fixed: {filepath}")
        return True
    else:
        print(f"ℹ️  No changes: {filepath}")
        return False


def main():
    print("Fixing remaining imports...")
    fixed = 0
    for filepath in FILES_TO_FIX:
        if fix_file(filepath):
            fixed += 1

    print(f"\n✅ Fixed {fixed} files")


if __name__ == "__main__":
    main()
