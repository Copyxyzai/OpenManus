"""
Simplified Perplexity Search Test

Quick test without Pydantic complexities.
"""

import asyncio

from duckduckgo_search import DDGS

from app.llm import LLM
from app.logger import logger


async def simple_perplexity_search(query: str, num_results: int = 5):
    """Simple search without Pydantic tool wrapper"""

    print(f"\n🔍 Searching: {query}\n")

    # 1. Search DuckDuckGo
    results = []
    try:
        with DDGS() as ddg:
            for i, result in enumerate(ddg.text(query, max_results=num_results), 1):
                results.append(
                    {
                        "index": i,
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "url": result.get("href", ""),
                    }
                )
        print(f"✅ Found {len(results)} results\n")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return None

    # 2. Build context
    context = "\n".join(
        [
            f"[{r['index']}] {r['title']}\n{r['snippet']}\nURL: {r['url']}\n"
            for r in results
        ]
    )

    # 3. LLM Synthesis
    llm = LLM()

    prompt = f"""Based on the following web search results, provide a comprehensive answer to the query.
Include citations using [1], [2], [3] format to reference sources.

Query: {query}

Search Results:
{context}

Instructions:
- Provide a clear, concise answer
- Use [1], [2], [3] to cite sources inline
- Write in Portuguese (BR)
- Be factual and accurate
"""

    print("🤖 Generating answer with LLM...\n")

    synthesis = await llm.ask(
        messages=[{"role": "user", "content": prompt}], stream=False, temperature=0.3
    )

    # 4. Format response
    sources = "\n\n".join(
        [f"**[{r['index']}]** [{r['title']}]({r['url']})" for r in results]
    )

    response = f"""# 🔍 {query}

{synthesis}

---

## 📚 Fontes

{sources}
"""

    return response


async def main():
    """Test simple search"""

    queries = [
        "What is artificial intelligence?",
        "Como funciona machine learning?",
    ]

    for query in queries:
        result = await simple_perplexity_search(query, num_results=3)

        if result:
            print("=" * 60)
            print(result)
            print("=" * 60)
            print("\n")

        # Wait between queries
        if query != queries[-1]:
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
