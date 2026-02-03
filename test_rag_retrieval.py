"""
Test RAG retrieval to verify it's working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag.rag_service import RAGService
import structlog

logger = structlog.get_logger()


def test_rag_retrieval():
    """Test RAG retrieval with sample data."""
    
    logger.info("initializing_rag_service")
    rag_service = RAGService()
    
    # Index some test conversations
    logger.info("indexing_test_conversations")
    
    student_id = "test_student_jordan"
    
    # Conversation 1: About math exam
    rag_service.index_conversation(
        conversation_id="test_1",
        student_id_hash=student_id,
        message="I have a big math exam tomorrow and I'm really nervous",
        response="That sounds stressful. How are you feeling about the material?",
        risk_level="SAFE"
    )
    
    # Conversation 2: About exam results
    rag_service.index_conversation(
        conversation_id="test_2",
        student_id_hash=student_id,
        message="I got a B on the math exam but I'm disappointed",
        response="A B is a good grade! What were you hoping for?",
        risk_level="SAFE"
    )
    
    # Conversation 3: About parents
    rag_service.index_conversation(
        conversation_id="test_3",
        student_id_hash=student_id,
        message="My parents are upset about the B",
        response="That's tough. How did they react?",
        risk_level="CAUTION"
    )
    
    logger.info("test_conversations_indexed")
    
    # Test retrieval
    logger.info("testing_retrieval")
    
    # Query 1: Generic greeting (should retrieve recent conversations)
    context1 = rag_service.build_context(
        current_message="Hi",
        student_id_hash=student_id,
        include_conversations=True,
        include_resources=False
    )
    
    print("\n" + "="*80)
    print("Query: 'Hi'")
    print("="*80)
    print(f"Retrieved {context1['retrieval_stats']['conversations']['count']} conversations")
    print("\nContext:")
    print(context1['past_conversations'])
    
    # Query 2: About exams (should retrieve exam-related conversations)
    context2 = rag_service.build_context(
        current_message="How did my exam go?",
        student_id_hash=student_id,
        include_conversations=True,
        include_resources=False
    )
    
    print("\n" + "="*80)
    print("Query: 'How did my exam go?'")
    print("="*80)
    print(f"Retrieved {context2['retrieval_stats']['conversations']['count']} conversations")
    print("\nContext:")
    print(context2['past_conversations'])
    
    # Query 3: About parents (should retrieve parent-related conversations)
    context3 = rag_service.build_context(
        current_message="My parents are still mad",
        student_id_hash=student_id,
        include_conversations=True,
        include_resources=False
    )
    
    print("\n" + "="*80)
    print("Query: 'My parents are still mad'")
    print("="*80)
    print(f"Retrieved {context3['retrieval_stats']['conversations']['count']} conversations")
    print("\nContext:")
    print(context3['past_conversations'])
    
    # Show stats
    stats = rag_service.get_stats()
    print("\n" + "="*80)
    print("RAG Stats:")
    print("="*80)
    print(f"Total conversations indexed: {stats['conversation_store']['total_documents']}")
    print(f"Total resources indexed: {stats['resource_store']['total_documents']}")
    
    logger.info("test_complete")


if __name__ == "__main__":
    test_rag_retrieval()
