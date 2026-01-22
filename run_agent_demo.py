"""
Conversation Agent Demo

Test the native Llama integration with sample conversations.
Verifies model loading, generation, and "empathic pause" streaming.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from conversation import ConversationAgent, ConversationContext


async def demo_conversation():
    """Run a demo conversation to test the agent."""
    
    print("=" * 60)
    print("PsyFlo Conversation Agent Demo")
    print("=" * 60)
    print()
    
    # Initialize agent
    print("Loading conversation agent...")
    try:
        agent = ConversationAgent()
        print("✓ Agent loaded successfully")
        print()
    except Exception as e:
        print(f"✗ Failed to load agent: {e}")
        print()
        print("Make sure:")
        print("1. Model file exists at models/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf")
        print("2. Run: python tools/download_mistral_model.py")
        print("3. Or set LLAMA_MODEL_PATH in .env")
        return
    
    # Test messages
    test_cases = [
        {
            "message": "I'm feeling a bit stressed about my exams coming up.",
            "risk_level": "SAFE",
            "risk_score": 0.1,
            "matched_patterns": []
        },
        {
            "message": "I've been having trouble sleeping and I feel really anxious.",
            "risk_level": "CAUTION",
            "risk_score": 0.65,
            "matched_patterns": ["anxiety_symptoms"]
        },
        {
            "message": "I want to end my life.",
            "risk_level": "CRISIS",
            "risk_score": 0.95,
            "matched_patterns": ["suicidal_ideation", "explicit_intent"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['risk_level']}")
        print("-" * 60)
        print(f"Student: {test_case['message']}")
        print()
        
        # Create context
        context = ConversationContext(
            session_id=f"demo_session_{i}",
            risk_level=test_case["risk_level"],
            risk_score=test_case["risk_score"],
            matched_patterns=test_case["matched_patterns"],
            conversation_history=[]
        )
        
        # Generate response
        print("Connor: ", end="", flush=True)
        
        try:
            response = await agent.generate_response(
                message=test_case["message"],
                context=context
            )
            
            # Simulate "empathic pause" by printing character by character
            for char in response:
                print(char, end="", flush=True)
                await asyncio.sleep(0.02)  # 20ms per character
            
            print()
            print()
            
        except Exception as e:
            print(f"\n✗ Generation failed: {e}")
            print()
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_conversation())
