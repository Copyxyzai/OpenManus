"""Document Search Tool - Search uploaded documents

Allows the agent to search through uploaded documents
using keyword and semantic search.
"""

from typing import Any, Dict, Optional

from app.logger import logger
from app.tools.base import BaseTool, ToolResult


class DocumentSearchTool(BaseTool):
    """Search through uploaded documents"""

    name: str = "document_search"
    description: str = """
Search through uploaded documents using keywords or semantic search.
Useful for finding information in previously uploaded files like PDFs, Word documents, or text files.

When to use:
- User asks about content in uploaded documents
- Need to retrieve information from files
- Search across multiple documents

The tool supports:
- Keyword search (based on exact words)
- Semantic search (based on meaning)
- Hybrid search (combines both - recommended)
"""

    parameters: Optional[dict] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query - what to look for in the documents",
            },
            "search_type": {
                "type": "string",
                "enum": ["keyword", "semantic", "hybrid"],
                "default": "hybrid",
                "description": "Type of search: keyword (exact words), semantic (meaning), or hybrid (both)",
            },
            "top_k": {
                "type": "integer",
                "default": 5,
                "description": "Number of results to return (max 20)",
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute document search

        Args:
            query: Search query
            search_type: "keyword", "semantic", or "hybrid"
            top_k: Number of results

        Returns:
            ToolResult with search results
        """
        try:
            from app.documents.search import get_search_engine

            query = kwargs["query"]
            search_type = kwargs.get("search_type", "hybrid")
            top_k = min(kwargs.get("top_k", 5), 20)  # Cap at 20

            logger.info(
                f"🔍 Searching documents: query='{query}', type={search_type}, top_k={top_k}"
            )

            # Get search engine
            search_engine = get_search_engine()

            # Perform search
            results = await search_engine.search(
                query=query, top_k=top_k, search_type=search_type, extract_keywords=True
            )

            if not results:
                return ToolResult(
                    output=f"No documents found matching '{query}'. Try:\n"
                    "- Using different keywords\n"
                    "- Using semantic search (searches by meaning)\n"
                    "- Checking if documents have been uploaded",
                    success=True,
                )

            # Format results
            output_lines = [f"Found {len(results)} document(s) matching '{query}':\n"]

            for i, result in enumerate(results, 1):
                filename = result["metadata"].get("filename", "Unknown")
                content_preview = (
                    result["content"][:300] + "..."
                    if len(result["content"]) > 300
                    else result["content"]
                )
                score = result.get("score", 0)

                output_lines.append(f"{i}. **{filename}** (relevance: {score:.2f})")
                output_lines.append(f"   {content_preview}\n")

            output = "\n".join(output_lines)

            logger.info(f"✅ Document search completed: {len(results)} results")

            return ToolResult(output=output, success=True)

        except Exception as e:
            logger.error(f"Document search error: {e}")
            return ToolResult(
                output=f"Error searching documents: {str(e)}", success=False
            )
