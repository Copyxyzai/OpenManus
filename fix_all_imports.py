#!/usr/bin/env python3
"""Comprehensive fix for ALL old imports in moved files"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# All possible replacements
REPLACEMENTS = {
    "from app.tool.base import": "from app.tools.base import",
    "from app.tool import": "from app.tools import",
    "from app.tool.file_operators import": "from app.tools.core.file_operators import",
    "from app.tool.search.": "from app.tools.web.search.",
    "from app.tool.search import": "from app.tools.web.search import",
    "from app.tool.chart_visualization.": "from app.tools.visualization.chart.",
    "from app.tool.chart_visualization import": "from app.tools.visualization.chart import",
    "from app.tool.web_search import": "from app.tools.web.web_search import",
    "from app.tool.tool_collection import": "from app.tools.collection import",
}


def fix_all_imports_in_dir(directory: Path):
    """Recursively fix all Python files in directory"""
    fixed = 0

    for py_file in directory.rglob("*.py"):
        # Skip venv and __pycache__
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            original = content

            # Apply all replacements
            for old, new in REPLACEMENTS.items():
                content = content.replace(old, new)

            if content != original:
                py_file.write_text(content, encoding="utf-8")
                print(f"✅ Fixed: {py_file.relative_to(PROJECT_ROOT)}")
                fixed += 1
        except Exception as e:
            print(f"⚠️  Error in {py_file}: {e}")

    return fixed


def main():
    print("=" * 60)
    print("Comprehensive Import Fix")
    print("=" * 60)

    # Fix tools directory
    print("\nFixing app/tools/...")
    fixed_tools = fix_all_imports_in_dir(PROJECT_ROOT / "app" / "tools")

    # Fix entire app directory for any missed imports
    print("\nFixing entire app/...")
    fixed_app = fix_all_imports_in_dir(PROJECT_ROOT / "app")

    print("\n" + "=" * 60)
    print(f"✅ Fixed {fixed_tools + fixed_app} files total")
    print("=" * 60)


if __name__ == "__main__":
    main()
