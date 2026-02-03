"""
PsyFlo 'Council of Agents' Graph Implementation using LangGraph.

This module implements the PACA (PsyFlo Adaptive Consensus Algorithm) strategy
using a stateful graph architecture. It orchestrates the existing SafetyService,
MistralReasoner, and ConversationAgent as nodes in a directed workflow.
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
import structlog
from dataclasses import asdict

from src.safety.safety_analyzer import SafetyService, SafetyResult
from src.reasoning.mistral_reasoner import MistralReasoner, ReasoningResult, RiskLevel as MistralRisk
from src.conversation.conversation_agent import ConversationAgent, ConversationContext
from src.orchestrator.consensus_config import ConsensusConfig

logger = structlog.get_logger()

class AgentState(TypedDict):
    """
    The shared state of the Council execution.
    Targeting 'Explicit Over Clever' by keeping state flat and typed.
    """
    # Inputs
    session_id: str
    message: str
    conversation_history: List[Dict[str, str]]
    
    # Internal Assessments
    safety_result: Optional[SafetyResult]
    mistral_result: Optional[ReasoningResult]
    
    # Analysis Configuration
    config: ConsensusConfig
    
    # Outputs
    risk_level: str
    final_response: str
    final_score: float  # Consensus score from PACA algorithm
    is_crisis: bool
    matched_patterns: List[str]
    latency_ms: float
    
    # Debug/Trace
    trace_steps: List[str]

class CouncilGraph:
    def __init__(
        self, 
        safety_service: SafetyService,
        mistral_reasoner: MistralReasoner,
        conversation_agent: ConversationAgent
    ):
        self.safety = safety_service
        self.mistral = mistral_reasoner
        self.conversation = conversation_agent
        self.workflow = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Construct the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add Nodes
        workflow.add_node("reflex_agent", self._reflex_node)
        workflow.add_node("clinical_agent", self._clinical_node)
        workflow.add_node("empathy_agent", self._empathy_node)
        
        # Set Entry Point
        workflow.set_entry_point("reflex_agent")
        
        # Add Conditional Edges
        workflow.add_conditional_edges(
            "reflex_agent",
            self._route_after_reflex,
            {
                "green_path": "empathy_agent",
                "yellow_path": "clinical_agent",
                "red_path": "clinical_agent" # Clinical agent handles crisis prompt assembly too
            }
        )
        
        workflow.add_edge("clinical_agent", "empathy_agent")
        workflow.add_edge("empathy_agent", END)
        
        return workflow.compile()

    async def _reflex_node(self, state: AgentState) -> Dict[str, Any]:
        """Node 1: Reflex Agent (SafetyService)."""
        logger.info("node_execution", node="reflex_agent", session_id=state["session_id"])
        
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.safety.analyze, state["message"])
        
        # Determine strict crisis from regex
        is_hard_crisis = result.p_regex >= 0.90
        
        # Log safety scores for visibility
        logger.info(
            "safety_analysis_complete",
            session_id=state["session_id"],
            p_regex=result.p_regex,
            p_semantic=result.p_semantic,
            sarcasm_filtered=result.sarcasm_filtered,
            matched_patterns=result.matched_patterns,
            is_crisis=is_hard_crisis
        )
        
        return {
            "safety_result": result,
            "is_crisis": is_hard_crisis,
            "matched_patterns": result.matched_patterns,
            "trace_steps": state.get("trace_steps", []) + ["reflex_checked"]
        }

    async def _route_after_reflex(self, state: AgentState) -> str:
        """Decide the path based on Reflex result."""
        safety = state["safety_result"]
        
        # Red Path: Explicit Regex Crisis
        if state["is_crisis"]:
            logger.info(
                "routing_decision",
                path="red",
                reason="regex_crisis",
                p_regex=safety.p_regex,
                matched_patterns=safety.matched_patterns
            )
            return "red_path"
            
        # Yellow Path: Ambiguous or concerning patterns
        # Lower threshold to 0.5 for semantic to catch more nuanced concerns
        # Also trigger if any patterns matched (even if below crisis threshold)
        should_review_clinical = (
            safety.p_semantic > 0.50 or 
            safety.sarcasm_filtered or 
            len(safety.matched_patterns) > 0 or
            safety.p_regex > 0.30  # Some regex match but not crisis level
        )
        
        if should_review_clinical:
            logger.info(
                "routing_decision",
                path="yellow",
                reason="clinical_review_needed",
                p_semantic=safety.p_semantic,
                p_regex=safety.p_regex,
                sarcasm_filtered=safety.sarcasm_filtered,
                matched_patterns=safety.matched_patterns
            )
            return "yellow_path"
            
        # Green Path: Clean - no concerning signals
        logger.info(
            "routing_decision",
            path="green",
            reason="clean_checks",
            p_semantic=safety.p_semantic,
            p_regex=safety.p_regex
        )
        return "green_path"

    async def _clinical_node(self, state: AgentState) -> Dict[str, Any]:
        """Node 2: Clinical Agent (MistralReasoner)."""
        logger.info(
            "node_execution",
            node="clinical_agent",
            session_id=state["session_id"],
            model="mistral_expert"
        )
        
        # Run Mistral Analysis
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.mistral.analyze, state["message"], [m["content"] for m in state["conversation_history"][-3:]])
        
        risk_level_str = result.risk_level.value
        
        # Merge clinical markers into patterns
        new_patterns = [m.category for m in result.clinical_markers]
        all_patterns = list(set(state["matched_patterns"] + new_patterns))
        
        # Force Crisis if Mistral says so
        is_crisis = state["is_crisis"] or (result.risk_level == MistralRisk.CRISIS)
        
        logger.info(
            "clinical_analysis_complete",
            session_id=state["session_id"],
            risk_level=risk_level_str,
            p_mistral=result.p_mistral,
            clinical_markers=[m.category for m in result.clinical_markers],
            is_crisis=is_crisis
        )
        
        return {
            "mistral_result": result,
            "risk_level": risk_level_str,
            "is_crisis": is_crisis,
            "matched_patterns": all_patterns,
            "trace_steps": state["trace_steps"] + ["clinical_reviewed"]
        }

    async def _empathy_node(self, state: AgentState) -> Dict[str, Any]:
        """Node 3: Empathy Agent (ConversationAgent)."""
        logger.info("node_execution", node="empathy_agent", session_id=state["session_id"])
        
        # Calculate Consensus Score (PACA Algorithm)
        # This is the actual decision-making score, not just for visualization
        safety_result = state["safety_result"]
        mistral_result = state["mistral_result"]
        config = state["config"]
        
        regex_score = float(safety_result.p_regex) if safety_result else 0.0
        semantic_score = float(safety_result.p_semantic) if safety_result else 0.0
        mistral_score = float(mistral_result.p_mistral) if mistral_result else 0.0
        
        # History score (for now, we don't have a separate history analyzer, so use 0)
        # In future, this could analyze conversation patterns over time
        history_score = 0.0
        
        # Weighted consensus calculation (PACA)
        # NOTE: We're ignoring w_history for now since we don't have a history analyzer
        # So we need to normalize the other weights to sum to 1.0
        total_weight = config.w_regex + config.w_semantic + config.w_mistral
        
        if mistral_result:
            # All three layers available - normalize weights
            normalized_w_regex = config.w_regex / total_weight
            normalized_w_semantic = config.w_semantic / total_weight
            normalized_w_mistral = config.w_mistral / total_weight
            
            final_score = (
                regex_score * normalized_w_regex +
                semantic_score * normalized_w_semantic +
                mistral_score * normalized_w_mistral
            )
        else:
            # Mistral timed out - adjust weights for remaining layers
            adjusted_w_regex = config.w_regex / (config.w_regex + config.w_semantic)
            adjusted_w_semantic = config.w_semantic / (config.w_regex + config.w_semantic)
            final_score = (regex_score * adjusted_w_regex) + (semantic_score * adjusted_w_semantic)
        
        # Determine risk level from consensus score
        if final_score >= config.crisis_threshold:
            current_risk = "CRISIS"
            is_crisis = True
        elif final_score >= config.caution_threshold:
            current_risk = "CAUTION"
            is_crisis = False
        else:
            current_risk = "SAFE"
            is_crisis = False
        
        # Override with routing decision if it was more severe
        if state["is_crisis"]:
            current_risk = "CRISIS"
            is_crisis = True
        
        logger.info(
            "consensus_calculated",
            session_id=state["session_id"],
            final_score=float(final_score),
            regex_score=float(regex_score),
            semantic_score=float(semantic_score),
            mistral_score=float(mistral_score),
            normalized_w_regex=normalized_w_regex if mistral_result else adjusted_w_regex,
            normalized_w_semantic=normalized_w_semantic if mistral_result else adjusted_w_semantic,
            normalized_w_mistral=normalized_w_mistral if mistral_result else 0.0,
            calculation=f"({regex_score}*{normalized_w_regex if mistral_result else adjusted_w_regex:.3f}) + ({semantic_score}*{normalized_w_semantic if mistral_result else adjusted_w_semantic:.3f}) + ({mistral_score}*{normalized_w_mistral if mistral_result else 0:.3f})",
            risk_level=current_risk,
            is_crisis=is_crisis
        )
        
        # Create Context Object
        context = ConversationContext(
            session_id=state["session_id"],
            risk_level=current_risk,
            risk_score=final_score,  # Use consensus score, not just regex
            matched_patterns=state["matched_patterns"],
            conversation_history=state["conversation_history"]
        )
        
        # Generate Response
        response = await self.conversation.generate_response(
            message=state["message"],
            context=context,
            max_tokens=None
        )
        
        return {
            "final_response": response,
            "risk_level": current_risk,
            "is_crisis": is_crisis,
            "final_score": final_score,  # Add consensus score to state
            "trace_steps": state["trace_steps"] + ["response_generated"]
        }

    async def analyze_fast(self, message: str, session_id: str, history: List[Dict]) -> Dict[str, Any]:
        """
        FAST consensus analysis (regex + semantic + mistral scoring only).
        Returns scores immediately without generating response.
        
        Tenet #15: Performance Is a Safety Feature - Crisis detection <50ms
        """
        import asyncio
        import time
        
        start_time = time.time()
        
        # Step 1: Safety Analysis (regex + semantic) - FAST (<50ms)
        safety_result = await asyncio.get_event_loop().run_in_executor(
            None, self.safety.analyze, message
        )
        
        # Step 2: Mistral Analysis with SHORT timeout for scoring only (15s max)
        mistral_result = None
        try:
            # Use shorter timeout for scoring - we don't need full reasoning here
            mistral_task = asyncio.get_event_loop().run_in_executor(
                None, self.mistral.analyze, message, [m["content"] for m in history[-3:]]
            )
            mistral_result = await asyncio.wait_for(mistral_task, timeout=15.0)
        except asyncio.TimeoutError:
            logger.warning("mistral_scoring_timeout", timeout_seconds=15.0)
        
        # Step 3: Calculate Consensus Score
        config = ConsensusConfig()
        regex_score = float(safety_result.p_regex)
        semantic_score = float(safety_result.p_semantic)
        mistral_score = float(mistral_result.p_mistral) if mistral_result else 0.0
        
        logger.info(
            "calculating_consensus",
            regex_score=regex_score,
            semantic_score=semantic_score,
            mistral_score=mistral_score,
            mistral_timeout=mistral_result is None,
            w_regex=config.w_regex,
            w_semantic=config.w_semantic,
            w_mistral=config.w_mistral
        )
        
        # Normalize weights (ignoring w_history for now)
        total_weight = config.w_regex + config.w_semantic + config.w_mistral
        
        if mistral_result:
            normalized_w_regex = config.w_regex / total_weight
            normalized_w_semantic = config.w_semantic / total_weight
            normalized_w_mistral = config.w_mistral / total_weight
            
            # Calculate each contribution separately for debugging
            regex_contribution = regex_score * normalized_w_regex
            semantic_contribution = semantic_score * normalized_w_semantic
            mistral_contribution = mistral_score * normalized_w_mistral
            
            final_score = regex_contribution + semantic_contribution + mistral_contribution
            
            # Tenet #4: Fail Loud, Fail Early - Verify calculation is correct
            expected_score = (
                regex_score * normalized_w_regex +
                semantic_score * normalized_w_semantic +
                mistral_score * normalized_w_mistral
            )
            if abs(final_score - expected_score) > 0.001:
                logger.error(
                    "CONSENSUS_CALCULATION_ERROR",
                    final_score=final_score,
                    expected_score=expected_score,
                    difference=abs(final_score - expected_score)
                )
                raise ValueError(
                    f"Consensus calculation mismatch: {final_score:.4f} != {expected_score:.4f}"
                )
            
            logger.info(
                "consensus_with_mistral",
                # Input scores
                regex_score=regex_score,
                semantic_score=semantic_score,
                mistral_score=mistral_score,
                # Weights
                w_regex_original=config.w_regex,
                w_semantic_original=config.w_semantic,
                w_mistral_original=config.w_mistral,
                total_weight=total_weight,
                # Normalized weights
                normalized_w_regex=normalized_w_regex,
                normalized_w_semantic=normalized_w_semantic,
                normalized_w_mistral=normalized_w_mistral,
                weights_sum=normalized_w_regex + normalized_w_semantic + normalized_w_mistral,
                # Contributions
                regex_contribution=regex_contribution,
                semantic_contribution=semantic_contribution,
                mistral_contribution=mistral_contribution,
                # Final
                final_score=final_score,
                calculation=f"({regex_score:.3f}*{normalized_w_regex:.3f}) + ({semantic_score:.3f}*{normalized_w_semantic:.3f}) + ({mistral_score:.3f}*{normalized_w_mistral:.3f}) = {regex_contribution:.3f} + {semantic_contribution:.3f} + {mistral_contribution:.3f} = {final_score:.3f}"
            )
        else:
            # Mistral timed out - use only regex + semantic
            adjusted_w_regex = config.w_regex / (config.w_regex + config.w_semantic)
            adjusted_w_semantic = config.w_semantic / (config.w_regex + config.w_semantic)
            final_score = (regex_score * adjusted_w_regex) + (semantic_score * adjusted_w_semantic)
            
            logger.info(
                "consensus_without_mistral",
                adjusted_w_regex=adjusted_w_regex,
                adjusted_w_semantic=adjusted_w_semantic,
                calculation=f"({regex_score}*{adjusted_w_regex:.3f}) + ({semantic_score}*{adjusted_w_semantic:.3f})",
                final_score=final_score
            )
        
        # Determine risk level
        if final_score >= config.crisis_threshold or regex_score >= 0.90:
            risk_level = "CRISIS"
            is_crisis = True
        elif final_score >= config.caution_threshold:
            risk_level = "CAUTION"
            is_crisis = False
        else:
            risk_level = "SAFE"
            is_crisis = False
        
        analysis_latency = int((time.time() - start_time) * 1000)
        
        logger.info(
            "fast_consensus_complete",
            session_id=session_id,
            final_score=float(final_score),
            regex_score=float(regex_score),
            semantic_score=float(semantic_score),
            mistral_score=float(mistral_score),
            risk_level=risk_level,
            is_crisis=is_crisis,
            latency_ms=analysis_latency,
            mistral_timeout=mistral_result is None
        )
        
        return {
            "safety_result": safety_result,
            "mistral_result": mistral_result,
            "final_score": final_score,
            "risk_level": risk_level,
            "is_crisis": is_crisis,
            "matched_patterns": safety_result.matched_patterns,
            "latency_ms": analysis_latency
        }
    
    async def generate_response(self, message: str, session_id: str, history: List[Dict], analysis_result: Dict[str, Any], student_id_hash: Optional[str] = None) -> str:
        """
        Generate response AFTER consensus analysis.
        This can take 120s - it's separate from the fast scoring.
        
        Tenet #8: Engagement - "Thinking" animation builds trust during processing
        
        Args:
            message: Student message
            session_id: Session ID
            history: Conversation history
            analysis_result: Results from analyze_fast()
            student_id_hash: Hashed student ID for RAG retrieval
        """
        context = ConversationContext(
            session_id=session_id,
            risk_level=analysis_result["risk_level"],
            risk_score=analysis_result["final_score"],
            matched_patterns=analysis_result["matched_patterns"],
            conversation_history=history
        )
        
        response = await self.conversation.generate_response(
            message=message,
            context=context,
            max_tokens=None,
            student_id_hash=student_id_hash
        )
        
        return response

    async def run(self, message: str, session_id: str, history: List[Dict]) -> AgentState:
        """Run the full graph execution."""
        initial_state = {
            "session_id": session_id,
            "message": message,
            "conversation_history": history,
            "safety_result": None,
            "mistral_result": None,
            "matched_patterns": [],
            "risk_level": "SAFE",
            "final_score": 0.0,
            "is_crisis": False,
            "trace_steps": [],
            "config": ConsensusConfig()
        }
        
        # Run graph
        result_state = await self.workflow.ainvoke(initial_state)
        return result_state
