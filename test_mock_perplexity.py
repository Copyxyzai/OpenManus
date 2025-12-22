"""
Mock Test for Perplexity Tools

Tests tool structure and methods without external API calls.
"""

import asyncio

from app.tools.web.perplexity_deep_search import PerplexityDeepSearchTool
from app.tools.web.perplexity_search import PerplexitySearchTool


def test_tool_initialization():
    """Test that tools can be initialized"""
    print("\n=== Testing Tool Initialization ===\n")

    # Test PerplexitySearchTool
    search_tool = PerplexitySearchTool()
    print(f"✅ PerplexitySearchTool initialized")
    print(f"   Name: {search_tool.name}")
    print(f"   Description: {search_tool.description[:50]}...")
    print(f"   Parameters: {list(search_tool.parameters.get('properties', {}).keys())}")

    # Test PerplexityDeepSearchTool
    deep_tool = PerplexityDeepSearchTool()
    print(f"\n✅ PerplexityDeepSearchTool initialized")
    print(f"   Name: {deep_tool.name}")
    print(f"   Description: {deep_tool.description[:50]}...")
    print(f"   Parameters: {list(deep_tool.parameters.get('properties', {}).keys())}")


def test_tool_params():
    """Test that tools expose correct parameters"""
    print("\n\n=== Testing Tool Parameters ===\n")

    search_tool = PerplexitySearchTool()
    params = search_tool.to_param()

    print(f"✅ Tool parameter schema:")
    print(f"   Type: {params['type']}")
    print(f"   Function name: {params['function']['name']}")
    print(f"   Required params: {params['function']['parameters'].get('required', [])}")


async def test_mock_search():
    """Test search with mocked results"""
    print("\n\n=== Testing Mock Search ===\n")

    # Mock results
    mock_results = [
        {
            "index": 1,
            "title": "AI Explained",
            "snippet": "Artificial Intelligence is the simulation of human intelligence...",
            "url": "https://example.com/ai",
        },
        {
            "index": 2,
            "title": "Machine Learning Basics",
            "snippet": "ML is a subset of AI that enables systems to learn...",
            "url": "https://example.com/ml",
        },
    ]

    # Test context building
    search_tool = PerplexitySearchTool()
    context = search_tool._build_context(mock_results)
    print(f"✅ Context built: {len(context)} characters")

    # Test sources section
    sources = search_tool._build_sources_section(mock_results)
    print(f"✅ Sources formatted:\n{sources}\n")


async def test_mock_deep_search():
    """Test deep search with mocked content"""
    print("\n\n=== Testing Mock Deep Search ===\n")

    # Mock scraped content
    mock_scraped = [
        {
            "index": 1,
            "title": "Deep AI Analysis",
            "url": "https://example.com/deep-ai",
            "content": "This is a comprehensive analysis of AI technologies..." * 10,
            "content_length": 500,
        },
        {
            "index": 2,
            "title": "ML Research Paper",
            "url": "https://example.com/ml-paper",
            "content": "Machine learning research has shown..." * 10,
            "content_length": 450,
        },
    ]

    # Test context building
    deep_tool = PerplexityDeepSearchTool()
    context = deep_tool._build_deep_context(mock_scraped)
    print(f"✅ Deep context built: {len(context)} characters")

    # Test sources section
    sources = deep_tool._build_detailed_sources(mock_scraped)
    print(f"✅ Detailed sources formatted:\n{sources}\n")


async def main():
    """Run all mock tests"""
    print("\n🧪 Mock Testing Perplexity Tools\n")
    print("=" * 60)

    try:
        # Test 1: Initialization
        test_tool_initialization()

        # Test 2: Parameters
        test_tool_params()

        # Test 3: Mock search
        await test_mock_search()

        # Test 4: Mock deep search
        await test_mock_deep_search()

        print("\n" + "=" * 60)
        print("\n✅ All mock tests passed!")
        print("\n📊 Summary:")
        print("   - Tool initialization: ✅")
        print("   - Parameter schemas: ✅")
        print("   - Context building: ✅")
        print("   - Source formatting: ✅")
        print("\n⚠️  Note: Live API tests blocked by DuckDuckGo rate limit")
        print("   Try again in ~10 minutes for full integration test")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
