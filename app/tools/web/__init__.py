"""
Perplexity-Style Search Tools - Easy Registration for Agent Integration

Provides convenient functions to get and register Perplexity tools.
"""

from app.tools.web.perplexity_deep_search import PerplexityDeepSearchTool
from app.tools.web.perplexity_search import PerplexitySearchTool

__all__ = [
    "PerplexitySearchTool",
    "PerplexityDeepSearchTool",
    "get_perplexity_tools",
    "get_search_tool",
    "get_deep_search_tool",
]


def get_perplexity_tools():
    """
    Get all Perplexity tools for easy agent integration

    Returns:
        List of Perplexity tool instances

    Example:
        >>> from app.tools.web import get_perplexity_tools
        >>> tools = get_perplexity_tools()
        >>> agent.add_tools(tools)
    """
    return [PerplexitySearchTool(), PerplexityDeepSearchTool()]


def get_search_tool():
    """
    Get fast search tool

    Returns:
        PerplexitySearchTool instance
    """
    return PerplexitySearchTool()


def get_deep_search_tool():
    """
    Get deep search tool

    Returns:
        PerplexityDeepSearchTool instance
    """
    return PerplexityDeepSearchTool()
