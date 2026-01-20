"""
Regex Detection Strategy - Deterministic Crisis Keyword Matching

Uses Google's RE2 regex engine for exact keyword matching with word boundaries.
Provides the "safety floor" - guaranteed to catch explicit crisis language.

Performance: O(n) time complexity, prevents ReDoS attacks
Latency: ~5-10ms per message

Design Principles:
- Deterministic (same input = same output, always)
- No false negatives on explicit keywords
- Word boundaries prevent partial matches ("alive" vs "I want to be alive")
- Configurable via YAML (non-engineers can update patterns)

Usage:
    patterns = load_patterns("config/crisis_patterns.yaml")
    strategy = RegexDetectionStrategy(patterns)
    score, matches = strategy.analyze("I want to die")
    # score == 0.95, matches == ['suicidal_ideation']
"""

import re2
from typing import Tuple, List, Dict
import structlog

from .base import DetectionStrategy

logger = structlog.get_logger()


class RegexDetectionStrategy(DetectionStrategy):
    """
    Deterministic regex-based crisis detection.
    
    The "Safety Floor" - highest trust detection layer.
    Uses RE2 for O(n) performance and ReDoS prevention.
    Matches explicit crisis keywords with word boundaries.
    
    Strengths:
        - 100% recall on explicit keywords
        - Deterministic (no ML uncertainty)
        - Fast (~5-10ms)
        - Explainable (exact pattern matched)
        
    Limitations:
        - Misses obfuscated language ("checking out early")
        - Misses novel phrasings
        - Requires pattern maintenance
        
    Pattern Structure:
        Each category has:
        - patterns: List of crisis phrases
        - confidence: Score 0.0-1.0 (higher = more severe)
        
    Example Patterns:
        suicidal_ideation:
          patterns: ["want to die", "kill myself"]
          confidence: 0.95
          
    What Happens If This Fails:
        - Crisis keywords won't be detected
        - System falls back to semantic layer (less reliable)
        - Add logging to _compile_patterns() to debug
    """
    
    def __init__(self, patterns: Dict):
        """
        Initialize regex strategy with crisis patterns.
        
        Args:
            patterns: Crisis patterns dict from YAML with structure:
                     {'crisis_keywords': {'category': {'patterns': [...], 'confidence': 0.95}}}
                     
        Side Effects:
            - Compiles all regex patterns at initialization
            - Logs number of categories loaded
            
        Performance:
            - Compilation: ~10-20ms for 50 patterns
            - Memory: ~1KB per compiled pattern
            
        Example:
            patterns = {
                'crisis_keywords': {
                    'suicidal_ideation': {
                        'patterns': ['want to die', 'kill myself'],
                        'confidence': 0.95
                    }
                }
            }
            strategy = RegexDetectionStrategy(patterns)
        """
        self.patterns = patterns
        self.compiled_patterns = self._compile_patterns()
        
        logger.info(
            "regex_strategy_initialized",
            categories=len(self.compiled_patterns)
        )
    
    def _compile_patterns(self) -> Dict:
        """
        Compile regex patterns with word boundaries for exact matching.
        
        Process:
        1. Escape each pattern to prevent regex injection
        2. Combine patterns with OR operator (|)
        3. Add word boundaries (\b) for exact word matching
        4. Compile with case-insensitive flag
        
        Returns:
            Dict mapping category to compiled pattern and metadata:
            {
                'category': {
                    'pattern': compiled_re2_pattern,
                    'confidence': 0.95,
                    'raw_patterns': ['phrase1', 'phrase2']
                }
            }
            
        Word Boundary Examples:
            Pattern: "die"
            - Matches: "I want to die" ✓
            - Doesn't match: "studied" ✗ (die is part of word)
            
        Security:
            - Uses re2.escape() to prevent regex injection
            - RE2 prevents ReDoS (Regular Expression Denial of Service)
            
        Debug:
            Add logging here to see which patterns are compiled:
            logger.debug("compiling_pattern", category=category, pattern=combined)
        """
        compiled = {}
        
        for category, config in self.patterns['crisis_keywords'].items():
            patterns = config['patterns']
            
            # Escape and combine with word boundaries
            # re2.escape prevents regex injection attacks
            pattern_parts = [re2.escape(p) for p in patterns]
            combined = r'(?i)\b(' + '|'.join(pattern_parts) + r')\b'
            
            compiled[category] = {
                'pattern': re2.compile(combined),
                'confidence': config['confidence'],
                'raw_patterns': patterns
            }
        
        return compiled
    
    def analyze(self, message: str, context: List[str] = None) -> Tuple[float, List[str]]:
        """
        Analyze message using regex matching (deterministic).
        
        Process:
        1. Convert message to lowercase
        2. Test each compiled pattern
        3. Track highest confidence score
        4. Return max confidence and all matched categories
        
        Args:
            message: Student message to analyze
            context: Optional previous messages (NOT USED by regex)
                    Regex is deterministic and context-independent
            
        Returns:
            Tuple of (max_confidence, matched_categories)
            - max_confidence: Highest confidence from matched patterns
            - matched_categories: List of all matched crisis categories
            
        Performance:
            - Time: O(n) where n = message length
            - Typical: ~5-10ms per message
            - Worst case: ~20ms for very long messages
            
        Examples:
            # Explicit crisis keyword
            score, matches = strategy.analyze("I want to die")
            # score == 0.95, matches == ['suicidal_ideation']
            
            # Multiple matches
            score, matches = strategy.analyze("I want to die and hurt myself")
            # score == 0.95, matches == ['suicidal_ideation', 'self_harm']
            
            # No match
            score, matches = strategy.analyze("I'm feeling sad")
            # score == 0.0, matches == []
            
            # Word boundary protection
            score, matches = strategy.analyze("I feel alive")
            # score == 0.0 (doesn't match "die" pattern)
            
        Debug:
            If patterns not matching:
            1. Check pattern is in YAML config
            2. Verify word boundaries (whole words only)
            3. Add logging in loop to see which patterns tested
        """
        message_lower = message.lower()
        max_confidence = 0.0
        matched_patterns = []
        
        for category, config in self.compiled_patterns.items():
            match = config['pattern'].search(message_lower)
            if match:
                matched_patterns.append(category)
                max_confidence = max(max_confidence, config['confidence'])
                
                logger.debug(
                    "regex_match",
                    category=category,
                    matched_text=match.group(0),
                    confidence=config['confidence']
                )
        
        return max_confidence, matched_patterns
    
    def get_name(self) -> str:
        """Return strategy identifier for logging."""
        return "regex"
