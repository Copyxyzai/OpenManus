"""
Perplexity-Style Search Tool - Enhanced with Phase 1 Improvements

Fast web search with Perplexity.ai-style formatting.
Includes citations, LLM synthesis, and markdown output.

Phase 1 Enhancements:
- Cache with TTL and LRU eviction
- Rate limiting
- Input sanitization
- Search engine fallback
- Retry logic with exponential backoff
- Configuration management
"""

from typing import Any, Dict, List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.logger import logger
from app.tools.base import BaseTool, ToolResult
from app.tools.web.cache import SearchCache
from app.tools.web.config import perplexity_config
from app.tools.web.rate_limiter import AsyncRateLimiter
from app.tools.web.sanitizer import InputSanitizer
from app.tools.web.search_engines import SearchEngineManager

# Module-level instances (shared across all tool instances)
# This avoids Pydantic v2 ModelPrivateAttr issues with class-level attributes
_tool_cache = SearchCache(
    ttl=perplexity_config.search.get("cache_ttl", 3600),
    max_size=perplexity_config.search.get("cache_max_size", 100),
)
_tool_rate_limiter = AsyncRateLimiter(
    max_calls=perplexity_config.rate_limit.get("max_calls_per_hour", 50),
    period=perplexity_config.rate_limit.get("period_seconds", 3600),
)
_tool_search_manager = SearchEngineManager()


class PerplexitySearchTool(BaseTool):
    """
    Search web com formatação estilo Perplexity

    Features:
    - Busca DuckDuckGo (with fallback)
    - Citações numeradas [1][2][3]
    - Resumo com LLM
    - Markdown formatting
    - Cache de resultados
    - Rate limiting
    - Input sanitization
    """

    name: str = "perplexity_search"
    description: str = """
Busca web rápida estilo Perplexity.ai.
Retorna resposta formatada com citações e fontes.

Use quando:
- Precisa de informação rápida da web
- Quer resposta bem formatada
- Precisa de citações/fontes
"""

    parameters: Optional[dict] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Query de busca"},
            "num_results": {
                "type": "integer",
                "default": 5,
                "description": "Número de resultados (max 10)",
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> ToolResult:
        """Execute perplexity-style search with all Phase 1 enhancements"""
        try:
            # 1. Sanitize input
            raw_query = kwargs.get("query", "")
            query = InputSanitizer.sanitize_query(
                raw_query,
                max_length=perplexity_config.sanitization.get("max_query_length", 500),
            )

            if not InputSanitizer.validate_query(
                query,
                min_length=perplexity_config.sanitization.get("min_query_length", 2),
            ):
                return ToolResult(
                    output="❌ Query inválida. Use pelo menos 2 caracteres com letras ou números.",
                    success=False,
                )

            num_results = min(
                kwargs.get(
                    "num_results",
                    perplexity_config.search.get("default_num_results", 5),
                ),
                perplexity_config.search.get("max_num_results", 10),
            )

            logger.info(f"🔍 Perplexity Search: {query}")

            # 2. Check cache
            cache_key = _tool_cache.get_cache_key(query, num_results=num_results)
            cached_result = _tool_cache.get(cache_key)
            if cached_result:
                logger.info("💨 Returning cached result")
                return cached_result

            # 3. Rate limit
            await _tool_rate_limiter.acquire()

            # 4. Search with fallback and retry
            search_results = await self._search_web_with_retry(query, num_results)

            if not search_results:
                return ToolResult(
                    output=f"❌ Nenhum resultado encontrado para: {query}",
                    success=False,
                )

            # 5. Format response
            formatted_response = await self._format_perplexity_style(
                query, search_results
            )

            logger.info(
                f"✅ Perplexity search completed: {len(search_results)} sources"
            )

            # 6. Create result and cache it
            result = ToolResult(output=formatted_response, success=True)
            _tool_cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Perplexity search error: {e}")
            return ToolResult(output=f"❌ Erro na busca: {str(e)}", success=False)

    @retry(
        stop=stop_after_attempt(perplexity_config.retry.get("max_attempts", 3)),
        wait=wait_exponential(
            multiplier=1,
            min=perplexity_config.retry.get("min_wait", 4),
            max=perplexity_config.retry.get("max_wait", 10),
        ),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def _search_web_with_retry(self, query: str, num_results: int) -> List[Dict]:
        """Search with automatic retry on transient failures"""
        try:
            return await _tool_search_manager.search(query, num_results)
        except Exception as e:
            logger.warning(f"Search attempt failed: {e}, retrying...")
            raise

    async def _format_perplexity_style(self, query: str, results: List[Dict]) -> str:
        """
        Formatar resposta estilo Perplexity

        Formato:
        1. Resposta sintetizada (LLM)
        2. Citações inline [1][2][3]
        3. Seção "Sources" com links
        """

        # 1. Criar contexto para LLM
        context = self._build_context(results)

        # 2. Sintetizar resposta com LLM
        from app.llm import LLM

        llm = LLM()

        synthesis_prompt = f"""Based on the following web search results, provide a comprehensive answer to the query.
Include citations using [1], [2], [3] format to reference sources.

Query: {query}

Search Results:
{context}

Instructions:
- Provide a clear, concise answer
- Use [1], [2], [3] to cite sources inline
- Write in Portuguese (BR)
- Be factual and accurate
- If information is uncertain, mention it
"""

        synthesis = await llm.ask(
            messages=[{"role": "user", "content": synthesis_prompt}],
            stream=False,
            temperature=0.3,
        )

        # 3. Adicionar seção de fontes
        sources_section = self._build_sources_section(results)

        # 4. Montar resposta final
        final_response = f"""# 🔍 {query}

{synthesis}

---

## 📚 Fontes

{sources_section}
"""

        return final_response

    def _build_context(self, results: List[Dict]) -> str:
        """Build context for LLM"""
        context_lines = []
        for r in results:
            context_lines.append(
                f"[{r['index']}] {r['title']}\n{r['snippet']}\nURL: {r['url']}\n"
            )
        return "\n".join(context_lines)

    def _build_sources_section(self, results: List[Dict]) -> str:
        """Build sources section"""
        sources = []
        for r in results:
            source_label = r.get("source", "Web")
            sources.append(
                f"**[{r['index']}]** [{r['title']}]({r['url']}) ({source_label})"
            )
        return "\n\n".join(sources)

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        return _tool_cache.get_stats()

    @classmethod
    def clear_cache(cls):
        """Clear the cache"""
        _tool_cache.clear()

    @classmethod
    def get_rate_limit_remaining(cls) -> int:
        """Get remaining API calls before rate limit"""
        return _tool_rate_limiter.get_remaining()
