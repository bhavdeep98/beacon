"""
Clear existing conversation data and reseed with correct session hashes.
"""

from backend.database import SessionLocal, Conversation, CrisisEvent, ConversationTheme

def clear_conversations():
    """Clear all conversations, crisis events, and themes."""
    db = SessionLocal()
    
    try:
        # Delete in correct order (foreign keys)
        crisis_count = db.query(CrisisEvent).delete()
        conv_count = db.query(Conversation).delete()
        theme_count = db.query(ConversationTheme).delete()
        
        db.commit()
        
        print(f"✓ Deleted {crisis_count} crisis events")
        print(f"✓ Deleted {conv_count} conversations")
        print(f"✓ Deleted {theme_count} themes")
        print("\n✅ Database cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🗑️  Clearing conversation data...")
    clear_conversations()
    print("\n📝 Now run: python tools\\seed_demo_conversations.py")
