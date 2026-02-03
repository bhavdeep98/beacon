"""
Vector Store for RAG

Tenet #7: Immutability by Default - Vectors are immutable once stored
Tenet #15: Performance is a Safety Feature - Fast similarity search
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import structlog
from datetime import datetime
import json

logger = structlog.get_logger()


@dataclass(frozen=True)
class Document:
    """
    Immutable document with embedding.
    
    Tenet #7: Immutability by Default
    """
    id: str
    content: str
    embedding: tuple  # Tuple for immutability
    metadata: dict
    created_at: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


class VectorStore:
    """
    In-memory vector store for fast similarity search.
    
    For production, use Pinecone, Weaviate, or pgvector.
    """
    
    def __init__(self):
        """Initialize empty vector store."""
        self.documents: List[Document] = []
        self._index_built = False
        self._embeddings_matrix: Optional[np.ndarray] = None
        
        logger.info("vector_store_initialized")
    
    def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: np.ndarray,
        metadata: Optional[dict] = None
    ) -> Document:
        """
        Add document to vector store.
        
        Args:
            doc_id: Unique document ID
            content: Document text
            embedding: Document embedding vector
            metadata: Optional metadata
            
        Returns:
            Created document
        """
        # Check for duplicates
        if any(doc.id == doc_id for doc in self.documents):
            logger.warning(
                "duplicate_document",
                doc_id=doc_id
            )
            return next(doc for doc in self.documents if doc.id == doc_id)
        
        # Create immutable document
        doc = Document(
            id=doc_id,
            content=content,
            embedding=tuple(embedding.tolist()),
            metadata=metadata or {},
            created_at=datetime.utcnow().isoformat()
        )
        
        self.documents.append(doc)
        self._index_built = False  # Invalidate index
        
        logger.debug(
            "document_added",
            doc_id=doc_id,
            content_length=len(content),
            total_docs=len(self.documents)
        )
        
        return doc
    
    def add_documents_batch(
        self,
        documents: List[Tuple[str, str, np.ndarray, dict]]
    ) -> List[Document]:
        """
        Add multiple documents efficiently.
        
        Args:
            documents: List of (id, content, embedding, metadata) tuples
            
        Returns:
            List of created documents
        """
        created_docs = []
        
        for doc_id, content, embedding, metadata in documents:
            doc = self.add_document(doc_id, content, embedding, metadata)
            created_docs.append(doc)
        
        logger.info(
            "documents_batch_added",
            count=len(created_docs),
            total_docs=len(self.documents)
        )
        
        return created_docs
    
    def _build_index(self):
        """Build numpy matrix for fast similarity search."""
        if self._index_built and self._embeddings_matrix is not None:
            return
        
        if not self.documents:
            self._embeddings_matrix = np.array([])
            self._index_built = True
            return
        
        # Stack all embeddings into matrix
        embeddings = [np.array(doc.embedding) for doc in self.documents]
        self._embeddings_matrix = np.vstack(embeddings)
        self._index_built = True
        
        logger.debug(
            "index_built",
            num_docs=len(self.documents),
            embedding_dim=self._embeddings_matrix.shape[1]
        )
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_metadata: Optional[dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.documents:
            return []
        
        # Build index if needed
        self._build_index()
        
        # Filter documents by metadata
        if filter_metadata:
            filtered_docs = [
                (i, doc) for i, doc in enumerate(self.documents)
                if all(doc.metadata.get(k) == v for k, v in filter_metadata.items())
            ]
        else:
            filtered_docs = list(enumerate(self.documents))
        
        if not filtered_docs:
            return []
        
        # Get embeddings for filtered documents
        indices = [i for i, _ in filtered_docs]
        filtered_embeddings = self._embeddings_matrix[indices]
        
        # Calculate cosine similarities
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return []
        
        doc_norms = np.linalg.norm(filtered_embeddings, axis=1)
        
        # Avoid division by zero
        valid_indices = doc_norms > 0
        if not np.any(valid_indices):
            return []
        
        # Cosine similarity
        similarities = np.dot(
            filtered_embeddings[valid_indices],
            query_embedding
        ) / (doc_norms[valid_indices] * query_norm)
        
        # Convert to [0, 1] range
        similarities = (similarities + 1) / 2
        
        # Get top-k
        valid_docs = [filtered_docs[i] for i, v in enumerate(valid_indices) if v]
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = [
            (valid_docs[i][1], float(similarities[i]))
            for i in top_indices
        ]
        
        logger.debug(
            "search_completed",
            query_embedding_dim=len(query_embedding),
            filtered_count=len(filtered_docs),
            top_k=top_k,
            results_count=len(results)
        )
        
        return results
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def delete_by_id(self, doc_id: str) -> bool:
        """
        Delete document by ID.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        original_count = len(self.documents)
        self.documents = [doc for doc in self.documents if doc.id != doc_id]
        
        if len(self.documents) < original_count:
            self._index_built = False
            logger.info("document_deleted", doc_id=doc_id)
            return True
        
        return False
    
    def clear(self):
        """Clear all documents."""
        count = len(self.documents)
        self.documents = []
        self._embeddings_matrix = None
        self._index_built = False
        
        logger.info("vector_store_cleared", documents_removed=count)
    
    def get_stats(self) -> dict:
        """Get vector store statistics."""
        return {
            "total_documents": len(self.documents),
            "index_built": self._index_built,
            "embedding_dim": self._embeddings_matrix.shape[1] if self._embeddings_matrix is not None else 0
        }
    
    def export_to_json(self, filepath: str):
        """Export vector store to JSON file."""
        data = {
            "documents": [
                {
                    "id": doc.id,
                    "content": doc.content,
                    "embedding": list(doc.embedding),
                    "metadata": doc.metadata,
                    "created_at": doc.created_at
                }
                for doc in self.documents
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(
            "vector_store_exported",
            filepath=filepath,
            document_count=len(self.documents)
        )
    
    def import_from_json(self, filepath: str):
        """Import vector store from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.clear()
        
        for doc_data in data["documents"]:
            self.add_document(
                doc_id=doc_data["id"],
                content=doc_data["content"],
                embedding=np.array(doc_data["embedding"]),
                metadata=doc_data["metadata"]
            )
        
        logger.info(
            "vector_store_imported",
            filepath=filepath,
            document_count=len(self.documents)
        )
