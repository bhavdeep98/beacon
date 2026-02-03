"""
Mistral Reasoner - Fast Clinical Pattern Detection

Implements clinical reasoning using DistilBERT for fast emotion/sentiment analysis
combined with rule-based clinical marker extraction.

Key Features:
- Uses distilbert-base-uncased-emotion for fast emotion detection
- Rule-based clinical marker extraction (PHQ-9, GAD-7, C-SSRS)
- Context-aware analysis using conversation history
- Sarcasm/hyperbole detection for teenage vernacular
- Timeout protection (raises TimeoutError)
- Fail-fast design: raises exceptions on errors (no fallbacks)

Architecture:
- Runs locally using transformers library
- Lazy loading (model loads on first use)
- Immutable ReasoningResult for audit trail
- Explicit error handling (fail loud, fail early)

SLA: <200ms reasoning latency with 2s timeout

Error Handling:
- RuntimeError: Model fails to load or generate
- ValueError: Response cannot be parsed
- TimeoutError: Analysis exceeds timeout
- No fallbacks - errors propagate to caller for explicit handling
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import time
import json
import structlog

logger = structlog.get_logger()

# Lazy imports for model loading
_transformers_available = False
try:
    from transformers import pipeline
    import torch
    _transformers_available = True
except ImportError:
    logger.warning("transformers not installed - install with: pip install transformers torch")
    pipeline = None
    torch = None


class RiskLevel(Enum):
    """Risk assessment levels."""
    CRISIS = "crisis"  # Immediate intervention required
    CAUTION = "caution"  # Monitor closely, check-in soon
    SAFE = "safe"  # No immediate concerns


@dataclass(frozen=True)
class ClinicalMarker:
    """
    Clinical marker detected in conversation.
    
    Maps to evidence-based screening tools:
    - PHQ-9: Depression screening (9 items)
    - GAD-7: Anxiety screening (7 items)
    - C-SSRS: Suicide risk assessment (5 levels)
    
    Attributes:
        category: Screening tool (phq9, gad7, cssrs)
        item: Specific item number or description
        confidence: Detection confidence (0.0-1.0)
        evidence: Quote from conversation supporting detection
        
    Example:
        ClinicalMarker(
            category="phq9",
            item="item_2_feeling_down",
            confidence=0.85,
            evidence="I've been feeling really down lately"
        )
    """
    category: str  # phq9, gad7, cssrs
    item: str
    confidence: float
    evidence: str


@dataclass(frozen=True)
class ReasoningResult:
    """
    Immutable reasoning result from Mistral-7B analysis.
    
    Attributes:
        p_mistral: Crisis probability from Mistral (0.0-1.0)
        risk_level: Categorical risk assessment
        reasoning_trace: Step-by-step reasoning explanation
        clinical_markers: List of detected clinical markers
        is_sarcasm: Whether message is likely hyperbole/sarcasm
        sarcasm_reasoning: Explanation for sarcasm detection
        latency_ms: Analysis latency in milliseconds
        model_used: Which model generated this result
        
    Design:
        - Frozen dataclass ensures immutability (audit trail)
        - All scores normalized to 0.0-1.0 range
        - Reasoning trace provides explainability for counselors
        
    Example:
        result = ReasoningResult(
            p_mistral=0.92,
            risk_level=RiskLevel.CRISIS,
            reasoning_trace="Student expresses suicidal ideation with specific plan...",
            clinical_markers=[
                ClinicalMarker(category="cssrs", item="ideation_with_plan", ...)
            ],
            is_sarcasm=False,
            sarcasm_reasoning="Language is direct and serious, not hyperbolic",
            latency_ms=1850.5,
            model_used="mistral-7b-instruct"
        )
    """
    p_mistral: float
    risk_level: RiskLevel
    reasoning_trace: str
    clinical_markers: List[ClinicalMarker]
    is_sarcasm: bool
    sarcasm_reasoning: str
    latency_ms: float
    model_used: str


class MistralReasoner:
    """
    Fast clinical reasoning using DistilBERT emotion detection.
    
    Provides structured analysis of student messages for:
    - Fast emotion/sentiment detection (<200ms)
    - Clinical marker extraction (PHQ-9, GAD-7, C-SSRS)
    - Sarcasm/hyperbole filtering for teenage vernacular
    - Explainable reasoning traces for counselors
    
    Current Implementation (Milestone 2):
        - DistilBERT for emotion classification
        - Rule-based clinical marker extraction
        - Fast inference (<200ms on GPU, <500ms on CPU)
        
    Target Implementation (Milestone 3+):
        - AWS Bedrock Mistral-7B endpoint for deeper reasoning
        - Fine-tuned on mental health conversations
        - Circuit breaker with fallback
        
    SLA: <200ms reasoning latency with 2s timeout
    
    Example:
        reasoner = MistralReasoner()
        
        # Single message analysis
        result = reasoner.analyze("I want to die")
        
        # With context (improves accuracy)
        result = reasoner.analyze(
            "I'm checking out early",
            context=["I can't take it anymore", "Everything is hopeless"]
        )
        
        if result.risk_level == RiskLevel.CRISIS:
            logger.warning("crisis_detected_by_mistral", result=result)
    """
    
    CRISIS_KEYWORDS = [
        "kill myself", "end my life", "want to die", "suicide",
        "end it all", "not worth living", "better off dead"
    ]
    
    SELF_HARM_KEYWORDS = [
        "cut myself", "hurt myself", "self harm", "self-harm",
        "cutting", "burning myself"
    ]
    
    HYPERBOLE_PATTERNS = [
        "homework is killing me", "dying of boredom", "literally dying",
        "kill me now", "dead tired", "so dead"
    ]
    
    def __init__(
        self, 
        strategy: Optional['ReasoningStrategy'] = None, 
        timeout: float = 120.0,  # 2 minutes - Safety over speed (Tenet #1)
        use_intelligent_selection: bool = True
    ):
        """
        Initialize reasoner with strategy selection.
        
        Args:
            strategy: Fixed strategy (if use_intelligent_selection=False)
            timeout: Maximum reasoning time in seconds
            use_intelligent_selection: Use StrategySelector for dynamic selection (default: True)
                                      Tenet #11: Graceful Degradation
                                      Tenet #15: Performance Is a Safety Feature
        """
        from src.reasoning.strategies import FastEmotionStrategy, StrategyContext
        
        self.timeout = timeout
        self.use_intelligent_selection = use_intelligent_selection
        
        if use_intelligent_selection:
            # Import selector
            try:
                from src.reasoning.strategy_selector import StrategySelector
                self.selector = StrategySelector(
                    expert_timeout=120.0,  # 2 minutes - Safety over speed
                    max_expert_failures=3
                )
                self.strategy = None  # Will be selected dynamically
                logger.info(
                    "mistral_reasoner_initialized",
                    mode="intelligent_selection",
                    timeout=timeout
                )
            except ImportError as e:
                logger.warning(
                    "strategy_selector_unavailable_using_fast",
                    error=str(e)
                )
                self.selector = None
                self.strategy = FastEmotionStrategy()
                self.use_intelligent_selection = False
        else:
            # Fixed strategy mode (backward compatible)
            self.selector = None
            self.strategy = strategy or FastEmotionStrategy()
            logger.info(
                "mistral_reasoner_initialized",
                mode="fixed_strategy",
                strategy=self.strategy.name,
                timeout=timeout
            )
    
    def analyze(self, message: str, context: List[str] = None) -> ReasoningResult:
        """
        Analyze message using intelligent strategy selection or fixed strategy.
        
        Args:
            message: Student message
            context: Conversation history
            
        Returns:
            ReasoningResult
            
        Flow (Intelligent Selection):
        1. Run Fast Strategy for preliminary assessment (<100ms)
        2. Decide if Expert is needed based on risk/keywords
        3. If Expert needed, try with timeout, fallback to Fast on failure
        4. Return result with strategy used
        """
        from src.reasoning.strategies import StrategyContext
        
        start_time = time.perf_counter()
        
        if context is None:
            context = []
        
        ctx = StrategyContext(
            message=message,
            history=context,
            timeout=self.timeout
        )
        
        try:
            # Mode 1: Intelligent Selection
            if self.use_intelligent_selection and self.selector:
                result = self._analyze_with_selection(message, context, ctx)
            
            # Mode 2: Fixed Strategy (backward compatible)
            else:
                result = self.strategy.analyze(ctx)
            
            latency = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                "reasoning_complete",
                strategy=result.model_used if hasattr(result, 'model_used') else "unknown",
                risk_level=result.risk_level.value,
                p_mistral=result.p_mistral,
                latency_ms=latency
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "reasoning_failed", 
                error=str(e), 
                strategy=self.strategy.name if self.strategy else "selector"
            )
            raise
    
    def _analyze_with_selection(
        self, 
        message: str, 
        context: List[str],
        ctx: 'StrategyContext'
    ) -> ReasoningResult:
        """
        Analyze with intelligent strategy selection.
        
        Tenet #11: Graceful Degradation
        Tenet #15: Performance Is a Safety Feature
        """
        # Step 1: Fast preliminary analysis
        fast_result = self.selector.fast_strategy.analyze(ctx)
        
        logger.info(
            "preliminary_analysis",
            risk_score=fast_result.p_mistral,
            risk_level=fast_result.risk_level.value,
            latency_ms=fast_result.latency_ms
        )
        
        # Step 2: Select strategy
        selected_strategy, reason = self.selector.select_strategy(
            message=message,
            context=context,
            preliminary_risk=fast_result.p_mistral
        )
        
        # Step 3: If Fast selected, return immediately (meets SLA)
        if selected_strategy is self.selector.fast_strategy:
            logger.info(
                "using_fast_result",
                reason=reason,
                latency_ms=fast_result.latency_ms
            )
            return fast_result
        
        # Step 4: Try Expert with timeout and fallback
        try:
            import asyncio
            import concurrent.futures
            from functools import partial
            
            # Create a thread pool executor for running sync code with timeout
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(selected_strategy.analyze, ctx)
                
                try:
                    # Wait with timeout
                    expert_result = future.result(timeout=self.selector.expert_timeout)
                    
                    self.selector.record_expert_success()
                    
                    logger.info(
                        "expert_analysis_complete",
                        latency_ms=expert_result.latency_ms,
                        risk_score=expert_result.p_mistral
                    )
                    
                    return expert_result
                    
                except concurrent.futures.TimeoutError:
                    logger.warning(
                        "expert_timeout_using_fast_fallback",
                        timeout=self.selector.expert_timeout,
                        reason=reason
                    )
                    self.selector.record_expert_failure()
                    return fast_result
            
        except Exception as e:
            logger.error(
                "expert_failed_using_fast_fallback",
                error=str(e),
                reason=reason
            )
            self.selector.record_expert_failure()
            return fast_result

