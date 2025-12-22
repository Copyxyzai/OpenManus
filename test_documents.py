"""
Test Document Storage System

Tests upload, search, and retrieval functionality.
"""

import asyncio
import tempfile
from pathlib import Path

from app.documents.processor import DocumentProcessor
from app.documents.search import KeywordExtractor, get_search_engine


async def test_keyword_extraction():
    """Test NLTK keyword extraction"""
    print("\n=== Testing Keyword Extraction ===")

    extractor = KeywordExtractor()

    test_queries = [
        "Do you think Jean and Alex live in Paris?",
        "How to implement machine learning algorithms?",
        "What is the capital of France?",
    ]

    for query in test_queries:
        keywords = extractor.extract_keywords(query, max_keywords=5)
        print(f"Query: {query}")
        print(f"Keywords: {keywords}\n")


async def test_document_processing():
    """Test document processor"""
    print("\n=== Testing Document Processor ===")

    # Create test text file
    test_content = """
    This is a test document about machine learning.
    Machine learning is a subset of artificial intelligence.
    It involves training models on data to make predictions.
    """

    # Test validation
    is_valid, error = DocumentProcessor.validate_file(
        "test.txt", len(test_content.encode()), "text/plain"
    )
    print(f"Validation: {is_valid} - {error}")

    # Test text extraction
    text = DocumentProcessor.extract_text_from_bytes(test_content.encode(), "test.txt")
    print(f"Extracted text length: {len(text)}")

    # Test chunking
    chunks = DocumentProcessor.chunk_text(text, chunk_size=100, overlap=20)
    print(f"Chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {chunk[:50]}...")


async def test_search_engine():
    """Test document search engine"""
    print("\n=== Testing Search Engine ===")

    search_engine = get_search_engine(collection_name="test_documents")

    # Add test documents
    test_docs = [
        {
            "id": "doc1",
            "content": "Machine learning is a branch of artificial intelligence focused on building systems that learn from data.",
            "metadata": {"filename": "ml_intro.txt", "author": "Test"},
        },
        {
            "id": "doc2",
            "content": "Python is a popular programming language for data science and machine learning applications.",
            "metadata": {"filename": "python_guide.txt", "author": "Test"},
        },
        {
            "id": "doc3",
            "content": "Deep learning uses neural networks with multiple layers to process complex patterns.",
            "metadata": {"filename": "deep_learning.txt", "author": "Test"},
        },
    ]

    print("Adding documents...")
    for doc in test_docs:
        result = await search_engine.add_document(
            document_id=doc["id"], content=doc["content"], metadata=doc["metadata"]
        )
        print(f"  Added: {doc['id']} - {result['success']}")

    # Test search
    print("\nTesting searches...")

    test_queries = [
        ("machine learning", "hybrid"),
        ("python programming", "keyword"),
        ("neural networks artificial intelligence", "semantic"),
    ]

    for query, search_type in test_queries:
        print(f"\nQuery: '{query}' (type: {search_type})")
        results = await search_engine.search(
            query=query, top_k=3, search_type=search_type
        )
        print(f"Results: {len(results)}")
        for i, result in enumerate(results, 1):
            print(
                f"  {i}. {result['metadata']['filename']} (score: {result.get('score', 0):.3f})"
            )

    # Cleanup
    print("\nCleaning up...")
    for doc in test_docs:
        search_engine.delete_document(doc["id"])
    print("✅ Test completed")


async def main():
    """Run all tests"""
    print("🧪 Testing Document Storage System\n")

    try:
        await test_keyword_extraction()
        await test_document_processing()
        await test_search_engine()

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
