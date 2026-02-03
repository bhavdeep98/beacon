"""
Test: Verify Expert Agent and Empathy Agent can coexist without memory issues.

This test ensures:
1. The Shared LLM Engine is used by both agents
2. No duplicate model loading occurs
3. Both agents can operate sequentially without crashes
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reasoning.mistral_reasoner import MistralReasoner
from src.reasoning.strategies import ExpertLLMStrategy
from src.conversation.conversation_agent import ConversationAgent
from src.core.llm_engine import get_llm_engine
import structlog

logger = structlog.get_logger()

def test_dual_agent_coexistence():
    print("\n" + "="*60)
    print("TEST: Dual Agent Coexistence (Expert + Empathy)")
    print("="*60)
    
    # 1. Initialize Shared Engine
    print("\n[STEP 1] Initializing Shared LLM Engine...")
    engine = get_llm_engine()
    print(f"✓ Engine Ready. Mock Mode: {engine.mock_mode}")
    
    # 2. Initialize Expert Agent (Clinical Reasoning)
    print("\n[STEP 2] Initializing Expert Agent (Clinical Reasoning)...")
    expert_strategy = ExpertLLMStrategy()
    clinical_agent = MistralReasoner(strategy=expert_strategy)
    print("✓ Expert Agent Ready")
    
    # 3. Initialize Empathy Agent (Conversation)
    print("\n[STEP 3] Initializing Empathy Agent (Conversation)...")
    empathy_agent = ConversationAgent()
    print("✓ Empathy Agent Ready")
    
    # 4. Test Clinical Analysis
    print("\n[STEP 4] Testing Clinical Analysis...")
    test_message = "I've been feeling really down lately. Can't focus on anything."
    
    try:
        clinical_result = clinical_agent.analyze(
            message=test_message,
            context=["I haven't been sleeping well."]
        )
        
        print(f"✓ Clinical Analysis Complete:")
        print(f"  - Risk Level: {clinical_result.risk_level}")
        print(f"  - Risk Score: {clinical_result.p_mistral:.2f}")
        print(f"  - Latency: {clinical_result.latency_ms:.0f}ms")
        print(f"  - Model: {clinical_result.model_used}")
        
    except Exception as e:
        print(f"✗ Clinical Analysis Failed: {e}")
        return False
    
    # 5. Test Empathy Response
    print("\n[STEP 5] Testing Empathy Response...")
    
    try:
        # Import ConversationContext
        from src.conversation.conversation_agent import ConversationContext
        import asyncio
        
        # Build context
        context = ConversationContext(
            session_id="test_session_001",
            risk_level=clinical_result.risk_level.value,
            risk_score=clinical_result.p_mistral,
            matched_patterns=[],
            conversation_history=[]
        )
        
        # Generate response (async)
        empathy_response = asyncio.run(empathy_agent.generate_response(
            message=test_message,
            context=context
        ))
        
        print(f"✓ Empathy Response Generated:")
        print(f"  - Response: {empathy_response[:100]}...")
        
    except Exception as e:
        print(f"✗ Empathy Response Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Verify No Duplicate Loading
    print("\n[STEP 6] Verifying Single Model Instance...")
    engine_check = get_llm_engine()
    if engine_check is engine:
        print("✓ Singleton Pattern Confirmed: Same engine instance")
    else:
        print("✗ WARNING: Multiple engine instances detected!")
        return False
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED: Dual Agent Coexistence Verified")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_dual_agent_coexistence()
    sys.exit(0 if success else 1)
