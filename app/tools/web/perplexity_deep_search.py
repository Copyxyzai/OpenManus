"""
Perplexity-Style Deep Search Tool

Deep web search with content analysis and advanced synthesis.
Scrapes and analyzes multiple sources for comprehensive answers.
"""

import asyncio
from typing import Any, Dict, List, Optional

from app.logger import logger
from app.tools.base import BaseTool, ToolResult


class PerplexityDeepSearchTool(BaseTool):
    """
    Deep Search estilo Perplexity

    Features:
    - Multi-source search
    - Web scraping (trafilatura)
    - Análise profunda
    - Síntese LLM avançada
    - Comparação de fontes
    """

    name: str = "perplexity_deep_search"
    description: str = """
Busca web profunda estilo Perplexity.ai Pro.
Analisa conteúdo completo de múltiplas fontes.

Use quando:
- Precisa de análise detalhada
- Quer comparar múltiplas fontes
- Busca informação complexa
- Tempo não é crítico (10-30s)
"""

    parameters: Optional[dict] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Query de busca"},
            "num_sources": {
                "type": "integer",
                "default": 5,
                "description": "Número de fontes a analisar (max 10)",
            },
            "depth": {
                "type": "string",
                "enum": ["standard", "comprehensive"],
                "default": "standard",
                "description": "Profundidade de análise",
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> ToolResult:
        """Execute deep search"""
        try:
            query = kwargs["query"]
            num_sources = min(kwargs.get("num_sources", 5), 10)
            depth = kwargs.get("depth", "standard")

            logger.info(f"🔍 Deep Search: {query} (depth: {depth})")

            # 1. Multi-source search
            search_results = await self._multi_source_search(query, num_sources)

            if not search_results:
                return ToolResult(
                    output=f"❌ Nenhum resultado encontrado para: {query}",
                    success=False,
                )

            # 2. Scrape top sources
            scraped_content = await self._scrape_sources(
                search_results[:5], depth=depth  # Top 5
            )

            # 3. Deep synthesis
            deep_response = await self._deep_synthesis(
                query, search_results, scraped_content, depth
            )

            logger.info(
                f"✅ Deep search completed: {len(scraped_content)} sources analyzed"
            )

            return ToolResult(output=deep_response, success=True)

        except Exception as e:
            logger.error(f"Deep search error: {e}")
            return ToolResult(
                output=f"❌ Erro na busca profunda: {str(e)}", success=False
            )

    async def _multi_source_search(self, query: str, num_results: int) -> List[Dict]:
        """Search usando múltiplas fontes"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.error("duckduckgo_search not installed")
            return []

        results = []

        # DuckDuckGo
        try:
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
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")

        return results

    async def _scrape_sources(self, sources: List[Dict], depth: str) -> List[Dict]:
        """
        Scrape content from sources using trafilatura
        """
        try:
            from trafilatura import extract, fetch_url
        except ImportError:
            logger.warning(
                "trafilatura not installed. Install: pip install trafilatura"
            )
            # Fallback: return snippets only
            return [
                {
                    "index": s["index"],
                    "title": s["title"],
                    "url": s["url"],
                    "content": s["snippet"],
                    "content_length": len(s["snippet"]),
                }
                for s in sources
            ]

        scraped = []

        # Scrape em paralelo
        tasks = []
        for source in sources:
            tasks.append(self._scrape_single_source(source, depth))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict) and result.get("content"):
                scraped.append(result)

        return scraped

    async def _scrape_single_source(self, source: Dict, depth: str) -> Dict:
        """Scrape single source"""
        try:
            from trafilatura import extract, fetch_url

            url = source["url"]

            # Fetch in thread pool (trafilatura is sync)
            loop = asyncio.get_event_loop()
            downloaded = await loop.run_in_executor(None, fetch_url, url)

            if not downloaded:
                # Fallback to snippet
                return {
                    "index": source["index"],
                    "title": source["title"],
                    "url": source["url"],
                    "content": source["snippet"],
                    "content_length": len(source["snippet"]),
                }

            # Extract content
            content = extract(
                downloaded,
                include_comments=False,
                include_tables=True if depth == "comprehensive" else False,
                output_format="text",
            )

            if not content:
                # Fallback to snippet
                return {
                    "index": source["index"],
                    "title": source["title"],
                    "url": source["url"],
                    "content": source["snippet"],
                    "content_length": len(source["snippet"]),
                }

            # Limit content based on depth
            max_chars = 3000 if depth == "standard" else 8000

            return {
                "index": source["index"],
                "title": source["title"],
                "url": source["url"],
                "content": content[:max_chars],
                "content_length": len(content),
            }

        except Exception as e:
            logger.warning(f"Failed to scrape {source.get('url')}: {e}")
            # Fallback to snippet
            return {
                "index": source.get("index", 0),
                "title": source.get("title", ""),
                "url": source.get("url", ""),
                "content": source.get("snippet", ""),
                "content_length": len(source.get("snippet", "")),
            }

    async def _deep_synthesis(
        self,
        query: str,
        search_results: List[Dict],
        scraped_content: List[Dict],
        depth: str,
    ) -> str:
        """
        Deep synthesis usando LLM
        """
        from app.llm import LLM

        llm = LLM()

        # Build comprehensive context
        context = self._build_deep_context(scraped_content)

        # Advanced synthesis prompt
        synthesis_prompt = f"""You are a research assistant providing a comprehensive answer based on multiple web sources.

Query: {query}

Sources analyzed: {len(scraped_content)} pages

Full Content:
{context}

Instructions:
- Provide a detailed, well-structured answer
- Use [1], [2], [3] to cite sources
- Compare information from different sources
- Note any contradictions or uncertainties
- Include key facts, statistics, and examples
- Write in Portuguese (BR)
- Use markdown formatting for clarity
- If depth is comprehensive, provide extra detail and analysis

Depth level: {depth}
"""

        synthesis = await llm.ask(
            messages=[{"role": "user", "content": synthesis_prompt}],
            stream=False,
            temperature=0.2,  # Lower temp for factual content
        )

        # Build final response
        sources_section = self._build_detailed_sources(scraped_content)

        response = f"""# 🔍 Deep Search: {query}

{synthesis}

---

## 📊 Análise de Fontes

**Fontes analisadas:** {len(scraped_content)} páginas
**Conteúdo total:** {sum(s.get('content_length', 0) for s in scraped_content):,} caracteres
**Profundidade:** {depth.title()}

---

## 📚 Fontes Detalhadas

{sources_section}
"""

        return response

    def _build_deep_context(self, scraped_content: List[Dict]) -> str:
        """Build comprehensive context"""
        context_parts = []

        for scraped in scraped_content:
            context_parts.append(
                f"[{scraped['index']}] {scraped['title']}\n"
                f"URL: {scraped['url']}\n"
                f"Content:\n{scraped['content']}\n"
                f"{'='*50}\n"
            )

        return "\n".join(context_parts)

    def _build_detailed_sources(self, scraped: List[Dict]) -> str:
        """Build detailed sources section"""
        sources = []

        for s in scraped:
            word_count = len(s["content"].split())
            sources.append(
                f"**[{s['index']}]** [{s['title']}]({s['url']})\n"
                f"  - Conteúdo analisado: {word_count} palavras"
            )

        return "\n\n".join(sources)
