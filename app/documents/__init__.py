"""
Document Storage Module

Initialization and exports for document storage system.
"""

from app.documents.processor import DocumentProcessor
from app.documents.search import (
    DocumentSearchEngine,
    KeywordExtractor,
    get_search_engine,
)

__all__ = [
    "DocumentProcessor",
    "DocumentSearchEngine",
    "KeywordExtractor",
    "get_search_engine",
]
