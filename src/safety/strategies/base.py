"""
Base Detection Strategy - Abstract Interface

Defines the contract that all crisis detection strategies must implement.
Part of the Strategy Pattern for pluggable detection layers.

Design Pattern: Strategy Pattern
- Allows runtime selection of detection algorithms
- Each strategy is independently testable
- Easy to add new detection methods (e.g., Mistral reasoning in Milestone 2)

Usage:
    class MyStrategy(DetectionStrategy):
        def analyze(self, message, context=None):
            # Implementation
            return score, patterns
        
        def get_name(self):
            return "my_strategy"
"""

from abc import ABC, abstractmethod
from typing import Tuple, List


class DetectionStrategy(ABC):
    """
    Abstract base class for all crisis detection strategies.
    
    All detection strategies must implement:
    1. analyze() - Analyze message and return confidence score
    2. get_name() - Return strategy identifier for logging
    
    Design Principles:
        - Strategies are stateless (thread-safe)
        - analyze() is idempotent (same input = same output)
        - Scores normalized to 0.0-1.0 range
        - Matched patterns returned for explainability
        
    Example Implementation:
        class SimpleStrategy(DetectionStrategy):
            def analyze(self, message, context=None):
                if "crisis" in message.lower():
                    return 0.9, ["crisis_keyword"]
                return 0.0, []
            
            def get_name(self):
                return "simple"
    """
    
    @abstractmethod
    def analyze(self, message: str, context: List[str] = None) -> Tuple[float, List[str]]:
        """
        Analyze message for crisis indicators.
        
        Args:
            message: Student message to analyze (required)
            context: Optional list of previous messages for context
                    Strategies may use context differently:
                    - Regex: ignores context (deterministic)
                    - Semantic: uses last 3 messages for disambiguation
                    - Sarcasm: may use context for sentiment analysis
            
        Returns:
            Tuple of (confidence_score, matched_patterns)
            - confidence_score: Float 0.0-1.0 indicating crisis probability
            - matched_patterns: List of matched crisis categories
                               Example: ['suicidal_ideation', 'self_harm']
                               
        Design Requirements:
            - Must be idempotent (same input = same output)
            - Must complete in <50ms for real-time analysis
            - Must handle empty/None context gracefully
            - Must return normalized scores (0.0-1.0)
            
        Example:
            score, patterns = strategy.analyze("I want to die")
            # score == 0.95, patterns == ['suicidal_ideation']
            
            score, patterns = strategy.analyze(
                "I'm checking out early",
                context=["I can't take it", "Everything is hopeless"]
            )
            # Context helps disambiguate intent
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return strategy name for logging and identification.
        
        Returns:
            String identifier for this strategy
            Examples: "regex", "semantic", "sarcasm_filter", "mistral"
            
        Usage:
            Used for:
            - Logging which strategy detected crisis
            - Mapping strategies in SafetyService
            - Debugging and monitoring
            
        Example:
            name = strategy.get_name()
            logger.info(f"{name}_analysis_complete", score=score)
        """
        pass
