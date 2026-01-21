"""
Consensus Result - Immutable output from orchestrator

Tenet #7: Immutability by Default
Tenet #9: Visibility and Explainability at Every Layer
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class RiskLevel(Enum):
    """Risk level classification."""
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    CRISIS = "CRISIS"


@dataclass(frozen=True)
class LayerScore:
    """Score from a single detection layer."""
    layer_name: str
    score: float
    latency_ms: int
    matched_patterns: List[str]
    evidence: str
    
    def __post_init__(self):
        """Validate score range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be 0.0-1.0, got {self.score}")


@dataclass(frozen=True)
class ConsensusResult:
    """
    Immutable result from consensus orchestrator.
    
    Contains all information needed for:
    - Crisis response (risk_level, final_score)
    - Counselor dashboard (layer_scores, reasoning)
    - Debugging (latency_ms, timeout_occurred)
    - Audit trail (all fields)
    """
    # Final decision
    risk_level: RiskLevel
    final_score: float
    
    # Individual layer scores (for explainability)
    regex_score: LayerScore
    semantic_score: LayerScore
    mistral_score: Optional[LayerScore]  # None if timeout
    
    # Reasoning trace
    reasoning: str
    matched_patterns: List[str]
    
    # Performance metrics
    total_latency_ms: int
    timeout_occurred: bool
    
    # Weights used (for audit trail)
    weights_used: dict
    
    def __post_init__(self):
        """Validate final score range."""
        if not 0.0 <= self.final_score <= 1.0:
            raise ValueError(f"Final score must be 0.0-1.0, got {self.final_score}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/storage."""
        return {
            "risk_level": self.risk_level.value,
            "final_score": self.final_score,
            "regex_score": {
                "score": self.regex_score.score,
                "latency_ms": self.regex_score.latency_ms,
                "patterns": self.regex_score.matched_patterns,
            },
            "semantic_score": {
                "score": self.semantic_score.score,
                "latency_ms": self.semantic_score.latency_ms,
                "patterns": self.semantic_score.matched_patterns,
            },
            "mistral_score": {
                "score": self.mistral_score.score if self.mistral_score else None,
                "latency_ms": self.mistral_score.latency_ms if self.mistral_score else None,
                "patterns": self.mistral_score.matched_patterns if self.mistral_score else [],
            } if self.mistral_score else None,
            "reasoning": self.reasoning,
            "matched_patterns": self.matched_patterns,
            "total_latency_ms": self.total_latency_ms,
            "timeout_occurred": self.timeout_occurred,
            "weights_used": self.weights_used,
        }
    
    def is_crisis(self) -> bool:
        """Check if this is a crisis."""
        return self.risk_level == RiskLevel.CRISIS
    
    def is_caution(self) -> bool:
        """Check if this requires caution."""
        return self.risk_level == RiskLevel.CAUTION
    
    def is_safe(self) -> bool:
        """Check if this is safe."""
        return self.risk_level == RiskLevel.SAFE
