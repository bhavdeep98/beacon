"""
Semantic Detection Strategy - Embedding-Based Similarity Matching

Uses sentence transformers to catch obfuscated or coded crisis language
that doesn't match explicit keywords. Converts text to 384-dimensional
embeddings and compares against pre-computed crisis phrase embeddings.

Model: all-MiniLM-L6-v2 (80MB, CPU-optimized)
Latency: ~20-30ms per message
Context Window: Last 3 messages

Design Principles:
- Catches obfuscated language ("checking out early", "time to disappear")
- Context-aware (uses previous messages for disambiguation)
- Should NOT trigger crisis alone (only 20% weight in consensus)
- Sarcasm filter reduces false positives

Limitations:
- Can misinterpret context ("checking out early" from class vs life)
- Requires sarcasm filter to prevent hyperbole false positives
- Less reliable than regex (probabilistic vs deterministic)

Usage:
    patterns = load_patterns("config/crisis_patterns.yaml")
    strategy = SemanticDetectionStrategy(patterns)
    score, matches = strategy.analyze(
        "I'm checking out early",
        context=["I can't take it anymore", "Everything is hopeless"]
    )
"""

import numpy as np
from typing import Tuple, List, Dict
from sentence_transformers import SentenceTransformer
import structlog

from .base import DetectionStrategy

logger = structlog.get_logger()


class SemanticDetectionStrategy(DetectionStrategy):
    """
    Semantic similarity-based crisis detection using embeddings.
    
    Catches obfuscated language that regex misses:
    - "checking out early" (leaving life, not class)
    - "time to disappear" (suicidal ideation)
    - "making things easier for everyone" (burden/worthlessness)
    
    How It Works:
    1. Convert message + context to 384-dim embedding
    2. Compare against pre-computed crisis phrase embeddings
    3. Use cosine similarity to find closest match
    4. Apply threshold (0.75) and weight by category confidence
    
    Strengths:
        - Catches novel phrasings and obfuscation
        - Context-aware (uses last 3 messages)
        - Handles typos and variations
        
    Limitations:
        - Can misinterpret context
        - Prone to false positives (needs sarcasm filter)
        - Slower than regex (~20-30ms vs ~5ms)
        - Less explainable (embedding similarity vs exact match)
        
    Design Decision:
        Gets only 20% weight in consensus scoring (Milestone 3)
        because it's less reliable than deterministic regex.
        Should NEVER trigger crisis alone.
        
    What Happens If This Fails:
        - Obfuscated crisis language won't be detected
        - System falls back to regex (misses obfuscation)
        - Add logging to analyze() to debug similarity scores
    """
    
    def __init__(self, patterns: Dict, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize semantic strategy with sentence transformer model.
        
        Args:
            patterns: Crisis patterns dict from YAML
            model_name: Sentence transformer model name
                       Default: 'all-MiniLM-L6-v2'
                       - 384-dimensional embeddings
                       - ~80MB model size
                       - Optimized for CPU inference
                       
        Side Effects:
            - Downloads model on first use (~80MB)
            - Pre-computes embeddings for all crisis phrases
            - Loads model to CPU (not GPU)
            
        Performance:
            - Model loading: ~2-3 seconds (first time only)
            - Embedding computation: ~50-100ms for all patterns
            - Memory: ~200MB (model + embeddings)
            
        Example:
            patterns = load_patterns("config/crisis_patterns.yaml")
            strategy = SemanticDetectionStrategy(patterns)
            # Model downloaded and embeddings pre-computed
        """
        self.patterns = patterns
        self.similarity_threshold = 0.75  # Minimum cosine similarity to consider match
        
        # Load semantic model
        logger.info("loading_semantic_model", model=model_name)
        self.model = SentenceTransformer(model_name)
        self.model.to('cpu')  # CPU inference is fast enough (<50ms)
        
        # Pre-compute crisis embeddings for fast lookup
        self.crisis_embeddings = self._precompute_embeddings()
        
        logger.info(
            "semantic_strategy_initialized",
            categories=len(self.crisis_embeddings),
            threshold=self.similarity_threshold
        )
    
    def _precompute_embeddings(self) -> Dict:
        """
        Pre-compute embeddings for all crisis phrases at initialization.
        
        Why Pre-compute:
            - Encoding is expensive (~10-20ms per phrase)
            - Crisis phrases don't change during runtime
            - Pre-computing reduces analysis latency from ~100ms to ~30ms
            
        Process:
        1. For each crisis category
        2. Encode all phrases to 384-dim embeddings
        3. Store embeddings + metadata for fast lookup
        
        Returns:
            Dict mapping category to embeddings and metadata:
            {
                'category': {
                    'embeddings': numpy array (N x 384),
                    'confidence': 0.95,
                    'phrases': ['phrase1', 'phrase2']
                }
            }
            
        Performance:
            - Time: ~50-100ms for 50 phrases
            - Memory: ~1KB per phrase embedding
            
        Example:
            embeddings['suicidal_ideation'] = {
                'embeddings': array([[0.1, 0.2, ...], [0.3, 0.4, ...]]),
                'confidence': 0.95,
                'phrases': ['want to die', 'kill myself']
            }
        """
        embeddings = {}
        
        for category, config in self.patterns['crisis_keywords'].items():
            phrases = config['patterns']
            
            # Encode all phrases for this category
            # show_progress_bar=False to avoid console spam
            emb = self.model.encode(
                phrases,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            embeddings[category] = {
                'embeddings': emb,  # Shape: (num_phrases, 384)
                'confidence': config['confidence'],
                'phrases': phrases
            }
        
        return embeddings
    
    def analyze(self, message: str, context: List[str] = None) -> Tuple[float, List[str]]:
        """
        Analyze message using semantic similarity with context window.
        
        Process:
        1. Build contextual message (current + last 3 messages)
        2. Encode contextual message to 384-dim embedding
        3. Compare against all pre-computed crisis embeddings
        4. Find highest similarity match
        5. Apply threshold (0.75) and weight by category confidence
        
        Args:
            message: Student message to analyze (required)
            context: Optional list of previous messages
                    Uses last 3 messages for context window
                    Helps disambiguate: "checking out early" from class vs life
                    
        Returns:
            Tuple of (weighted_score, matched_categories)
            - weighted_score: similarity * category_confidence (0.0-1.0)
            - matched_categories: List with "semantic:category" prefix
            
        Context Window:
            - Size: Last 3 messages
            - Separator: " [CONTEXT] "
            - Example: "msg1 [CONTEXT] msg2 [CONTEXT] msg3 [CONTEXT] current"
            - Why 3: Balance between context and token limit (512 tokens)
            
        Similarity Threshold:
            - 0.75 minimum cosine similarity to consider match
            - Lower = more false positives
            - Higher = more false negatives
            - Tuned based on evaluation data
            
        Performance:
            - Without context: ~20ms
            - With context (3 messages): ~25-30ms
            - Bottleneck: Encoding step (~20ms)
            
        Examples:
            # Without context - ambiguous
            score, matches = strategy.analyze("I'm checking out early")
            # score ~0.6 (below threshold, no match)
            
            # With crisis context - clear intent
            score, matches = strategy.analyze(
                "I'm checking out early",
                context=["I can't take it anymore", "Everything is hopeless"]
            )
            # score ~0.85, matches == ['semantic:suicidal_ideation']
            
            # Obfuscated language detected
            score, matches = strategy.analyze("Time to disappear forever")
            # score ~0.80, matches == ['semantic:suicidal_ideation']
            
        Debug:
            If not matching expected phrases:
            1. Check similarity scores in logs (logger.debug)
            2. Verify threshold (0.75 may be too high)
            3. Test with more context messages
            4. Check if phrase is in crisis_patterns.yaml
        """
        # Build contextual message
        # Combine last 3 messages with current for better understanding
        if context and len(context) > 0:
            # Take last 3 messages for context
            recent_context = context[-3:] if len(context) >= 3 else context
            contextual_message = " [CONTEXT] ".join(recent_context + [message])
            
            logger.debug(
                "semantic_with_context",
                context_messages=len(recent_context),
                total_length=len(contextual_message)
            )
        else:
            contextual_message = message
        
        # Encode message with context to 384-dim embedding
        message_emb = self.model.encode(
            [contextual_message],
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        max_similarity = 0.0
        matched_category = None
        best_phrase = None
        
        # Compare against all crisis embeddings using cosine similarity
        for category, config in self.crisis_embeddings.items():
            crisis_embs = config['embeddings']  # Shape: (num_phrases, 384)
            
            # Cosine similarity via dot product (embeddings are normalized)
            # Result shape: (num_phrases,)
            similarities = np.dot(crisis_embs, message_emb.T).flatten()
            max_sim_idx = similarities.argmax()
            max_sim = similarities[max_sim_idx]
            
            if max_sim > max_similarity:
                max_similarity = max_sim
                matched_category = category
                best_phrase = config['phrases'][max_sim_idx]
        
        # Apply threshold and weight by category confidence
        if max_similarity > self.similarity_threshold and matched_category:
            category_confidence = self.crisis_embeddings[matched_category]['confidence']
            score = max_similarity * category_confidence
            
            logger.debug(
                "semantic_match",
                category=matched_category,
                similarity=max_similarity,
                matched_phrase=best_phrase,
                score=score,
                used_context=context is not None and len(context) > 0
            )
            
            # Prefix with "semantic:" to distinguish from regex matches
            return score, [f"semantic:{matched_category}"]
        
        return 0.0, []
    
    def get_name(self) -> str:
        """Return strategy identifier for logging."""
        return "semantic"
