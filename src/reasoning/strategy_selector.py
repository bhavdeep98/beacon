"""
Strategy Selector - Intelligent Strategy Selection

Chooses between Fast and Expert strategies based on context.

Tenet #11: Graceful Degradation - Falls back to Fast if Expert fails
Tenet #15: Performance Is a Safety Feature - Meets <2s SLA
"""

from typing import List, Optional
import structlog
from src.reasoning.strategies import ReasoningStrategy, FastEmotionStrategy, ExpertLLMStrategy

logger = structlog.get_logger()


class StrategySelector:
    """
    Selects optimal reasoning strategy based on message context.
    
    Design:
    - Fast Strategy: Default for routine conversations (<100ms)
    - Expert Strategy: High-risk or ambiguous cases (with timeout)
    - Circuit Breaker: Automatic fallback if Expert repeatedly fails
    """
    
    def __init__(
        self,
        expert_timeout: float = 120.0,  # 2 minutes - Safety over speed (Tenet #1)
        max_expert_failures: int = 3
    ):
        """
        Initialize strategy selector.
        
        Args:
            expert_timeout: Max seconds to wait for Expert (default: 120s)
                          Tenet #1: Safety First - Mental health model needs time
                          Tenet #8: Engagement - "Thinking" animation builds trust
            max_expert_failures: Failures before circuit opens (default: 3)
        """
        self.fast_strategy = FastEmotionStrategy()
        self.expert_strategy = ExpertLLMStrategy()
        self.expert_timeout = expert_timeout
        self.max_expert_failures = max_expert_failures
        self.expert_failures = 0
        
        logger.info(
            "strategy_selector_initialized",
            expert_timeout=expert_timeout,
            max_failures=max_expert_failures
        )
    
    def select_strategy(
        self,
        message: str,
        context: Optional[List[str]] = None,
        preliminary_risk: Optional[float] = None
    ) -> tuple[ReasoningStrategy, str]:
        """
        Select strategy based on risk indicators.
        
        Args:
            message: Student's message
            context: Conversation history
            preliminary_risk: Risk score from Fast Strategy (0.0-1.0)
            
        Returns:
            Tuple of (strategy, reason)
            
        Selection Logic:
        1. Circuit breaker open → Fast
        2. Crisis keywords detected → Expert
        3. High preliminary risk (>0.7) → Expert
        4. Ambiguous content → Expert
        5. Otherwise → Fast
        """
        if context is None:
            context = []
        
        # Check circuit breaker
        if self.is_circuit_open():
            logger.warning(
                "expert_circuit_open",
                failures=self.expert_failures,
                max_failures=self.max_expert_failures
            )
            return self.fast_strategy, "circuit_breaker_open"
        
        # Check for explicit crisis keywords
        if self._has_crisis_keywords(message):
            logger.info("expert_selected", reason="crisis_keywords_detected")
            return self.expert_strategy, "crisis_keywords"
        
        # Check preliminary risk score
        if preliminary_risk and preliminary_risk > 0.7:
            logger.info(
                "expert_selected",
                reason="high_preliminary_risk",
                risk_score=preliminary_risk
            )
            return self.expert_strategy, "high_risk"
        
        # Check for ambiguous content
        if self._is_ambiguous(message, context):
            logger.info("expert_selected", reason="ambiguous_content")
            return self.expert_strategy, "ambiguous"
        
        # Default to Fast Strategy
        logger.info("fast_selected", reason="routine_conversation")
        return self.fast_strategy, "routine"
    
    def _has_crisis_keywords(self, message: str) -> bool:
        """
        Check for explicit crisis markers.
        
        These keywords always trigger Expert analysis for safety.
        """
        crisis_keywords = [
            # Suicidal ideation
            "kill myself", "end my life", "want to die", "suicide",
            "not worth living", "better off dead",
            
            # Self-harm
            "hurt myself", "self harm", "cut myself",
            
            # Intent/plan
            "going to", "plan to", "tonight", "pills"
        ]
        
        message_lower = message.lower()
        matched = [kw for kw in crisis_keywords if kw in message_lower]
        
        if matched:
            logger.warning(
                "crisis_keywords_matched",
                keywords=matched,
                message_hash=hash(message)
            )
        
        return len(matched) > 0
    
    def _is_ambiguous(self, message: str, context: List[str]) -> bool:
        """
        Detect ambiguous cases that need Expert analysis.
        
        Heuristics:
        - Short messages with negative words
        - Contradictory emotions
        - Sudden topic shifts
        - Vague distress signals
        """
        message_lower = message.lower()
        words = message.split()
        
        # Negative indicators
        negative_words = [
            "bad", "terrible", "awful", "hate", "can't",
            "never", "always", "nothing", "everything"
        ]
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        # Vague distress
        vague_distress = [
            "i don't know", "i can't", "everything is",
            "nothing works", "what's the point"
        ]
        has_vague = any(phrase in message_lower for phrase in vague_distress)
        
        # Short + negative = ambiguous
        is_short = len(words) < 15
        is_ambiguous = (is_short and negative_count >= 2) or has_vague
        
        if is_ambiguous:
            logger.info(
                "ambiguous_content_detected",
                message_length=len(words),
                negative_count=negative_count,
                has_vague=has_vague
            )
        
        return is_ambiguous
    
    def is_circuit_open(self) -> bool:
        """Check if Expert circuit breaker is open."""
        return self.expert_failures >= self.max_expert_failures
    
    def record_expert_success(self):
        """Reset failure counter on Expert success."""
        if self.expert_failures > 0:
            logger.info(
                "expert_success_resetting_failures",
                previous_failures=self.expert_failures
            )
        self.expert_failures = 0
    
    def record_expert_failure(self):
        """Increment failure counter."""
        self.expert_failures += 1
        
        logger.warning(
            "expert_failure_recorded",
            failures=self.expert_failures,
            max_failures=self.max_expert_failures,
            circuit_will_open=self.is_circuit_open()
        )
        
        if self.is_circuit_open():
            logger.critical(
                "expert_circuit_breaker_opened",
                failures=self.expert_failures,
                action="falling_back_to_fast_strategy"
            )
    
    def get_stats(self) -> dict:
        """Get selector statistics for monitoring."""
        return {
            "expert_failures": self.expert_failures,
            "max_failures": self.max_expert_failures,
            "circuit_open": self.is_circuit_open(),
            "expert_timeout": self.expert_timeout
        }
