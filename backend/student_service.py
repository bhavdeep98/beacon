"""
Student Profile Service

Tenet #8: Engagement Before Intervention - Remember students, build trust
Tenet #2: Zero PII in logs - Always hash identifiers
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import structlog
from datetime import datetime, timedelta

from backend.database import Student, ConversationTheme, ConversationSummary, Conversation

logger = structlog.get_logger()


class StudentService:
    """Service for managing student profiles and conversation memory."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_student_context(self, student_id_hash: str) -> Dict:
        """
        Build comprehensive context for LLM about this student.
        
        Tenet #8: Make LLM feel like a friend who remembers
        
        Returns:
            Dict with student profile, themes, and recent summary
        """
        student = self.db.query(Student).filter(
            Student.student_id_hash == student_id_hash
        ).first()
        
        if not student:
            return {
                "has_profile": False,
                "is_new_student": True
            }
        
        # Get active themes
        themes = self.db.query(ConversationTheme).filter(
            ConversationTheme.student_id_hash == student_id_hash,
            ConversationTheme.is_active == 1
        ).order_by(ConversationTheme.last_mentioned.desc()).limit(5).all()
        
        # Get most recent summary
        summary = self.db.query(ConversationSummary).filter(
            ConversationSummary.student_id_hash == student_id_hash
        ).order_by(ConversationSummary.created_at.desc()).first()
        
        # Get conversation count
        conv_count = self.db.query(Conversation).filter(
            Conversation.session_id_hash == student_id_hash
        ).count()
        
        return {
            "has_profile": True,
            "is_new_student": conv_count == 0,
            "student_name": student.preferred_name or student.name,
            "grade": student.grade,
            "communication_style": student.communication_style,
            "total_conversations": student.total_conversations,
            "active_themes": [
                {
                    "theme": t.theme,
                    "description": t.description,
                    "last_mentioned": t.last_mentioned,
                    "mention_count": t.mention_count
                }
                for t in themes
            ],
            "recent_summary": summary.summary if summary else None,
            "last_active": student.last_active
        }
    
    def update_themes(
        self,
        student_id_hash: str,
        message: str,
        detected_themes: List[str]
    ) -> None:
        """
        Update conversation themes based on detected topics.
        
        Args:
            student_id_hash: Hashed student ID
            message: Student's message
            detected_themes: List of theme identifiers (e.g., "academic_stress")
        """
        for theme_name in detected_themes:
            existing = self.db.query(ConversationTheme).filter(
                ConversationTheme.student_id_hash == student_id_hash,
                ConversationTheme.theme == theme_name
            ).first()
            
            if existing:
                # Update existing theme
                existing.last_mentioned = datetime.utcnow()
                existing.mention_count += 1
                existing.is_active = 1
            else:
                # Create new theme
                new_theme = ConversationTheme(
                    student_id_hash=student_id_hash,
                    theme=theme_name,
                    description=self._generate_theme_description(theme_name),
                    first_mentioned=datetime.utcnow(),
                    last_mentioned=datetime.utcnow(),
                    mention_count=1,
                    is_active=1,
                    resolved=0
                )
                self.db.add(new_theme)
        
        self.db.commit()
        
        logger.info(
            "themes_updated",
            student_id=student_id_hash,
            themes=detected_themes
        )
    
    def create_summary(
        self,
        student_id_hash: str,
        days: int = 7
    ) -> Optional[ConversationSummary]:
        """
        Create a summary of recent conversations.
        
        Tenet #8: Long-term memory for continuity
        
        Args:
            student_id_hash: Hashed student ID
            days: Number of days to summarize
            
        Returns:
            Created summary or None if no conversations
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get conversations in date range
        conversations = self.db.query(Conversation).filter(
            Conversation.session_id_hash == student_id_hash,
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        ).order_by(Conversation.created_at.asc()).all()
        
        if not conversations:
            return None
        
        # Extract key points
        key_points = []
        high_risk_count = 0
        
        for conv in conversations:
            if conv.risk_level == "CRISIS" or conv.risk_level == "CAUTION":
                high_risk_count += 1
                key_points.append({
                    "date": conv.created_at.isoformat(),
                    "risk_level": conv.risk_level,
                    "patterns": conv.matched_patterns
                })
        
        # Generate summary text
        summary_text = self._generate_summary_text(
            conversations=conversations,
            high_risk_count=high_risk_count
        )
        
        # Create summary record
        summary = ConversationSummary(
            student_id_hash=student_id_hash,
            summary=summary_text,
            key_points=key_points,
            start_date=start_date,
            end_date=end_date,
            conversation_count=len(conversations)
        )
        
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        
        logger.info(
            "summary_created",
            student_id=student_id_hash,
            conversation_count=len(conversations),
            days=days
        )
        
        return summary
    
    def _generate_theme_description(self, theme: str) -> str:
        """Generate human-readable description for theme."""
        descriptions = {
            "academic_stress": "Stress related to schoolwork, grades, or academic performance",
            "family_issues": "Concerns about family relationships or home life",
            "peer_relationships": "Friendships, social dynamics, or peer pressure",
            "self_esteem": "Self-worth, body image, or identity concerns",
            "anxiety": "Worry, nervousness, or anxiety symptoms",
            "depression": "Low mood, sadness, or depression symptoms",
            "loneliness": "Feelings of isolation or lack of connection",
            "future_concerns": "Worries about college, career, or future plans"
        }
        return descriptions.get(theme, theme.replace("_", " ").title())
    
    def _generate_summary_text(
        self,
        conversations: List[Conversation],
        high_risk_count: int
    ) -> str:
        """Generate summary text from conversations."""
        total = len(conversations)
        
        # Extract common themes from matched patterns
        all_patterns = []
        for conv in conversations:
            if conv.matched_patterns:
                all_patterns.extend(conv.matched_patterns)
        
        # Count pattern frequency
        pattern_counts = {}
        for pattern in all_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Get top 3 patterns
        top_patterns = sorted(
            pattern_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        summary = f"Over the past week, had {total} conversation(s). "
        
        if high_risk_count > 0:
            summary += f"{high_risk_count} conversation(s) showed elevated concern. "
        
        if top_patterns:
            themes = ", ".join([p[0] for p in top_patterns])
            summary += f"Common themes: {themes}."
        
        return summary
