
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reasoning.mistral_reasoner import MistralReasoner
from src.reasoning.strategies import ExpertLLMStrategy, FastEmotionStrategy
from src.core.llm_engine import get_llm_engine
import structlog

logger = structlog.get_logger()

def test_expert_strategy():
    print("\n[TEST] Initializing ExpertLLMStrategy...")
    
    # 1. Initialize Engine (should mock if no model found)
    engine = get_llm_engine()
    print(f"[INFO] Engine Initialized. Mock Mode: {engine.mock_mode}")
    
    if engine.mock_mode:
        print("[WARN] Running in Mock Mode - Real inference will be simulated.")
    
    # 2. Check Strategies
    expert_strategy = ExpertLLMStrategy()
    fast_strategy = FastEmotionStrategy()
    
    # 3. Initialize Reasoner with Expert Strategy
    reasoner = MistralReasoner(strategy=expert_strategy)
    
    # 4. Test Analysis
    message = "I feel like everything is crashing down on me. I can't sleep and I'm scared about the exams."
    history = ["I've been skipping meals.", "My parents are fighting a lot."]
    
    print(f"\n[TEST] Analyzing Message: '{message}'")
    
    try:
        result = reasoner.analyze(message, context=history)
        
        print("\n[RESULT] Analysis Complete:")
        print(f"Risk Level: {result.risk_level}")
        print(f"Score: {result.p_mistral}")
        print(f"Reasoning: {result.reasoning_trace}")
        print(f"Markers: {result.clinical_markers}")
        print(f"Model Used: {result.model_used}")
        print(f"Latency: {result.latency_ms:.2f}ms")
        
    except Exception as e:
        print(f"[ERROR] Analysis Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_expert_strategy()
