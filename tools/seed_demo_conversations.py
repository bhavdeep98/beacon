"""
Seed realistic conversation examples for Counselor Dashboard demo.

This creates diverse conversation scenarios showing:
- Crisis situations with full diagnostic traces
- Caution-level concerns
- Safe conversations
- Various matched patterns and reasoning
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal, Conversation, CrisisEvent, Student, ConversationTheme
from datetime import datetime, timedelta
import hashlib
import json

def hash_pii(value: str) -> str:
    """Hash PII for privacy."""
    return hashlib.sha256(f"demo_salt:{value}".encode()).hexdigest()[:16]


def seed_conversations():
    """Seed realistic conversation examples."""
    db = SessionLocal()
    
    try:
        # Get existing students
        students = db.query(Student).all()
        if not students:
            print("No students found. Run seed_demo_students.py first.")
            return
        
        print(f"Found {len(students)} students. Creating conversations...")
        
        # Conversation examples with full diagnostic data
        conversations = [
            # CRISIS: Explicit suicidal ideation
            {
                "student": students[0],
                "message": "I can't do this anymore. I've been thinking about ending it all. I have a plan and I'm ready to go through with it tonight.",
                "response": "I hear that you're in a lot of pain right now, and I'm really concerned about what you've shared. Your safety is the most important thing. I need you to know that you don't have to face this alone. Can we talk about getting you immediate support? There are people who care about you and want to help.",
                "risk_level": "CRISIS",
                "risk_score": 0.98,
                "regex_score": 0.95,
                "semantic_score": 0.92,
                "mistral_score": 0.97,
                "reasoning": "CRISIS DETECTED: Message contains explicit suicidal ideation with intent and plan. Regex layer matched 'ending it all' (suicidal_ideation) and 'have a plan' (intent_with_plan). Semantic layer shows 94% similarity to crisis training examples. Mistral analysis confirms active suicidal thoughts with specific plan and timeline ('tonight'). Immediate intervention required.",
                "matched_patterns": ["suicidal_ideation", "intent_with_plan", "timeline_specified", "explicit_crisis"],
                "latency_ms": 45,
                "timeout_occurred": False,
                "is_crisis": True
            },
            
            # CRISIS: Self-harm with depression indicators
            {
                "student": students[1],
                "message": "I've been cutting myself again. It's the only thing that makes me feel better. Nobody understands how much I'm hurting inside.",
                "response": "Thank you for trusting me with this. I can hear how much pain you're in, and I want you to know that what you're feeling is valid. Self-harm might feel like relief in the moment, but there are healthier ways to cope with these intense feelings. I'm here to help you find them. Can we talk about what's been going on?",
                "risk_level": "CRISIS",
                "risk_score": 0.89,
                "regex_score": 0.92,
                "semantic_score": 0.85,
                "mistral_score": 0.88,
                "reasoning": "CRISIS DETECTED: Active self-harm behavior disclosed. Regex layer matched 'cutting myself' (self_harm_active) and 'hurting inside' (emotional_pain). Semantic analysis shows strong correlation with self-injury patterns. Mistral identifies ongoing behavior ('again') and isolation ('nobody understands'). Requires immediate counselor notification.",
                "matched_patterns": ["self_harm_active", "emotional_pain", "isolation", "coping_mechanism"],
                "latency_ms": 42,
                "timeout_occurred": False,
                "is_crisis": True
            },
            
            # CAUTION: Depression symptoms without immediate crisis
            {
                "student": students[2],
                "message": "I just feel empty all the time. I can't remember the last time I was actually happy. Nothing seems worth it anymore.",
                "response": "It sounds like you've been carrying a heavy weight for a while now. Feeling empty and losing interest in things that used to matter can be really difficult. These feelings are important, and I'm glad you're talking about them. Have you noticed when these feelings started, or if anything specific triggered them?",
                "risk_level": "CAUTION",
                "risk_score": 0.72,
                "regex_score": 0.68,
                "semantic_score": 0.75,
                "mistral_score": 0.73,
                "reasoning": "CAUTION LEVEL: Indicators of depression (anhedonia, emptiness, hopelessness) without immediate crisis markers. Regex matched 'feel empty' and 'nothing seems worth it' (hopelessness). Semantic layer shows 75% similarity to depression patterns. Mistral notes persistent symptoms ('all the time') and loss of meaning. Warrants counselor follow-up within 48 hours.",
                "matched_patterns": ["depression_symptoms", "anhedonia", "hopelessness", "persistent_low_mood"],
                "latency_ms": 38,
                "timeout_occurred": False,
                "is_crisis": False
            },
            
            # CAUTION: Academic stress with anxiety
            {
                "student": students[0],
                "message": "I'm so stressed about finals. I can't sleep, I can't eat, and I keep having panic attacks. What if I fail everything?",
                "response": "Finals can definitely feel overwhelming, and it sounds like the stress is really affecting you physically. Panic attacks and changes in sleep and appetite are your body's way of saying it needs support. Let's talk about some strategies to manage this stress and break things down into smaller, more manageable pieces.",
                "risk_level": "CAUTION",
                "risk_score": 0.65,
                "regex_score": 0.58,
                "semantic_score": 0.70,
                "mistral_score": 0.67,
                "reasoning": "CAUTION LEVEL: Acute stress response with anxiety symptoms. Regex matched 'panic attacks' (anxiety_symptoms) and 'can't sleep' (sleep_disturbance). Semantic analysis shows academic stress pattern. Mistral identifies catastrophizing ('fail everything') and physical symptoms. No immediate crisis but requires monitoring and coping strategies.",
                "matched_patterns": ["anxiety_symptoms", "academic_stress", "sleep_disturbance", "catastrophizing"],
                "latency_ms": 35,
                "timeout_occurred": False,
                "is_crisis": False
            },
            
            # SAFE: Normal teenage stress (filtered hyperbole)
            {
                "student": students[1],
                "message": "Ugh, this homework is killing me! I'm literally dying from boredom. Can we talk about something else?",
                "response": "Haha, I hear you - homework can definitely feel like a drag sometimes! What would you rather talk about? Anything on your mind lately?",
                "risk_level": "SAFE",
                "risk_score": 0.15,
                "regex_score": 0.45,
                "semantic_score": 0.12,
                "mistral_score": 0.08,
                "reasoning": "SAFE: Teenage hyperbole detected and filtered. Regex initially flagged 'killing me' and 'dying' but sarcasm filter activated. Semantic layer shows low similarity (12%) to genuine crisis patterns. Mistral confirms casual tone and context ('homework', 'boredom'). No intervention needed.",
                "matched_patterns": ["hyperbole_filtered", "casual_conversation", "topic_change_request"],
                "latency_ms": 28,
                "timeout_occurred": False,
                "is_crisis": False
            },
            
            # SAFE: Positive check-in
            {
                "student": students[2],
                "message": "Hey Connor! I actually had a pretty good day today. Made a new friend in art class and got an A on my history test!",
                "response": "That's awesome! It sounds like things are going well. Making new friends and doing well academically - those are both great things to celebrate. What did you like about your new friend?",
                "risk_level": "SAFE",
                "risk_score": 0.05,
                "regex_score": 0.02,
                "semantic_score": 0.05,
                "mistral_score": 0.03,
                "reasoning": "SAFE: Positive emotional state with social and academic success indicators. No crisis patterns detected. Regex shows no concerning keywords. Semantic analysis confirms positive sentiment. Mistral identifies healthy social engagement and achievement. Continue building rapport.",
                "matched_patterns": ["positive_mood", "social_connection", "academic_success"],
                "latency_ms": 25,
                "timeout_occurred": False,
                "is_crisis": False
            },
            
            # CAUTION: Family conflict
            {
                "student": students[0],
                "message": "My parents are fighting again. They're talking about divorce and I don't know what to do. I feel like it's my fault somehow.",
                "response": "I'm sorry you're going through this. Family conflict, especially when parents are considering divorce, can be really hard on everyone. I want you to know that this is not your fault - adult relationships are complex and their decisions are not because of you. How are you coping with all of this?",
                "risk_level": "CAUTION",
                "risk_score": 0.58,
                "regex_score": 0.52,
                "semantic_score": 0.62,
                "mistral_score": 0.60,
                "reasoning": "CAUTION LEVEL: Family stressor with self-blame. Regex matched 'my fault' (self_blame) and 'don't know what to do' (helplessness). Semantic layer shows family conflict pattern. Mistral identifies parental divorce stressor and inappropriate guilt. Monitor for escalation, provide support resources.",
                "matched_patterns": ["family_conflict", "self_blame", "helplessness", "parental_divorce"],
                "latency_ms": 33,
                "timeout_occurred": False,
                "is_crisis": False
            },
            
            # CRISIS: Substance abuse with suicidal thoughts
            {
                "student": students[1],
                "message": "I've been drinking a lot lately to forget everything. Sometimes I think about just not waking up. Would anyone even care?",
                "response": "I'm really concerned about what you're sharing with me. Using alcohol to cope and having thoughts about not waking up are serious warning signs that you need support right now. People absolutely would care - I care, and I want to make sure you're safe. Can we talk about getting you help today?",
                "risk_level": "CRISIS",
                "risk_score": 0.94,
                "regex_score": 0.88,
                "semantic_score": 0.91,
                "mistral_score": 0.95,
                "reasoning": "CRISIS DETECTED: Substance abuse as coping mechanism combined with passive suicidal ideation. Regex matched 'not waking up' (suicidal_ideation_passive) and 'drinking a lot' (substance_abuse). Semantic analysis shows 91% crisis similarity. Mistral identifies maladaptive coping, suicidal thoughts, and perceived lack of support ('would anyone care'). Immediate intervention required.",
                "matched_patterns": ["suicidal_ideation_passive", "substance_abuse", "maladaptive_coping", "perceived_isolation"],
                "latency_ms": 47,
                "timeout_occurred": False,
                "is_crisis": True
            },
            
            # CAUTION: Social isolation and loneliness
            {
                "student": students[2],
                "message": "I don't really have any friends. Everyone seems to have their groups and I'm just... alone. I eat lunch by myself every day.",
                "response": "Feeling left out and lonely can be really painful, especially when you see others connecting. I want you to know that you're not alone in feeling this way - many students struggle with finding their place. Let's talk about some ways we might help you connect with others who share your interests.",
                "risk_level": "CAUTION",
                "risk_score": 0.62,
                "regex_score": 0.55,
                "semantic_score": 0.68,
                "mistral_score": 0.64,
                "reasoning": "CAUTION LEVEL: Social isolation and loneliness without immediate crisis. Regex matched 'don't have any friends' (social_isolation) and 'alone' (loneliness). Semantic layer shows isolation pattern. Mistral identifies chronic social difficulty ('every day') and exclusion feelings. Risk factor for depression - requires counselor outreach and social support planning.",
                "matched_patterns": ["social_isolation", "loneliness", "peer_rejection", "low_social_support"],
                "latency_ms": 31,
                "timeout_occurred": False,
                "is_crisis": False
            },
            
            # SAFE: Hobby discussion
            {
                "student": students[0],
                "message": "I've been getting really into photography lately. Took some cool shots at the park this weekend. Do you think I could make a career out of it?",
                "response": "That's great that you've found something you're passionate about! Photography can definitely be a career path. There are many directions you could take - photojournalism, portrait photography, commercial work, and more. What kind of photography interests you most?",
                "risk_level": "SAFE",
                "risk_score": 0.03,
                "regex_score": 0.01,
                "semantic_score": 0.04,
                "mistral_score": 0.02,
                "reasoning": "SAFE: Positive engagement with hobby and future planning. No concerning patterns detected. Regex shows no crisis keywords. Semantic analysis confirms healthy interest exploration. Mistral identifies positive future orientation and skill development. Excellent rapport-building opportunity.",
                "matched_patterns": ["hobby_interest", "future_planning", "positive_engagement"],
                "latency_ms": 22,
                "timeout_occurred": False,
                "is_crisis": False
            },
        ]
        
        # Create conversations with timestamps spread over the last week
        base_time = datetime.utcnow() - timedelta(days=7)
        
        for i, conv_data in enumerate(conversations):
            # Create timestamp (spread conversations over time)
            created_at = base_time + timedelta(hours=i * 12)
            
            # Use student's hash as session_id_hash so we can query by student
            session_id_hash = conv_data['student'].student_id_hash
            
            conversation = Conversation(
                session_id_hash=session_id_hash,
                message=conv_data["message"],
                response=conv_data["response"],
                risk_level=conv_data["risk_level"],
                risk_score=conv_data["risk_score"],
                regex_score=conv_data["regex_score"],
                semantic_score=conv_data["semantic_score"],
                mistral_score=conv_data["mistral_score"],
                reasoning=conv_data["reasoning"],
                matched_patterns=json.dumps(conv_data["matched_patterns"]),
                latency_ms=conv_data["latency_ms"],
                timeout_occurred=1 if conv_data["timeout_occurred"] else 0,
                created_at=created_at
            )
            
            db.add(conversation)
            db.flush()  # Get the conversation ID
            
            # Create crisis event if this was a crisis
            if conv_data["is_crisis"]:
                crisis_event = CrisisEvent(
                    session_id_hash=session_id_hash,
                    student_id_hash=conv_data["student"].student_id_hash,
                    conversation_id=conversation.id,
                    risk_score=conv_data["risk_score"],
                    matched_patterns=json.dumps(conv_data["matched_patterns"]),
                    reasoning=conv_data["reasoning"],
                    detected_at=created_at
                )
                db.add(crisis_event)
            
            # Update student's last active and conversation count
            conv_data["student"].last_active = created_at
            conv_data["student"].total_conversations += 1
            
            print(f"✓ Created {conv_data['risk_level']} conversation for {conv_data['student'].name}")
        
        # Add some conversation themes
        themes = [
            {
                "student": students[0],
                "theme": "academic_stress",
                "description": "Ongoing concerns about academic performance and test anxiety",
                "mention_count": 3,
                "first_mentioned": base_time,
                "last_mentioned": base_time + timedelta(days=3)
            },
            {
                "student": students[0],
                "theme": "family_issues",
                "description": "Parents considering divorce, feeling caught in the middle",
                "mention_count": 2,
                "first_mentioned": base_time + timedelta(days=4),
                "last_mentioned": base_time + timedelta(days=5)
            },
            {
                "student": students[1],
                "theme": "self_harm",
                "description": "Active self-harm behavior as coping mechanism",
                "mention_count": 2,
                "first_mentioned": base_time + timedelta(days=1),
                "last_mentioned": base_time + timedelta(days=6)
            },
            {
                "student": students[1],
                "theme": "substance_use",
                "description": "Using alcohol to cope with emotional pain",
                "mention_count": 1,
                "first_mentioned": base_time + timedelta(days=6),
                "last_mentioned": base_time + timedelta(days=6)
            },
            {
                "student": students[2],
                "theme": "social_isolation",
                "description": "Difficulty making friends, eating lunch alone",
                "mention_count": 2,
                "first_mentioned": base_time + timedelta(days=2),
                "last_mentioned": base_time + timedelta(days=5)
            },
            {
                "student": students[2],
                "theme": "depression",
                "description": "Persistent feelings of emptiness and anhedonia",
                "mention_count": 1,
                "first_mentioned": base_time + timedelta(days=2),
                "last_mentioned": base_time + timedelta(days=2)
            },
        ]
        
        for theme_data in themes:
            theme = ConversationTheme(
                student_id_hash=theme_data["student"].student_id_hash,
                theme=theme_data["theme"],
                description=theme_data["description"],
                mention_count=theme_data["mention_count"],
                first_mentioned=theme_data["first_mentioned"],
                last_mentioned=theme_data["last_mentioned"],
                is_active=1,
                resolved=0
            )
            db.add(theme)
            print(f"✓ Added theme '{theme_data['theme']}' for {theme_data['student'].name}")
        
        db.commit()
        print(f"\n✅ Successfully seeded {len(conversations)} conversations and {len(themes)} themes!")
        print("\nConversation breakdown:")
        print(f"  - CRISIS: {sum(1 for c in conversations if c['is_crisis'])} conversations")
        print(f"  - CAUTION: {sum(1 for c in conversations if c['risk_level'] == 'CAUTION')} conversations")
        print(f"  - SAFE: {sum(1 for c in conversations if c['risk_level'] == 'SAFE')} conversations")
        
    except Exception as e:
        print(f"❌ Error seeding conversations: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding demo conversations...")
    seed_conversations()
