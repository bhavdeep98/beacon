"""
Database Migration: Add Student Profiles and Themes

Tenet #2: Zero PII in logs
Tenet #9: Visibility - All migrations logged and traceable
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import engine, Base, Student, ConversationTheme, ConversationSummary
import structlog

logger = structlog.get_logger()


def run_migration():
    """
    Create new tables for student profiles and conversation memory.
    
    This is a safe migration - it only creates new tables, doesn't modify existing ones.
    """
    logger.info("migration_started", tables=["students", "conversation_themes", "conversation_summaries"])
    
    try:
        # Create all tables (will skip existing ones)
        Base.metadata.create_all(bind=engine)
        
        logger.info(
            "migration_completed",
            status="success",
            message="Student profile tables created successfully"
        )
        
        print("✅ Migration completed successfully!")
        print("   - students table created")
        print("   - conversation_themes table created")
        print("   - conversation_summaries table created")
        
    except Exception as e:
        logger.error(
            "migration_failed",
            error=str(e),
            exc_info=True
        )
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    print("🔄 Running database migration: Add Student Profiles")
    print("=" * 60)
    run_migration()
    print("=" * 60)
