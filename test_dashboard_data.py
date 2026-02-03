"""
Quick test to verify dashboard data is properly seeded.
"""

from backend.database import SessionLocal, Student, Conversation, CrisisEvent, ConversationTheme

def test_dashboard_data():
    db = SessionLocal()
    
    print("=" * 70)
    print("DASHBOARD DATA VERIFICATION")
    print("=" * 70)
    
    # Check students
    students = db.query(Student).all()
    print(f"\n✓ Students: {len(students)}")
    for student in students:
        print(f"  - {student.name} (Grade {student.grade}): {student.total_conversations} conversations")
    
    # Check conversations
    conversations = db.query(Conversation).all()
    print(f"\n✓ Conversations: {len(conversations)}")
    crisis_convs = [c for c in conversations if c.risk_level == "CRISIS"]
    caution_convs = [c for c in conversations if c.risk_level == "CAUTION"]
    safe_convs = [c for c in conversations if c.risk_level == "SAFE"]
    print(f"  - CRISIS: {len(crisis_convs)}")
    print(f"  - CAUTION: {len(caution_convs)}")
    print(f"  - SAFE: {len(safe_convs)}")
    
    # Check crisis events
    crisis_events = db.query(CrisisEvent).all()
    print(f"\n✓ Crisis Events: {len(crisis_events)}")
    for event in crisis_events[:3]:
        conv = db.query(Conversation).filter(Conversation.id == event.conversation_id).first()
        if conv:
            print(f"  - Event {event.id}: Conv #{event.conversation_id}")
            print(f"    Message: {conv.message[:60]}...")
            print(f"    Risk: {event.risk_score:.2%}")
        else:
            print(f"  - Event {event.id}: Conv #{event.conversation_id} NOT FOUND!")
    
    # Check themes
    themes = db.query(ConversationTheme).all()
    print(f"\n✓ Themes: {len(themes)}")
    for theme in themes:
        student = db.query(Student).filter(Student.student_id_hash == theme.student_id_hash).first()
        if student:
            print(f"  - {student.name}: {theme.theme} ({theme.mention_count}x)")
    
    print("\n" + "=" * 70)
    print("DATA VERIFICATION COMPLETE")
    print("=" * 70)
    
    # Test a specific conversation
    print("\n" + "=" * 70)
    print("TESTING CONVERSATION ENDPOINT DATA")
    print("=" * 70)
    
    if crisis_events:
        test_event = crisis_events[0]
        test_conv = db.query(Conversation).filter(Conversation.id == test_event.conversation_id).first()
        
        if test_conv:
            print(f"\nConversation #{test_conv.id}:")
            print(f"  Message: {test_conv.message}")
            print(f"  Response: {test_conv.response}")
            print(f"  Risk Level: {test_conv.risk_level}")
            print(f"  Risk Score: {test_conv.risk_score:.2%}")
            print(f"  Regex Score: {test_conv.regex_score:.2%}")
            print(f"  Semantic Score: {test_conv.semantic_score:.2%}")
            print(f"  Mistral Score: {test_conv.mistral_score:.2%}" if test_conv.mistral_score else "  Mistral Score: None")
            print(f"  Reasoning: {test_conv.reasoning[:100]}...")
            print(f"  Patterns: {test_conv.matched_patterns}")
            print(f"  Latency: {test_conv.latency_ms}ms")
        else:
            print(f"\n❌ Conversation #{test_event.conversation_id} NOT FOUND!")
    
    db.close()

if __name__ == "__main__":
    test_dashboard_data()
