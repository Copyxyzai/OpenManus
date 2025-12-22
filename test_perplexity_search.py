"""
Test Perplexity-Style Search Tools

Tests both PerplexitySearchTool and PerplexityDeepSearchTool.
"""

import asyncio

from app.tools.web.perplexity_deep_search import PerplexityDeepSearchTool
from app.tools.web.perplexity_search import PerplexitySearchTool


async def test_perplexity_search():
    """Test fast Perplexity search"""
    print("\n" + "=" * 60)
    print("Testing PerplexitySearchTool (Fast Search)")
    print("=" * 60 + "\n")

    tool = PerplexitySearchTool()

    # Test query
    query = "What is artificial intelligence?"
    print(f"Query: {query}\n")

    # Execute search
    result = await tool.execute(query=query, num_results=5)

    if result.success:
        print("✅ Search successful!\n")
        print("Response:")
        print("-" * 60)
        print(result.output)
        print("-" * 60)
    else:
        print(f"❌ Search failed: {result.output}")


async def test_perplexity_deep_search():
    """Test deep Perplexity search"""
    print("\n" + "=" * 60)
    print("Testing PerplexityDeepSearchTool (Deep Search)")
    print("=" * 60 + "\n")

    tool = PerplexityDeepSearchTool()

    # Test query
    query = "How does machine learning work?"
    print(f"Query: {query}\n")

    # Execute deep search
    result = await tool.execute(query=query, num_sources=5, depth="standard")

    if result.success:
        print("✅ Deep search successful!\n")
        print("Response:")
        print("-" * 60)
        print(
            result.output[:2000] + "..." if len(result.output) > 2000 else result.output
        )
        print("-" * 60)
    else:
        print(f"❌ Deep search failed: {result.output}")


async def test_comparison():
    """Compare Search vs DeepSearch"""
    print("\n" + "=" * 60)
    print("Comparing Search vs DeepSearch")
    print("=" * 60 + "\n")

    query = "Python programming language"

    # Test 1: Fast search
    print(f"1. Testing Fast Search for: '{query}'")
    fast_tool = PerplexitySearchTool()
    import time

    start = time.time()
    fast_result = await fast_tool.execute(query=query, num_results=3)
    fast_time = time.time() - start
    print(f"   Time: {fast_time:.2f}s")
    print(f"   Success: {fast_result.success}")

    # Test 2: Deep search
    print(f"\n2. Testing Deep Search for: '{query}'")
    deep_tool = PerplexityDeepSearchTool()
    start = time.time()
    deep_result = await deep_tool.execute(query=query, num_sources=3, depth="standard")
    deep_time = time.time() - start
    print(f"   Time: {deep_time:.2f}s")
    print(f"   Success: {deep_result.success}")

    # Comparison
    print(f"\n📊 Performance:")
    print(f"   Fast Search: {fast_time:.2f}s")
    print(f"   Deep Search: {deep_time:.2f}s")
    print(f"   Difference: {((deep_time/fast_time - 1)*100):.1f}% slower")


async def main():
    """Run all tests"""
    print("\n🧪 Testing Perplexity-Style Search System\n")

    try:
        # Test 1: Fast search
        await test_perplexity_search()

        # Wait a bit
        await asyncio.sleep(2)

        # Test 2: Deep search
        await test_perplexity_deep_search()

        # Wait a bit
        await asyncio.sleep(2)

        # Test 3: Comparison
        await test_comparison()

        print("\n✅ All tests completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
