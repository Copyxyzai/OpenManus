import os
from datetime import datetime
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings


class SimpleVectorStore:
    """
    A wrapper around ChromaDB for vector storage with multi-collection support.
    """

    def __init__(self, storage_path: str = "workspace/memory/chroma_db"):
        self.storage_path = storage_path
        self._ensure_storage()

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.storage_path)

        # Default collection for backward compatibility
        self.collection = self.client.get_or_create_collection(name="manus_memory")

    def _ensure_storage(self):
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_path, exist_ok=True)

    def _get_collection(self, collection_name: str):
        """Get or create a specific collection."""
        return self.client.get_or_create_collection(name=collection_name)

    def add(self, text: str, embedding: List[float], metadata: Optional[Dict] = None):
        """Add a text and its embedding to the default store."""
        self.add_to_collection("manus_memory", text, embedding, metadata)

    def add_to_collection(
        self,
        collection_name: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict] = None,
    ):
        """
        Add a text and its embedding to a specific collection.

        Args:
            collection_name: Name of the collection
            text: Text content
            embedding: Embedding vector
            metadata: Optional metadata dict
        """
        collection = self._get_collection(collection_name)

        # Prepare metadata
        meta = metadata or {}
        meta["timestamp"] = datetime.now().isoformat()

        # Generate a unique ID
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        collection.add(
            documents=[text], embeddings=[embedding], metadatas=[meta], ids=[doc_id]
        )

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for the most similar texts in the default collection."""
        return self.search_collection("manus_memory", query_embedding, k)

    def search_collection(
        self, collection_name: str, query_embedding: List[float], k: int = 5
    ) -> List[Dict]:
        """
        Search for the most similar texts in a specific collection.

        Args:
            collection_name: Name of the collection to search
            query_embedding: The embedding vector of the query.
            k: Number of results to return.

        Returns:
            List of most similar entries (with 'similarity' score added).
        """
        collection = self._get_collection(collection_name)

        # Query ChromaDB
        results = collection.query(query_embeddings=[query_embedding], n_results=k)

        # Format results to match previous interface
        formatted_results = []

        if not results["documents"] or not results["documents"][0]:
            return []

        # Iterate through the first query result (since we only sent one query)
        for i in range(len(results["documents"][0])):
            doc = results["documents"][0][i]
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 0

            # Convert L2 distance to approximate cosine similarity
            # Note: embeddings are unit length from OpenAI, so L2^2 = 2(1-cos(theta))
            # Distance = sqrt(2(1-sim))
            # So Sim = 1 - (Distance^2)/2
            similarity = 1 - (dist * dist) / 2

            entry = {"text": doc, "metadata": meta, "similarity": float(similarity)}
            formatted_results.append(entry)

        return formatted_results

    def get_all_from_collection(self, collection_name: str) -> List[str]:
        """
        Get all texts from a specific collection.

        Args:
            collection_name: Name of the collection

        Returns:
            List of all text entries
        """
        try:
            collection = self._get_collection(collection_name)
            results = collection.get()
            return results["documents"] if results["documents"] else []
        except Exception:
            return []

    def delete_collection(self, collection_name: str):
        """Delete a collection."""
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass
