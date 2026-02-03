"""
Backfill RAG with existing conversations from database.

This script indexes all existing conversations into the RAG system
so that prior context can be retrieved in future sessions.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_db, Conversation
from src.rag.rag_service import RAGService
import structlog

logger = structlog.get_logger()


def backfill_rag():
    """Backfill RAG with existing conversations."""
    
    logger.info("initializing_rag_service")
    rag_service = RAGService()
    
    logger.info("loading_conversations_from_database")
    db = next(get_db())
    
    conversations = db.query(Conversation).order_by(Conversation.created_at).all()
    
    logger.info(f"found_{len(conversations)}_conversations")
    
    indexed_count = 0
    failed_count = 0
    
    for conv in conversations:
        try:
            # Index conversation
            rag_service.index_conversation(
                conversation_id=str(conv.id),
                student_id_hash=conv.session_id_hash,  # Using session_id_hash as student_id_hash
                message=conv.message,
                response=conv.response,
                risk_level=conv.risk_level,
                timestamp=conv.created_at
            )
            indexed_count += 1
            
            if indexed_count % 10 == 0:
                logger.info(f"indexed_{indexed_count}_conversations")
                
        except Exception as e:
            logger.error(f"failed_to_index_conversation_{conv.id}", error=str(e))
            failed_count += 1
    
    logger.info(
        "backfill_complete",
        total=len(conversations),
        indexed=indexed_count,
        failed=failed_count
    )
    
    # Show RAG stats
    stats = rag_service.get_stats()
    logger.info("rag_stats", stats=stats)


if __name__ == "__main__":
    backfill_rag()
