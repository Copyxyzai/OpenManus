"""
Document Search Engine with NLTK Keyword Extraction

Provides advanced search functionality with:
- Keyword extraction using NLTK
- ChromaDB integration
- Hybrid search (keyword + semantic)
"""

from typing import Any, Dict, List, Optional

from app.logger import logger

# NLTK for keyword extraction
try:
    import nltk
    from nltk import pos_tag, word_tokenize

    # Download required data if not present
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)

    try:
        nltk.data.find("taggers/averaged_perceptron_tagger_eng")
    except LookupError:
        nltk.download("averaged_perceptron_tagger_eng", quiet=True)

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available. Install with: pip install nltk")


class KeywordExtractor:
    """Extract keywords from text using NLTK POS tagging"""

    @staticmethod
    def extract_keywords(
        text: str,
        max_keywords: int = 5,
        include_verbs: bool = False,
        min_word_length: int = 3,
    ) -> List[str]:
        """
        Extract keywords from text

        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract
            include_verbs: Whether to include verbs (default: only nouns)
            min_word_length: Minimum word length to consider

        Returns:
            List of extracted keywords
        """
        if not NLTK_AVAILABLE:
            # Fallback: simple word splitting
            words = text.lower().split()
            return [w for w in words if len(w) >= min_word_length][:max_keywords]

        try:
            # Tokenize and normalize
            tokens = word_tokenize(text.lower())

            # POS tagging
            tagged = pos_tag(tokens)

            # Extract based on POS tags
            if include_verbs:
                # Nouns and verbs
                keywords = [
                    word
                    for word, pos in tagged
                    if pos.startswith(("NN", "VB")) and len(word) >= min_word_length
                ]
            else:
                # Only nouns
                keywords = [
                    word
                    for word, pos in tagged
                    if pos.startswith("NN") and len(word) >= min_word_length
                ]

            # Remove duplicates while preserving order
            seen = set()
            unique_keywords = []
            for kw in keywords:
                if kw not in seen and kw.isalpha():  # Only alphabetic words
                    seen.add(kw)
                    unique_keywords.append(kw)

            result = unique_keywords[:max_keywords]

            if not result:
                # Fallback: get all non-trivial words
                result = [
                    word
                    for word, _ in tagged
                    if len(word) >= min_word_length and word.isalpha()
                ][:max_keywords]

            return result

        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            # Fallback
            words = text.lower().split()
            return [w for w in words if len(w) >= min_word_length and w.isalpha()][
                :max_keywords
            ]


class DocumentSearchEngine:
    """
    Search engine for uploaded documents
    Uses ChromaDB for vector storage and search
    """

    def __init__(self, collection_name: str = "documents"):
        """
        Initialize search engine

        Args:
            collection_name: ChromaDB collection name
        """
        self.collection_name = collection_name
        self.keyword_extractor = KeywordExtractor()
        self._collection = None

    def _get_collection(self):
        """Get or create ChromaDB collection"""
        if self._collection is None:
            from app.memory.vector_store import SimpleVectorStore

            store = SimpleVectorStore()
            self._collection = store._get_collection(self.collection_name)
        return self._collection

    async def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any],
        chunks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Add document to search index

        Args:
            document_id: Unique document ID
            content: Full document text
            metadata: Document metadata
            chunks: Optional pre-chunked content

        Returns:
            Result dictionary
        """
        try:
            collection = self._get_collection()

            # Get embedding for full content
            from app.llm import LLM

            llm = LLM()

            # Store main document
            embedding = await llm.get_embedding(content[:8000])  # Limit for embedding

            collection.add(
                ids=[document_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
            )

            # Store chunks if provided
            if chunks:
                chunk_ids = []
                chunk_embeddings = []
                chunk_texts = []
                chunk_metas = []

                for i, chunk in enumerate(chunks):
                    chunk_id = f"{document_id}_chunk_{i}"
                    chunk_embedding = await llm.get_embedding(chunk)
                    chunk_meta = {
                        **metadata,
                        "chunk_index": i,
                        "parent_id": document_id,
                        "is_chunk": True,
                    }

                    chunk_ids.append(chunk_id)
                    chunk_embeddings.append(chunk_embedding)
                    chunk_texts.append(chunk)
                    chunk_metas.append(chunk_meta)

                # Batch add chunks
                if chunk_ids:
                    collection.add(
                        ids=chunk_ids,
                        embeddings=chunk_embeddings,
                        documents=chunk_texts,
                        metadatas=chunk_metas,
                    )

            logger.info(
                f"✅ Added document {document_id} with {len(chunks or [])} chunks"
            )

            return {
                "success": True,
                "document_id": document_id,
                "chunks_count": len(chunks or []),
            }

        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return {"success": False, "error": str(e)}

    async def search(
        self,
        query: str,
        top_k: int = 10,
        search_type: str = "hybrid",
        extract_keywords: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search documents

        Args:
            query: Search query
            top_k: Number of results
            search_type: "keyword", "semantic", or "hybrid"
            extract_keywords: Whether to extract keywords from query
            filters: Optional metadata filters

        Returns:
            List of search results
        """
        try:
            collection = self._get_collection()

            if search_type == "semantic" or search_type == "hybrid":
                # Get query embedding
                from app.llm import LLM

                llm = LLM()
                query_embedding = await llm.get_embedding(query)

                # Semantic search
                results = collection.query(
                    query_embeddings=[query_embedding], n_results=top_k, where=filters
                )

                # Format results
                documents = []
                for i in range(len(results["ids"][0])):
                    documents.append(
                        {
                            "id": results["ids"][0][i],
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": (
                                results["distances"][0][i]
                                if "distances" in results
                                else None
                            ),
                            "score": (
                                1 - results["distances"][0][i]
                                if "distances" in results
                                else 1.0
                            ),
                        }
                    )

                logger.info(f"🔍 Semantic search returned {len(documents)} results")
                return documents

            elif search_type == "keyword":
                # Extract keywords if enabled
                if extract_keywords:
                    keywords = self.keyword_extractor.extract_keywords(
                        query, max_keywords=5
                    )
                    logger.info(f"📝 Extracted keywords: {keywords}")
                    search_query = " ".join(keywords)
                else:
                    search_query = query

                # For ChromaDB, we'll use contains filter on document text
                # This is a simple implementation - could be enhanced with full-text search
                all_docs = collection.get(where=filters)

                # Filter by keyword presence
                filtered_docs = []
                keywords_lower = (
                    [k.lower() for k in keywords]
                    if extract_keywords
                    else query.lower().split()
                )

                for i, doc in enumerate(all_docs["documents"]):
                    doc_lower = doc.lower()

                    # Count keyword matches
                    matches = sum(1 for kw in keywords_lower if kw in doc_lower)

                    if matches > 0:
                        filtered_docs.append(
                            {
                                "id": all_docs["ids"][i],
                                "content": doc,
                                "metadata": all_docs["metadatas"][i],
                                "score": matches
                                / len(keywords_lower),  # Simple relevance score
                                "matches": matches,
                            }
                        )

                # Sort by score
                filtered_docs.sort(key=lambda x: x["score"], reverse=True)

                logger.info(f"🔍 Keyword search returned {len(filtered_docs)} results")
                return filtered_docs[:top_k]

            else:
                raise ValueError(f"Invalid search_type: {search_type}")

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def delete_document(self, document_id: str) -> bool:
        """
        Delete document and its chunks

        Args:
            document_id: Document ID to delete

        Returns:
            Success boolean
        """
        try:
            collection = self._get_collection()

            # Delete main document
            collection.delete(ids=[document_id])

            # Delete chunks
            # Get all chunks for this document
            chunks = collection.get(where={"parent_id": document_id})
            if chunks["ids"]:
                collection.delete(ids=chunks["ids"])

            logger.info(f"🗑️ Deleted document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False

    def list_documents(
        self, limit: int = 50, offset: int = 0, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List all documents

        Args:
            limit: Max number of results
            offset: Offset for pagination
            filters: Optional metadata filters

        Returns:
            List of documents
        """
        try:
            collection = self._get_collection()

            # Get documents (exclude chunks)
            where_filter = filters or {}
            where_filter["is_chunk"] = {"$ne": True}  # Exclude chunks

            results = collection.get(where=where_filter, limit=limit, offset=offset)

            documents = []
            for i in range(len(results["ids"])):
                documents.append(
                    {
                        "id": results["ids"][i],
                        "content": results["documents"][i][:200] + "...",  # Preview
                        "metadata": results["metadatas"][i],
                    }
                )

            return documents

        except Exception as e:
            logger.error(f"List error: {e}")
            return []


# Singleton instance
_search_engine = None


def get_search_engine(collection_name: str = "documents") -> DocumentSearchEngine:
    """Get global search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = DocumentSearchEngine(collection_name)
    return _search_engine
