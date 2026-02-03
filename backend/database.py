"""
Database configuration and models

Tenet #2: Zero PII in logs
Tenet #7: Immutability by Default
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./beacon.db"  # Default to SQLite for prototype
)

print(f"[DATABASE] Using DATABASE_URL: {DATABASE_URL}")  # Debug

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Conversation(Base):
    """
    Conversation messages with risk assessments.
    
    Note: session_id is hashed for privacy (Tenet #2)
    """
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id_hash = Column(String(64), index=True, nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    
    # Risk assessment
    risk_level = Column(String(20), nullable=False)  # SAFE, CAUTION, CRISIS
    risk_score = Column(Float, nullable=False)
    
    # Layer scores (for explainability)
    regex_score = Column(Float, nullable=False)
    semantic_score = Column(Float, nullable=False)
    mistral_score = Column(Float, nullable=True)  # Null if timeout
    
    # Reasoning trace
    reasoning = Column(Text, nullable=False)
    matched_patterns = Column(JSON, nullable=False)
    
    # Performance metrics
    latency_ms = Column(Integer, nullable=False)
    timeout_occurred = Column(Integer, nullable=False)  # 0 or 1 (boolean)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id_hash": self.session_id_hash,
            "message": self.message,
            "response": self.response,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "regex_score": self.regex_score,
            "semantic_score": self.semantic_score,
            "mistral_score": self.mistral_score,
            "reasoning": self.reasoning,
            "matched_patterns": self.matched_patterns,
            "latency_ms": self.latency_ms,
            "timeout_occurred": bool(self.timeout_occurred),
            "created_at": self.created_at.isoformat()
        }


class Student(Base):
    """
    Student profile.
    
    Tenet #2: PII stored with encryption, hashed for lookups
    Tenet #8: Engagement - Remember student preferences and history
    """
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id_hash = Column(String(64), unique=True, index=True, nullable=False)
    
    # Profile (encrypted in production)
    name = Column(String(100), nullable=False)
    grade = Column(String(20), nullable=True)
    preferred_name = Column(String(100), nullable=True)
    
    # Preferences
    communication_style = Column(String(50), nullable=True)  # brief, detailed, casual
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_conversations = Column(Integer, default=0, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "student_id_hash": self.student_id_hash,
            "name": self.name,
            "grade": self.grade,
            "preferred_name": self.preferred_name,
            "communication_style": self.communication_style,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "total_conversations": self.total_conversations
        }


class ConversationTheme(Base):
    """
    Track ongoing themes/topics in student conversations.
    
    Tenet #8: Engagement - Remember what matters to the student
    """
    __tablename__ = "conversation_themes"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id_hash = Column(String(64), index=True, nullable=False)
    
    # Theme details
    theme = Column(String(100), nullable=False)  # e.g., "academic_stress", "family_issues"
    description = Column(Text, nullable=True)
    
    # Tracking
    first_mentioned = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_mentioned = Column(DateTime, default=datetime.utcnow, nullable=False)
    mention_count = Column(Integer, default=1, nullable=False)
    
    # Status
    is_active = Column(Integer, default=1, nullable=False)  # 0 or 1 (boolean)
    resolved = Column(Integer, default=0, nullable=False)  # 0 or 1 (boolean)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "student_id_hash": self.student_id_hash,
            "theme": self.theme,
            "description": self.description,
            "first_mentioned": self.first_mentioned.isoformat(),
            "last_mentioned": self.last_mentioned.isoformat(),
            "mention_count": self.mention_count,
            "is_active": bool(self.is_active),
            "resolved": bool(self.resolved)
        }


class ConversationSummary(Base):
    """
    Periodic summaries of conversations for long-term memory.
    
    Tenet #8: Engagement - LLM remembers past conversations
    """
    __tablename__ = "conversation_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id_hash = Column(String(64), index=True, nullable=False)
    
    # Summary content
    summary = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=False)  # List of key discussion points
    
    # Time range
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    conversation_count = Column(Integer, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "student_id_hash": self.student_id_hash,
            "summary": self.summary,
            "key_points": self.key_points,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "conversation_count": self.conversation_count,
            "created_at": self.created_at.isoformat()
        }


class CrisisEvent(Base):
    """
    Crisis events for audit trail.
    
    Tenet #2: Immutable audit trail
    """
    __tablename__ = "crisis_events"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id_hash = Column(String(64), index=True, nullable=False)
    student_id_hash = Column(String(64), index=True, nullable=True)  # Link to student
    conversation_id = Column(Integer, nullable=False)
    
    # Risk details
    risk_score = Column(Float, nullable=False)
    matched_patterns = Column(JSON, nullable=False)
    reasoning = Column(Text, nullable=False)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id_hash": self.session_id_hash,
            "student_id_hash": self.student_id_hash,
            "conversation_id": self.conversation_id,
            "risk_score": self.risk_score,
            "matched_patterns": self.matched_patterns,
            "reasoning": self.reasoning,
            "detected_at": self.detected_at.isoformat()
        }


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
