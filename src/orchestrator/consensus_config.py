"""
Consensus Configuration

Tenet #9: Configuration over code
Tenet #5: Make Illegal States Unrepresentable
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ConsensusConfig:
    """
    Configuration for consensus orchestrator.
    
    All weights and thresholds are configurable to support:
    - Weight learning/optimization
    - A/B testing
    - School-specific tuning
    """
    # Layer weights (must sum to 1.0)
    w_regex: float = 0.40
    w_semantic: float = 0.20
    w_mistral: float = 0.30
    w_history: float = 0.10
    
    # Decision thresholds
    crisis_threshold: float = 0.90
    caution_threshold: float = 0.65
    
    # Timeout settings (seconds)
    mistral_timeout: float = 3.0
    total_timeout: float = 5.0
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5  # failures before opening
    circuit_breaker_timeout: int = 30  # seconds before retry
    
    def __post_init__(self):
        """Validate configuration."""
        # Weights must sum to 1.0 (with small tolerance for floating point)
        weight_sum = self.w_regex + self.w_semantic + self.w_mistral + self.w_history
        if not 0.99 <= weight_sum <= 1.01:
            raise ValueError(
                f"Weights must sum to 1.0, got {weight_sum:.4f} "
                f"(regex={self.w_regex}, semantic={self.w_semantic}, "
                f"mistral={self.w_mistral}, history={self.w_history})"
            )
        
        # All weights must be non-negative
        if any(w < 0 for w in [self.w_regex, self.w_semantic, self.w_mistral, self.w_history]):
            raise ValueError("All weights must be non-negative")
        
        # Thresholds must be in valid range
        if not 0.0 <= self.crisis_threshold <= 1.0:
            raise ValueError(f"Crisis threshold must be 0.0-1.0, got {self.crisis_threshold}")
        if not 0.0 <= self.caution_threshold <= 1.0:
            raise ValueError(f"Caution threshold must be 0.0-1.0, got {self.caution_threshold}")
        
        # Crisis threshold must be higher than caution
        if self.crisis_threshold <= self.caution_threshold:
            raise ValueError(
                f"Crisis threshold ({self.crisis_threshold}) must be > "
                f"caution threshold ({self.caution_threshold})"
            )
        
        # Timeouts must be positive
        if self.mistral_timeout <= 0:
            raise ValueError(f"Mistral timeout must be positive, got {self.mistral_timeout}")
        if self.total_timeout <= 0:
            raise ValueError(f"Total timeout must be positive, got {self.total_timeout}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "weights": {
                "regex": self.w_regex,
                "semantic": self.w_semantic,
                "mistral": self.w_mistral,
                "history": self.w_history,
            },
            "thresholds": {
                "crisis": self.crisis_threshold,
                "caution": self.caution_threshold,
            },
            "timeouts": {
                "mistral": self.mistral_timeout,
                "total": self.total_timeout,
            },
            "circuit_breaker": {
                "enabled": self.circuit_breaker_enabled,
                "threshold": self.circuit_breaker_threshold,
                "timeout": self.circuit_breaker_timeout,
            },
        }
