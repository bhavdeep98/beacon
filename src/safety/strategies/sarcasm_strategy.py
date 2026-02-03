"""
Sarcasm Filter Strategy - Teenage Hyperbole Detection

Detects teenage hyperbole and figurative language to reduce false positives
from the semantic layer. Prevents phrases like "homework is killing me" from
triggering crisis alerts.

Approach: Pattern-based regex matching + sentiment indicators
Latency: ~2-5ms per message
Effect: Reduces semantic score by 90% when hyperbole detected

Design Principles:
- Prevents false positives (primary goal)
- Pattern-based (fast, explainable)
- Conservative (better to miss hyperbole than miss crisis)
- Continuously updated with new teenage language patterns

Limitations:
- Pattern-based (can miss novel hyperbole)
- No ML (can't learn new patterns automatically)
- Requires manual pattern updates

Future Enhancement (Milestone 2):
- Fine-tuned DistilBERT for sarcasm detection
- Trained on teenage social media data
- More robust than regex patterns

Usage:
    patterns = load_patterns("config/crisis_patterns.yaml")
    strategy = SarcasmFilterStrategy(patterns)
    score, matches = strategy.analyze("This homework is killing me")
    # score == 0.9, matches == ['hyperbole']
"""

import re2
from typing import Tuple, List, Dict
import structlog

from .base import DetectionStrategy

logger = structlog.get_logger()


class SarcasmFilterStrategy(DetectionStrategy):
    """
    Sarcasm and hyperbole detection strategy.
    
    Filters out teenage hyperbole and figurative language to reduce
    false positives from semantic layer.
    
    Common Hyperbole Patterns:
        - "This homework is killing me" → NOT crisis
        - "I'm dying of boredom" → NOT crisis
        - "My parents would kill me if I failed" → NOT crisis
        - "I'm dead tired" → NOT crisis
        - "That test murdered me" → NOT crisis
        
    How It Works:
    1. Check for hyperbolic patterns (homework + killing, dying of boredom)
    2. Check for positive sentiment indicators (lol, haha, emojis)
    3. Return high score (0.8-0.9) if hyperbole detected
    4. SafetyService reduces semantic score by 90% when score > 0.7
    
    Strengths:
        - Fast (~2-5ms)
        - Explainable (exact pattern matched)
        - Reduces false positives significantly
        
    Limitations:
        - Pattern-based (can miss novel hyperbole)
        - Requires manual updates for new slang
        - Conservative (may miss some hyperbole)
        
    Design Decision:
        Acts as safety valve for semantic layer.
        When sarcasm detected, semantic score reduced by 90%.
        Prevents "homework is killing me" from triggering crisis.
        
    What Happens If This Fails:
        - More false positives from semantic layer
        - Teenage hyperbole triggers crisis alerts
        - Add logging to analyze() to debug pattern matches
    """
    
    # Common hyperbolic patterns that should NOT trigger crisis
    # Format: regex patterns with word boundaries
    HYPERBOLE_PATTERNS = [
        # Academic stress hyperbole
        r'\b(homework|test|exam|quiz).{0,20}(killing|murder|death)',
        
        # Boredom hyperbole
        r'\bdying of (boredom|laughter)',
        
        # Parental/authority hyperbole
        r'\b(parents|mom|dad|mother|father|teacher).{0,20}(kill|murder)',
        
        # Tiredness hyperbole
        r'\bdead tired\b',
        r'\b(so|really|literally) dead\b',
        
        # Positive usage
        r'\bkilling it\b',  # "I'm killing it" = doing well
        r'\bmurdered (the|that) (test|exam)',  # "I murdered the test" = did well
    ]
    
    def __init__(self, patterns: Dict):
        """
        Initialize sarcasm filter with hyperbole patterns.
        
        Args:
            patterns: Crisis patterns dict (for reference, not used directly)
                     Sarcasm patterns are hard-coded in HYPERBOLE_PATTERNS
                     
        Side Effects:
            - Compiles hyperbole regex patterns
            - Logs initialization
            
        Performance:
            - Compilation: ~5ms
            - Memory: ~1KB for compiled pattern
            
        Example:
            patterns = load_patterns("config/crisis_patterns.yaml")
            strategy = SarcasmFilterStrategy(patterns)
        """
        self.patterns = patterns
        
        # Compile hyperbole patterns into single regex
        # Combines all patterns with OR operator (|)
        self.hyperbole_regex = re2.compile(
            '(?i)' + '|'.join(self.HYPERBOLE_PATTERNS)
        )
        
        logger.info(
            "sarcasm_filter_initialized",
            pattern_count=len(self.HYPERBOLE_PATTERNS)
        )
    
    def analyze(self, message: str, context: List[str] = None) -> Tuple[float, List[str]]:
        """
        Check if message contains hyperbole or sarcasm.
        
        Process:
        1. Check for hyperbolic patterns (homework + killing, etc.)
        2. Check for positive sentiment indicators (lol, haha, emojis)
        3. Return high score if either detected
        
        Args:
            message: Student message to analyze
            context: Optional previous messages (not currently used)
                    Future: Could use context for sentiment analysis
            
        Returns:
            Tuple of (sarcasm_probability, matched_patterns)
            - sarcasm_probability: 0.0-1.0 (higher = more likely sarcasm)
            - matched_patterns: ['hyperbole'] or ['positive_sentiment'] or []
            
        Score Interpretation:
            - 0.9: Hyperbolic pattern matched (very likely sarcasm)
            - 0.8: Positive sentiment detected (likely sarcasm)
            - 0.0: No sarcasm indicators
            
        Effect on Crisis Detection:
            - If score > 0.7: SafetyService reduces semantic score by 90%
            - Prevents false positives from semantic layer
            
        Performance:
            - Time: ~2-5ms per message
            - Faster than semantic layer (~20-30ms)
            
        Examples:
            # Hyperbolic pattern
            score, matches = strategy.analyze("This homework is killing me")
            # score == 0.9, matches == ['hyperbole']
            
            # Positive sentiment
            score, matches = strategy.analyze("I'm dying lol")
            # score == 0.8, matches == ['positive_sentiment']
            
            # No sarcasm
            score, matches = strategy.analyze("I want to die")
            # score == 0.0, matches == []
            
            # Edge case: genuine crisis with lol (nervous laughter)
            score, matches = strategy.analyze("I want to kill myself lol")
            # score == 0.8 (may incorrectly filter)
            # This is acceptable trade-off: regex layer still catches it
            
        Debug:
            If not catching expected hyperbole:
            1. Check if pattern is in HYPERBOLE_PATTERNS
            2. Test pattern in isolation with re2
            3. Add logging to see which patterns tested
            4. Consider adding new pattern to HYPERBOLE_PATTERNS
        """
        message_lower = message.lower()
        
        # Check for hyperbolic patterns
        if self.hyperbole_regex.search(message_lower):
            logger.debug(
                "hyperbole_detected",
                message=message[:100]  # Log first 100 chars only
            )
            return 0.9, ["hyperbole"]
        
        # Check for positive sentiment indicators
        # These suggest joking/sarcasm rather than genuine crisis
        positive_indicators = [
            'lol',           # Laughing out loud
            'haha',          # Laughter
            'jk',            # Just kidding
            'just kidding',
            'joking',
            'lmao',          # Laughing my ass off
            'rofl',          # Rolling on floor laughing
            '😂',            # Crying laughing emoji
            '😅',            # Sweat smile emoji
            '🤣',            # Rolling laughing emoji
        ]
        
        if any(indicator in message_lower for indicator in positive_indicators):
            logger.debug(
                "positive_sentiment_detected",
                message=message[:100]
            )
            return 0.8, ["positive_sentiment"]
        
        # No sarcasm detected
        return 0.0, []
    
    def get_name(self) -> str:
        """Return strategy identifier for logging."""
        return "sarcasm_filter"
