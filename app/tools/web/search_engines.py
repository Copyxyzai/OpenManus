"""
Search Engine Manager with Fallback Support

Manages multiple search engines with automatic fallback on failures.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from app.logger import logger


class SearchEngine(ABC):
    """Abstract base class for search engines"""

    @abstractmethod
    async def search(self, query: str, num_results: int) -> List[Dict]:
        """
        Perform search

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        pass


class DuckDuckGoEngine(SearchEngine):
    """DuckDuckGo search engine"""

    async def search(self, query: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo"""
        from duckduckgo_search import DDGS

        results = []

        with DDGS() as ddg:
            for i, result in enumerate(ddg.text(query, max_results=num_results), 1):
                results.append(
                    {
                        "index": i,
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "url": result.get("href", ""),
                        "source": "DuckDuckGo",
                    }
                )

        return results


class BingEngine(SearchEngine):
    """Bing search engine (fallback)"""

    async def search(self, query: str, num_results: int) -> List[Dict]:
        """Search using Bing via existing WebSearch tool"""
        try:
            from app.tools.web.web_search import WebSearch

            search = WebSearch()
            # Use DuckDuckGo first since WebSearch uses it by default
            # In future, can add Bing API support here

            logger.info("Using WebSearch as fallback")
            result = await search.execute(query=query, num_results=num_results)

            # WebSearch returns different format, adapt it
            if hasattr(result, "output") and isinstance(result.output, list):
                return [
                    {
                        "index": i,
                        "title": r.get("title", ""),
                        "snippet": r.get("description", r.get("snippet", "")),
                        "url": r.get("url", r.get("link", "")),
                        "source": "WebSearch",
                    }
                    for i, r in enumerate(result.output, 1)
                ]

            return []

        except Exception as e:
            logger.error(f"WebSearch fallback failed: {e}")
            return []


class SearchEngineManager:
    """Manages fallback between multiple search engines"""

    def __init__(self, engines: List[tuple] = None):
        """
        Initialize manager

        Args:
            engines: List of (name, engine_instance) tuples
        """
        if engines is None:
            self.engines = [
                ("duckduckgo", DuckDuckGoEngine()),
                ("bing_fallback", BingEngine()),
            ]
        else:
            self.engines = engines

    async def search(self, query: str, num_results: int) -> List[Dict]:
        """
        Try engines in order until one succeeds

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of search results

        Raises:
            Exception if all engines fail
        """
        last_error = None

        for engine_name, engine in self.engines:
            try:
                logger.info(f"🔍 Trying {engine_name}...")
                results = await engine.search(query, num_results)

                if results:
                    logger.info(
                        f"✅ {engine_name} succeeded with {len(results)} results"
                    )
                    return results
                else:
                    logger.warning(f"⚠️ {engine_name} returned no results")

            except Exception as e:
                logger.warning(f"❌ {engine_name} failed: {e}")
                last_error = e
                continue

        # All engines failed
        error_msg = f"All search engines failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
