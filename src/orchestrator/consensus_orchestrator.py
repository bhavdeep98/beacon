"""
Consensus Orchestrator - The Brain

Coordinates parallel execution of Safety Service and MistralReasoner
to make final triage decisions using weighted consensus.

Design Patterns:
- Observer Pattern: Crisis events published to event bus
- Circuit Breaker: Graceful degradation when Mistral fails
- Result Pattern: Explicit error handling
- Immutable Data: All results are frozen dataclasses

Tenets:
- #1 Safety First: Safety floor cannot be overridden
- #3 Explicit Over Clever: Simple asyncio.gather, linear flow
- #4 Fail Loud: All errors logged and raised
- #6 Event-Driven: Crisis events published to bus
- #9 Visibility: Every step logged with context
- #10 Observable: Latency and scores instrumented
- #11 Graceful Degradation: Falls back to Safety if Mistral fails
"""

import asyncio
import time
from typing import Optional, Callable, List
import structlog

from .consensus_config import ConsensusConfig
from .consensus_result import ConsensusResult, LayerScore, RiskLevel


logger = structlog.get_logger()


class CircuitBreaker:
    """
    Circuit breaker for Mistral service.
    
    Tenet #11: Graceful Degradation Over Hard Failures
    """
    
    def __init__(self, failure_threshold: int, timeout_seconds: int):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False
    
    def record_success(self):
        """Record successful call."""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )
    
    def should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        if not self.is_open:
            return True
        
        # Check if timeout has passed
        if self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            if elapsed > self.timeout_seconds:
                logger.info("circuit_breaker_half_open", elapsed_seconds=elapsed)
                self.is_open = False
                return True
        
        return False


class CrisisEventBus:
    """
    Event bus for crisis events.
    
    Tenet #6: Event-Driven Crisis Response
    Pattern: Observer Pattern
    """
    
    def __init__(self):
        self._observers: List[Callable[[ConsensusResult], None]] = []
    
    def subscribe(self, observer: Callable[[ConsensusResult], None]) -> None:
        """Subscribe to crisis events."""
        self._observers.append(observer)
    
    def publish(self, result: ConsensusResult) -> None:
        """
        Publish crisis event to all observers.
        
        Tenet #4: Fail Loud - Log failures but continue notifying others
        """
        for observer in self._observers:
            try:
                observer(result)
            except Exception as e:
                logger.error(
                    "observer_failed",
                    observer=observer.__name__,
                    error=str(e),
                    exc_info=True
                )
                # Continue notifying other observers


class ConsensusOrchestrator:
    """
    Orchestrates parallel consensus pipeline.
    
    What does this file do?
    - Runs Safety Service and MistralReasoner in parallel
    - Combines scores using weighted formula
    - Makes final CRISIS/CAUTION/SAFE decision
    - Publishes crisis events to event bus
    
    What happens if this fails?
    - If Mistral times out: Falls back to Safety score only
    - If Safety fails: Raises exception (safety is critical)
    - If both fail: Raises exception with full context
    
    Where would I add a log statement to debug this?
    - Start of analyze(): Log message received
    - After each layer completes: Log score and latency
    - After consensus calculation: Log final score and decision
    - On timeout: Log which layer timed out
    """
    
    def __init__(
        self,
        safety_service,
        mistral_reasoner,
        config: Optional[ConsensusConfig] = None,
        event_bus: Optional[CrisisEventBus] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            safety_service: Safety service instance
            mistral_reasoner: Mistral reasoner instance
            config: Configuration (uses defaults if None)
            event_bus: Event bus for crisis events (creates new if None)
        """
        self.safety = safety_service
        self.mistral = mistral_reasoner
        self.config = config or ConsensusConfig()
        self.event_bus = event_bus or CrisisEventBus()
        
        # Circuit breaker for Mistral
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            timeout_seconds=self.config.circuit_breaker_timeout
        ) if self.config.circuit_breaker_enabled else None
        
        logger.info(
            "orchestrator_initialized",
            config=self.config.to_dict()
        )
    
    async def analyze(self, message: str, session_id: str) -> ConsensusResult:
        """
        Analyze message using parallel consensus pipeline.
        
        Tenet #3: Explicit Over Clever - Simple linear flow
        Tenet #9: Visibility - Log every step
        
        Args:
            message: Student message to analyze
            session_id: Session identifier (will be hashed for logging)
            
        Returns:
            ConsensusResult with final decision and all layer scores
            
        Raises:
            Exception: If safety service fails (critical)
        """
        start_time = time.time()
        
        logger.info(
            "consensus_analysis_started",
            session_id=self._hash_pii(session_id),
            message_length=len(message)
        )
        
        # Run layers in parallel
        regex_score, semantic_score, mistral_score = await self._run_parallel_analysis(
            message, session_id
        )
        
        # Calculate consensus score
        final_score = self._calculate_consensus_score(
            regex_score, semantic_score, mistral_score
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(final_score, regex_score)
        
        # Build reasoning trace
        reasoning = self._build_reasoning(
            regex_score, semantic_score, mistral_score, final_score, risk_level
        )
        
        # Collect all matched patterns
        matched_patterns = self._collect_patterns(
            regex_score, semantic_score, mistral_score
        )
        
        # Calculate total latency
        total_latency_ms = int((time.time() - start_time) * 1000)
        
        # Build result
        result = ConsensusResult(
            risk_level=risk_level,
            final_score=final_score,
            regex_score=regex_score,
            semantic_score=semantic_score,
            mistral_score=mistral_score,
            reasoning=reasoning,
            matched_patterns=matched_patterns,
            total_latency_ms=total_latency_ms,
            timeout_occurred=(mistral_score is None),
            weights_used=self.config.to_dict()["weights"]
        )
        
        # Log final decision
        logger.info(
            "consensus_analysis_complete",
            session_id=self._hash_pii(session_id),
            risk_level=risk_level.value,
            final_score=final_score,
            total_latency_ms=total_latency_ms,
            timeout_occurred=(mistral_score is None)
        )
        
        # Publish crisis event if needed
        if result.is_crisis():
            logger.warning(
                "crisis_detected",
                session_id=self._hash_pii(session_id),
                final_score=final_score,
                matched_patterns=matched_patterns
            )
            self.event_bus.publish(result)
        
        return result
    
    async def _run_parallel_analysis(
        self, message: str, session_id: str
    ) -> tuple[LayerScore, LayerScore, Optional[LayerScore]]:
        """
        Run all detection layers in parallel.
        
        Tenet #11: Graceful Degradation - Continue if Mistral fails
        """
        # Create tasks for parallel execution
        regex_task = self._run_regex_layer(message)
        semantic_task = self._run_semantic_layer(message)
        mistral_task = self._run_mistral_layer(message, session_id)
        
        # Wait for all tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(regex_task, semantic_task, mistral_task, return_exceptions=True),
                timeout=self.config.total_timeout
            )
            
            regex_score, semantic_score, mistral_score = results
            
            # Check for exceptions
            if isinstance(regex_score, Exception):
                logger.error("regex_layer_failed", error=str(regex_score), exc_info=True)
                raise regex_score  # Safety is critical, must raise
            
            if isinstance(semantic_score, Exception):
                logger.error("semantic_layer_failed", error=str(semantic_score), exc_info=True)
                raise semantic_score  # Safety is critical, must raise
            
            if isinstance(mistral_score, Exception):
                logger.warning("mistral_layer_failed", error=str(mistral_score))
                mistral_score = None  # Graceful degradation
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
            else:
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
            
            return regex_score, semantic_score, mistral_score
            
        except asyncio.TimeoutError:
            logger.error(
                "consensus_timeout",
                timeout_seconds=self.config.total_timeout
            )
            # Return whatever we have so far
            # This is a critical failure - should be rare
            raise
    
    async def _run_regex_layer(self, message: str) -> LayerScore:
        """Run regex detection layer."""
        start_time = time.time()
        
        result = await self.safety.analyze_regex(message)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.debug(
            "regex_layer_complete",
            score=result.confidence,
            latency_ms=latency_ms,
            patterns=result.matched_patterns
        )
        
        return LayerScore(
            layer_name="regex",
            score=result.confidence,
            latency_ms=latency_ms,
            matched_patterns=result.matched_patterns,
            evidence=result.evidence
        )
    
    async def _run_semantic_layer(self, message: str) -> LayerScore:
        """Run semantic detection layer."""
        start_time = time.time()
        
        result = await self.safety.analyze_semantic(message)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.debug(
            "semantic_layer_complete",
            score=result.confidence,
            latency_ms=latency_ms,
            patterns=result.matched_patterns
        )
        
        return LayerScore(
            layer_name="semantic",
            score=result.confidence,
            latency_ms=latency_ms,
            matched_patterns=result.matched_patterns,
            evidence=result.evidence
        )
    
    async def _run_mistral_layer(self, message: str, session_id: str) -> Optional[LayerScore]:
        """
        Run Mistral reasoning layer with circuit breaker.
        
        Tenet #11: Graceful Degradation
        """
        # Check circuit breaker
        if self.circuit_breaker and not self.circuit_breaker.should_allow_request():
            logger.warning("mistral_circuit_breaker_open")
            return None
        
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self.mistral.analyze(message),
                timeout=self.config.mistral_timeout
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            logger.debug(
                "mistral_layer_complete",
                score=result.confidence,
                latency_ms=latency_ms,
                patterns=result.matched_patterns
            )
            
            return LayerScore(
                layer_name="mistral",
                score=result.confidence,
                latency_ms=latency_ms,
                matched_patterns=result.matched_patterns,
                evidence=result.reasoning
            )
            
        except asyncio.TimeoutError:
            logger.warning(
                "mistral_timeout",
                timeout_seconds=self.config.mistral_timeout
            )
            if self.circuit_breaker:
                self.circuit_breaker.record_failure()
            return None
    
    def _calculate_consensus_score(
        self,
        regex_score: LayerScore,
        semantic_score: LayerScore,
        mistral_score: Optional[LayerScore]
    ) -> float:
        """
        Calculate weighted consensus score.
        
        Formula: S_c = (w_reg × P_reg) + (w_sem × P_sem) + (w_mistral × P_mistral) + (w_hist × P_hist)
        
        Note: History weight currently unused (will be added in future milestone)
        """
        # If Mistral timed out, redistribute its weight to regex (safety floor)
        if mistral_score is None:
            # Redistribute Mistral's weight to regex (safety floor)
            adjusted_w_regex = self.config.w_regex + self.config.w_mistral
            adjusted_w_semantic = self.config.w_semantic
            
            score = (
                (adjusted_w_regex * regex_score.score) +
                (adjusted_w_semantic * semantic_score.score)
            )
            
            logger.info(
                "consensus_calculated_without_mistral",
                adjusted_w_regex=adjusted_w_regex,
                adjusted_w_semantic=adjusted_w_semantic,
                final_score=score
            )
        else:
            score = (
                (self.config.w_regex * regex_score.score) +
                (self.config.w_semantic * semantic_score.score) +
                (self.config.w_mistral * mistral_score.score)
                # w_history will be added later
            )
            
            logger.info(
                "consensus_calculated",
                regex_contribution=self.config.w_regex * regex_score.score,
                semantic_contribution=self.config.w_semantic * semantic_score.score,
                mistral_contribution=self.config.w_mistral * mistral_score.score,
                final_score=score
            )
        
        return round(score, 4)
    
    def _determine_risk_level(self, final_score: float, regex_score: LayerScore) -> RiskLevel:
        """
        Determine risk level from consensus score.
        
        Tenet #1: Safety First - Regex layer can override if it detects crisis
        """
        # Safety floor: If regex detected crisis with high confidence, that's final
        if regex_score.score >= 0.95:
            logger.info(
                "safety_floor_triggered",
                regex_score=regex_score.score,
                final_score=final_score
            )
            return RiskLevel.CRISIS
        
        # Otherwise use consensus score
        if final_score >= self.config.crisis_threshold:
            return RiskLevel.CRISIS
        elif final_score >= self.config.caution_threshold:
            return RiskLevel.CAUTION
        else:
            return RiskLevel.SAFE
    
    def _build_reasoning(
        self,
        regex_score: LayerScore,
        semantic_score: LayerScore,
        mistral_score: Optional[LayerScore],
        final_score: float,
        risk_level: RiskLevel
    ) -> str:
        """
        Build human-readable reasoning trace.
        
        Tenet #9: Visibility and Explainability at Every Layer
        """
        lines = [
            f"Risk Level: {risk_level.value}",
            f"Final Score: {final_score:.4f}",
            "",
            "Layer Scores:",
            f"  Regex: {regex_score.score:.4f} (weight: {self.config.w_regex})",
            f"  Semantic: {semantic_score.score:.4f} (weight: {self.config.w_semantic})",
        ]
        
        if mistral_score:
            lines.append(f"  Mistral: {mistral_score.score:.4f} (weight: {self.config.w_mistral})")
        else:
            lines.append(f"  Mistral: TIMEOUT (weight redistributed to regex)")
        
        lines.append("")
        lines.append("Evidence:")
        
        if regex_score.matched_patterns:
            lines.append(f"  Regex matched: {', '.join(regex_score.matched_patterns)}")
        
        if semantic_score.matched_patterns:
            lines.append(f"  Semantic matched: {', '.join(semantic_score.matched_patterns)}")
        
        if mistral_score and mistral_score.matched_patterns:
            lines.append(f"  Mistral detected: {', '.join(mistral_score.matched_patterns)}")
        
        return "\n".join(lines)
    
    def _collect_patterns(
        self,
        regex_score: LayerScore,
        semantic_score: LayerScore,
        mistral_score: Optional[LayerScore]
    ) -> List[str]:
        """Collect all matched patterns from all layers."""
        patterns = []
        patterns.extend(regex_score.matched_patterns)
        patterns.extend(semantic_score.matched_patterns)
        if mistral_score:
            patterns.extend(mistral_score.matched_patterns)
        return list(set(patterns))  # Remove duplicates
    
    def _hash_pii(self, pii: str) -> str:
        """
        Hash PII for logging.
        
        Tenet #2: Zero PII in application logs
        """
        import hashlib
        return hashlib.sha256(pii.encode()).hexdigest()[:16]
