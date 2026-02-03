"""
Test RAG System

Quick test to verify RAG components work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.rag_service import RAGService
from datetime import datetime
import structlog

logger = structlog.get_logger()


def test_rag_system():
    """Test complete RAG system."""
    print("=" * 60)
    print("Testing RAG System")
    print("=" * 60)
    
    # Initialize RAG service
    print("\n1. Initializing RAG service...")
    rag_service = RAGService()
    print("   ✅ RAG service initialized")
    
    # Check stats
    stats = rag_service.get_stats()
    print(f"   - Conversation docs: {stats['conversation_store']['total_documents']}")
    print(f"   - Resource docs: {stats['resource_store']['total_documents']}")
    
    # Test 1: Index conversations
    print("\n2. Indexing test conversations...")
    test_conversations = [
        {
            "id": "conv_1",
            "student": "student_123",
            "message": "I'm really stressed about my finals",
            "response": "That sounds really tough. What specifically is worrying you most about finals?",
            "risk": "CAUTION"
        },
        {
            "id": "conv_2",
            "student": "student_123",
            "message": "I can't sleep and keep worrying",
            "response": "Difficulty sleeping when you're anxious is really common. Have you tried any relaxation techniques?",
            "risk": "CAUTION"
        },
        {
            "id": "conv_3",
            "student": "student_123",
            "message": "I tried deep breathing but it didn't help",
            "response": "It's okay that deep breathing didn't work for you. Different techniques work for different people.",
            "risk": "SAFE"
        }
    ]
    
    for conv in test_conversations:
        rag_service.index_conversation(
            conversation_id=conv["id"],
            student_id_hash=conv["student"],
            message=conv["message"],
            response=conv["response"],
            risk_level=conv["risk"]
        )
    
    print(f"   ✅ Indexed {len(test_conversations)} conversations")
    
    # Test 2: Retrieve relevant conversations
    print("\n3. Testing conversation retrieval...")
    query = "I'm still worried about school and can't relax"
    result = rag_service.conversation_retriever.retrieve_relevant_conversations(
        query=query,
        student_id_hash="student_123",
        top_k=2
    )
    
    print(f"   Query: '{query}'")
    print(f"   Retrieved {len(result.documents)} conversations:")
    for i, (doc, score) in enumerate(zip(result.documents, result.scores), 1):
        print(f"   {i}. [Score: {score:.2f}] {doc.content[:80]}...")
    
    # Test 3: Retrieve resources
    print("\n4. Testing resource retrieval...")
    query = "I feel anxious and can't calm down"
    result = rag_service.resource_retriever.retrieve_relevant_resources(
        query=query,
        top_k=2
    )
    
    print(f"   Query: '{query}'")
    print(f"   Retrieved {len(result.documents)} resources:")
    for i, (doc, score) in enumerate(zip(result.documents, result.scores), 1):
        title = doc.metadata.get("title", "Unknown")
        category = doc.metadata.get("category", "Unknown")
        print(f"   {i}. [Score: {score:.2f}] {title} ({category})")
    
    # Test 4: Build complete context
    print("\n5. Testing context building...")
    query = "I'm still feeling anxious about finals"
    context = rag_service.build_context(
        current_message=query,
        student_id_hash="student_123",
        include_conversations=True,
        include_resources=True
    )
    
    print(f"   Query: '{query}'")
    print(f"   Context stats:")
    print(f"   - Past conversations: {context['retrieval_stats']['conversations']['count']}")
    print(f"   - Resources: {context['retrieval_stats']['resources']['count']}")
    print(f"   - Retrieval time: {context['retrieval_stats']['conversations']['retrieval_time_ms']:.1f}ms")
    
    # Test 5: Format context for LLM
    print("\n6. Testing context formatting...")
    context_str = rag_service.format_context_for_llm(context)
    print(f"   Context length: {len(context_str)} characters")
    print(f"   Preview:")
    print("   " + "-" * 56)
    for line in context_str.split('\n')[:10]:
        print(f"   {line}")
    if len(context_str.split('\n')) > 10:
        print("   ...")
    print("   " + "-" * 56)
    
    # Test 6: Crisis resources
    print("\n7. Testing crisis resource retrieval...")
    crisis_resources = rag_service.get_crisis_resources()
    print(f"   Retrieved crisis resources:")
    print("   " + "-" * 56)
    for line in crisis_resources.split('\n')[:8]:
        print(f"   {line}")
    print("   " + "-" * 56)
    
    # Test 7: Coping strategies
    print("\n8. Testing coping strategy retrieval...")
    coping = rag_service.get_coping_strategies("I feel anxious and overwhelmed")
    print(f"   Retrieved coping strategies:")
    print("   " + "-" * 56)
    for line in coping.split('\n')[:8]:
        print(f"   {line}")
    print("   " + "-" * 56)
    
    # Final stats
    print("\n9. Final statistics...")
    final_stats = rag_service.get_stats()
    print(f"   Conversation store: {final_stats['conversation_store']['total_documents']} docs")
    print(f"   Resource store: {final_stats['resource_store']['total_documents']} docs")
    print(f"   Embedding cache hit rate: {final_stats['embedding_cache']['hit_rate']:.2%}")
    
    print("\n" + "=" * 60)
    print("✅ All RAG tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_rag_system()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
