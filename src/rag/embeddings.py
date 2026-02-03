"""
Embedding Service for RAG

Tenet #15: Performance is a Safety Feature - Fast embeddings for real-time retrieval
Tenet #2: Zero PII in logs
"""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import structlog
from functools import lru_cache
import hashlib

logger = structlog.get_logger()


class EmbeddingService:
    """
    Generate embeddings for text using sentence-transformers.
    
    Uses all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service.
        
        Args:
            model_name: HuggingFace model name
        """
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info(
            "embedding_service_initialized",
            model=model_name
        )
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load model on first use."""
        if self._model is None:
            logger.info("loading_embedding_model", model=self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("embedding_model_loaded")
        return self._model
    
    @lru_cache(maxsize=1000)
    def _cached_embed(self, text_hash: str, text: str) -> tuple:
        """
        Cache embeddings by text hash.
        
        Args:
            text_hash: Hash of text (for cache key)
            text: Actual text to embed
            
        Returns:
            Tuple of embedding values (for hashability)
        """
        self._cache_misses += 1
        embedding = self.model.encode(text, convert_to_numpy=True)
        return tuple(embedding.tolist())
    
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (384 dimensions)
        """
        if not text or not text.strip():
            return np.zeros(384)
        
        # Hash text for caching (don't log actual text - PII protection)
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # Get from cache
        embedding_tuple = self._cached_embed(text_hash, text.strip())
        embedding = np.array(embedding_tuple)
        
        # Track cache performance
        cache_info = self._cached_embed.cache_info()
        if cache_info.hits > self._cache_hits:
            self._cache_hits = cache_info.hits
            logger.debug(
                "embedding_cache_hit",
                text_hash=text_hash,
                hit_rate=cache_info.hits / (cache_info.hits + cache_info.misses)
            )
        
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts (more efficient).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Array of embeddings (N x 384)
        """
        if not texts:
            return np.array([])
        
        # Filter empty texts
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        
        if not valid_texts:
            return np.zeros((len(texts), 384))
        
        logger.debug(
            "embedding_batch",
            count=len(valid_texts)
        )
        
        embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
        return embeddings
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        cache_info = self._cached_embed.cache_info()
        total = cache_info.hits + cache_info.misses
        
        return {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "hit_rate": cache_info.hits / total if total > 0 else 0.0,
            "cache_size": cache_info.currsize,
            "max_size": cache_info.maxsize
        }
