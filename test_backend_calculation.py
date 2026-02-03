"""
Test what the backend actually calculates with real data.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator.agent_graph import CouncilGraph
from src.safety.safety_analyzer import SafetyService
from src.reasoning.mistral_reasoner import MistralReasoner
from src.reasoning.strategies import ExpertLLMStrategy
from src.conversation.conversation_agent import ConversationAgent

async def test_real_calculation():
    """Test with real services."""
    
    print("=" * 80)
    print("TESTING REAL BACKEND CALCULATION")
    print("=" * 80)
    
    # Initialize services
    config_path = Path(__file__).parent / "config" / "crisis_patterns.yaml"
    safety_service = SafetyService(patterns_path=str(config_path))
    mistral_reasoner = MistralReasoner(strategy=ExpertLLMStrategy())
    conversation_agent = ConversationAgent(use_rag=False)
    
    council_graph = CouncilGraph(
        safety_service=safety_service,
        mistral_reasoner=mistral_reasoner,
        conversation_agent=conversation_agent
    )
    
    # Test message
    test_message = "I'm going to end my life tonight"
    
    print(f"\nTest Message: '{test_message}'")
    print("\n" + "-" * 80)
    print("Running analyze_fast()...")
    print("-" * 80)
    
    # Run analysis
    result = await council_graph.analyze_fast(
        message=test_message,
        session_id="test-session",
        history=[]
    )
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    safety_result = result["safety_result"]
    mistral_result = result.get("mistral_result")
    
    print(f"\nLayer Scores:")
    print(f"  Regex:    {safety_result.p_regex:.3f} ({safety_result.p_regex*100:.1f}%)")
    print(f"  Semantic: {safety_result.p_semantic:.3f} ({safety_result.p_semantic*100:.1f}%)")
    if mistral_result:
        print(f"  Mistral:  {mistral_result.p_mistral:.3f} ({mistral_result.p_mistral*100:.1f}%)")
    else:
        print(f"  Mistral:  TIMEOUT")
    
    print(f"\nConsensus Score: {result['final_score']:.4f} ({result['final_score']*100:.1f}%)")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Is Crisis: {result['is_crisis']}")
    print(f"Latency: {result['latency_ms']}ms")
    
    print("\n" + "=" * 80)
    
    # Manual calculation
    from src.orchestrator.consensus_config import ConsensusConfig
    config = ConsensusConfig()
    
    regex_score = float(safety_result.p_regex)
    semantic_score = float(safety_result.p_semantic)
    mistral_score = float(mistral_result.p_mistral) if mistral_result else 0.0
    
    total_weight = config.w_regex + config.w_semantic + config.w_mistral
    
    if mistral_result:
        normalized_w_regex = config.w_regex / total_weight
        normalized_w_semantic = config.w_semantic / total_weight
        normalized_w_mistral = config.w_mistral / total_weight
        
        manual_score = (
            regex_score * normalized_w_regex +
            semantic_score * normalized_w_semantic +
            mistral_score * normalized_w_mistral
        )
        
        print("MANUAL CALCULATION (with Mistral):")
        print(f"  ({regex_score:.3f} × {normalized_w_regex:.3f}) + ({semantic_score:.3f} × {normalized_w_semantic:.3f}) + ({mistral_score:.3f} × {normalized_w_mistral:.3f})")
        print(f"  = {manual_score:.4f} ({manual_score*100:.1f}%)")
    else:
        adjusted_w_regex = config.w_regex / (config.w_regex + config.w_semantic)
        adjusted_w_semantic = config.w_semantic / (config.w_regex + config.w_semantic)
        
        manual_score = (regex_score * adjusted_w_regex) + (semantic_score * adjusted_w_semantic)
        
        print("MANUAL CALCULATION (without Mistral):")
        print(f"  ({regex_score:.3f} × {adjusted_w_regex:.3f}) + ({semantic_score:.3f} × {adjusted_w_semantic:.3f})")
        print(f"  = {manual_score:.4f} ({manual_score*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print(f"Backend returned: {result['final_score']*100:.1f}%")
    print(f"Manual calc:      {manual_score*100:.1f}%")
    
    if abs(result['final_score'] - manual_score) < 0.01:
        print("✅ MATCH")
    else:
        print("❌ MISMATCH - BUG FOUND!")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_real_calculation())
