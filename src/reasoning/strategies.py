"""
Reasoning Strategies (Strategy Pattern)

Defines interchangeable algorithms for the MistralReasoner.
Allows dynamic switching between "Fast/Heuristic" and "Deep/Expert" analysis using the Shared LLM.

Strategy:
1. FastEmotionStrategy: Uses DistilBERT + Regex (Existing implementation).
2. ExpertLLMStrategy: Uses the shared Mistral 7B model via LLMEngine for deep clinical reasoning.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time
import json
import structlog
from src.core.llm_engine import get_llm_engine
from src.reasoning.mistral_reasoner import ReasoningResult, RiskLevel, ClinicalMarker

logger = structlog.get_logger()

@dataclass
class StrategyContext:
    message: str
    history: List[str]
    timeout: float

class ReasoningStrategy(ABC):
    """Abstract base strategy for clinical reasoning."""
    
    @abstractmethod
    def analyze(self, ctx: StrategyContext) -> ReasoningResult:
        pass
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the strategy for logging."""
        pass


class FastEmotionStrategy(ReasoningStrategy):
    """
    Current implementation using DistilBERT and Regex.
    Best for: Initial triage, high throughput, low latency.
    """
    
    def __init__(self, classifier_pipeline=None):
        self._classifier = classifier_pipeline
        self._transformers_available = False
        self._load_resources()
        
    def _load_resources(self):
        try:
            from transformers import pipeline
            import torch
            device = 0 if torch.cuda.is_available() else -1
            if not self._classifier:
                self._classifier = pipeline(
                    "text-classification",
                    model="bhadresh-savani/distilbert-base-uncased-emotion",
                    device=device,
                    top_k=None
                )
            self._transformers_available = True
        except ImportError:
            logger.warning("transformers_missing_for_fast_strategy")
        except Exception as e:
             logger.warning("fast_strategy_init_failed", error=str(e))

    @property
    def name(self) -> str:
        return "fast_emotion_distilbert"

    def analyze(self, ctx: StrategyContext) -> ReasoningResult:
        if not self._transformers_available:
            # Fallback safe result
            return ReasoningResult(
                p_mistral=0.0,
                risk_level=RiskLevel.SAFE,
                reasoning_trace="Strategy failed: Transformers not available",
                clinical_markers=[],
                is_sarcasm=False,
                sarcasm_reasoning="",
                latency_ms=0.0,
                model_used="none"
            )
            
        start = time.perf_counter()
        
        try:
            # 1. Run Emotion Classifier
            emotions = self._classifier(ctx.message)[0]
            emotion_dict = {e['label']: e['score'] for e in emotions}
            
            # 2. Heuristic Logic (Ported from original MistralReasoner)
            sadness = emotion_dict.get('sadness', 0.0)
            fear = emotion_dict.get('fear', 0.0)
            anger = emotion_dict.get('anger', 0.0)
            
            p_score = (sadness * 0.5 + fear * 0.3 + anger * 0.2)
            
            # Risk Logic
            if p_score > 0.75:
                risk = RiskLevel.CAUTION
                trace = f"High negative emotion (sad:{sadness:.2f}, fear:{fear:.2f})"
            elif p_score > 0.5:
                risk = RiskLevel.CAUTION
                trace = "Moderate negative emotion"
            else:
                risk = RiskLevel.SAFE
                trace = "Emotions within normal range"
                
            # Clinical Markers (Simplified regex for this strategy if needed)
            # For now returning empty as regex is handled by SafetyService usually
            # But we could duplicate the logic here if we wanted 'redundancy'
            markers = [] 
            
            latency = (time.perf_counter() - start) * 1000
            
            return ReasoningResult(
                p_mistral=p_score,
                risk_level=risk,
                reasoning_trace=trace,
                clinical_markers=markers,
                is_sarcasm=False,
                sarcasm_reasoning="Not checked in Fast Strategy",
                latency_ms=latency,
                model_used="distilbert-emotion"
            )
        except Exception as e:
            logger.error("fast_strategy_inference_failed", error=str(e))
            return ReasoningResult(
                p_mistral=0.0,
                risk_level=RiskLevel.SAFE,
                reasoning_trace=f"Error: {e}",
                clinical_markers=[],
                is_sarcasm=False,
                sarcasm_reasoning="",
                latency_ms=(time.perf_counter() - start) * 1000,
                model_used="error"
            )


class ExpertLLMStrategy(ReasoningStrategy):
    """
    Uses the Shared Mistral 7B Model for deep clinical reasoning.
    Best for: Ambiguous cases, confirmation, deep analysis.
    """
    
    def __init__(self):
        self.engine = get_llm_engine()
        
    @property
    def name(self) -> str:
        return "expert_mistral_7b"
        
    def analyze(self, ctx: StrategyContext) -> ReasoningResult:
        start = time.perf_counter()
        
        # 1. Construct Clinical Prompt
        prompt = self._build_prompt(ctx.message, ctx.history)
        
        # 2. Inference via Shared Engine
        try:
            output = self.engine.generate(
                prompt=prompt,
                max_tokens=256,
                temperature=0.0, # Deterministic for reasoning
                stop=["```", "Analysis:"]
            )
            response_text = output['choices'][0]['text']
            
            # 3. Parse Response
            result_data = self._parse_output(response_text)
            
            latency = (time.perf_counter() - start) * 1000
            
            return ReasoningResult(
                p_mistral=result_data['risk_score'],
                risk_level=result_data['risk_level'],
                reasoning_trace=result_data['reasoning'],
                clinical_markers=result_data['markers'],
                is_sarcasm=False, # TODO: Add sarcasm prompt logic
                sarcasm_reasoning="",
                latency_ms=latency,
                model_used="mistral-7b-instruct-v0.2"
            )
            
        except Exception as e:
            logger.error("expert_strategy_failed", error=str(e))
            # Fallback
            return ReasoningResult(
                p_mistral=0.0,
                risk_level=RiskLevel.SAFE,
                reasoning_trace=f"Expert analysis failed: {e}",
                clinical_markers=[],
                is_sarcasm=False,
                sarcasm_reasoning="",
                latency_ms=(time.perf_counter() - start) * 1000,
                model_used="error"
            )

    def _build_prompt(self, message: str, history: List[str]) -> str:
        # One-shot prompt for clinical triage
        # Fallback if history is None
        if history is None:
            history = []
            
        hist_str = "\n".join([f"- {h}" for h in history[-3:]])
        return f"""[INST] You are an expert clinical psychologist AI. Analyze the student's message for suicide risk, depression, and anxiety.
        
Recent History:
{hist_str}

Current Message: "{message}"

Task:
1. Estimate Risk Level (SAFE, CAUTION, CRISIS).
2. Assign a risk score (0.0 to 1.0).
3. Identify clinical markers (PHQ-9, GAD-7 concepts).
4. Provide brief reasoning.

Output Format (JSON):
{{
  "risk_level": "SAFE",
  "risk_score": 0.1,
  "markers": [],
  "reasoning": "Normal expression of..."
}}
[/INST]
```json
"""

    def _parse_output(self, text: str) -> Dict[str, Any]:
        # Simple parser attempt
        try:
            # Extract JSON between curly braces
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                # Map strings to Enums/Types
                risk_map = {"SAFE": RiskLevel.SAFE, "CAUTION": RiskLevel.CAUTION, "CRISIS": RiskLevel.CRISIS}
                risk_level = risk_map.get(data.get("risk_level", "SAFE").upper(), RiskLevel.SAFE)
                
                markers = []
                for m in data.get("markers", []):
                    markers.append(ClinicalMarker(category="ai_detected", item=m, confidence=1.0, evidence=""))
                
                return {
                    "risk_level": risk_level,
                    "risk_score": float(data.get("risk_score", 0.0)),
                    "reasoning": data.get("reasoning", "No reasoning provided"),
                    "markers": markers
                }
        except Exception:
            pass
            
        # Fallback if parsing fails
        return {
            "risk_level": RiskLevel.SAFE,
            "risk_score": 0.5 if "caution" in text.lower() else 0.1,
            "reasoning": "Raw output: " + text[:100],
            "markers": []
        }
