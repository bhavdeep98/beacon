"""
RAG (Retrieval-Augmented Generation) Module

Tenet #8: Engagement Before Intervention - Provide contextual, informed responses
Tenet #9: Visibility - All retrievals logged and traceable
"""

from src.rag.vector_store import VectorStore
from src.rag.retriever import ConversationRetriever, ResourceRetriever
from src.rag.embeddings import EmbeddingService

__all__ = [
    'VectorStore',
    'ConversationRetriever',
    'ResourceRetriever',
    'EmbeddingService'
]
