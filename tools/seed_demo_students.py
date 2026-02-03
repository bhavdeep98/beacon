"""
Seed Demo Students with Realistic Conversation Histories

Creates 3 students with different session counts and realistic mental health conversations.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import requests
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

API_URL = "http://localhost:8000"


def create_student(student_data):
    """Create a student profile."""
    response = requests.post(f"{API_URL}/students", json=student_data)
    if response.ok:
        return response.json()
    else:
        print(f"❌ Failed to create student: {response.text}")
        return None


def send_message(session_id, message, student_id=None):
    """Send a chat message."""
    payload = {
        "session_id": session_id,
        "message": message
    }
    if student_id:
        payload["student_id"] = student_id
    
    response = requests.post(f"{API_URL}/chat", json=payload)
    if response.ok:
        return response.json()
    else:
        print(f"❌ Failed to send message: {response.text}")
        return None


def seed_students():
    """Seed demo students with conversation histories."""
    
    print("=" * 70)
    print("SEEDING DEMO STUDENTS")
    print("=" * 70)
    
    # ========================================================================
    # STUDENT 1: Alex - 1st Session (New Student, Academic Stress)
    # ========================================================================
    
    print("\n📝 Creating Student 1: Alex (1st Session)")
    print("-" * 70)
    
    alex = create_student({
        "student_id": "S10001",
        "name": "Alex Johnson",
        "preferred_name": "Alex",
        "grade": "10",
        "communication_style": "casual"
    })
    
    if alex:
        print(f"✅ Created: {alex['name']} (Grade {alex['grade']})")
        
        # First conversation - just starting to open up
        print("\n   Session 1 (Today):")
        
        conv1 = send_message("alex_session_1", 
            "Hi, I'm not sure if this will help but I'm feeling really stressed",
            "S10001")
        if conv1:
            print(f"   💬 Alex: Expressed initial stress")
            time.sleep(1)
        
        conv2 = send_message("alex_session_1",
            "It's mostly about school. Finals are coming up and I feel like I'm drowning",
            "S10001")
        if conv2:
            print(f"   💬 Alex: Shared academic pressure")
            time.sleep(1)
        
        conv3 = send_message("alex_session_1",
            "I've been staying up late trying to study but I can't focus",
            "S10001")
        if conv3:
            print(f"   💬 Alex: Mentioned sleep issues and concentration")
    
    # ========================================================================
    # STUDENT 2: Jordan - 3rd Session (Ongoing Anxiety, Making Progress)
    # ========================================================================
    
    print("\n\n📝 Creating Student 2: Jordan (3rd Session)")
    print("-" * 70)
    
    jordan = create_student({
        "student_id": "S10002",
        "name": "Jordan Smith",
        "preferred_name": "Jordan",
        "grade": "11",
        "communication_style": "detailed"
    })
    
    if jordan:
        print(f"✅ Created: {jordan['name']} (Grade {jordan['grade']})")
        
        # Session 1 - 2 weeks ago
        print("\n   Session 1 (2 weeks ago):")
        
        send_message("jordan_session_1",
            "I've been having panic attacks before tests. My heart races and I can't breathe",
            "S10002")
        print(f"   💬 Jordan: First disclosed panic attacks")
        time.sleep(1)
        
        send_message("jordan_session_1",
            "It started last semester but it's getting worse. I'm scared to go to class",
            "S10002")
        print(f"   💬 Jordan: Shared escalation and avoidance")
        time.sleep(1)
        
        send_message("jordan_session_1",
            "My parents don't really understand. They just say I need to try harder",
            "S10002")
        print(f"   💬 Jordan: Mentioned lack of family support")
        time.sleep(1)
        
        # Session 2 - 1 week ago
        print("\n   Session 2 (1 week ago):")
        
        send_message("jordan_session_2",
            "I tried the breathing exercises you mentioned. They helped a little",
            "S10002")
        print(f"   💬 Jordan: Tried coping strategy")
        time.sleep(1)
        
        send_message("jordan_session_2",
            "But I still feel anxious all the time. Like something bad is going to happen",
            "S10002")
        print(f"   💬 Jordan: Persistent anxiety")
        time.sleep(1)
        
        send_message("jordan_session_2",
            "I talked to my school counselor. She's going to help me talk to my parents",
            "S10002")
        print(f"   💬 Jordan: Seeking additional support")
        time.sleep(1)
        
        # Session 3 - Today
        print("\n   Session 3 (Today):")
        
        send_message("jordan_session_3",
            "Hey Connor, I'm back. Things are a bit better",
            "S10002")
        print(f"   💬 Jordan: Returning with update")
        time.sleep(1)
        
        send_message("jordan_session_3",
            "My parents are being more understanding now. We're looking into therapy",
            "S10002")
        print(f"   💬 Jordan: Family support improving")
    
    # ========================================================================
    # STUDENT 3: Sam - 5th Session (Depression, Long-term Support)
    # ========================================================================
    
    print("\n\n📝 Creating Student 3: Sam (5th Session)")
    print("-" * 70)
    
    sam = create_student({
        "student_id": "S10003",
        "name": "Samantha Rodriguez",
        "preferred_name": "Sam",
        "grade": "12",
        "communication_style": "brief"
    })
    
    if sam:
        print(f"✅ Created: {sam['name']} (Grade {sam['grade']})")
        
        # Session 1 - 4 weeks ago
        print("\n   Session 1 (4 weeks ago):")
        
        send_message("sam_session_1",
            "I don't know why I'm here. Nothing really matters anymore",
            "S10003")
        print(f"   💬 Sam: Initial hopelessness")
        time.sleep(1)
        
        send_message("sam_session_1",
            "I used to love art but I haven't drawn in months. Just don't care",
            "S10003")
        print(f"   💬 Sam: Anhedonia (loss of interest)")
        time.sleep(1)
        
        send_message("sam_session_1",
            "My friends keep asking if I'm okay but I just say I'm tired",
            "S10003")
        print(f"   💬 Sam: Social withdrawal")
        time.sleep(1)
        
        # Session 2 - 3 weeks ago
        print("\n   Session 2 (3 weeks ago):")
        
        send_message("sam_session_2",
            "I'm sleeping like 12 hours a day but still exhausted",
            "S10003")
        print(f"   💬 Sam: Hypersomnia")
        time.sleep(1)
        
        send_message("sam_session_2",
            "College applications are due soon. Everyone's excited but I just feel empty",
            "S10003")
        print(f"   💬 Sam: Lack of future motivation")
        time.sleep(1)
        
        # Session 3 - 2 weeks ago
        print("\n   Session 3 (2 weeks ago):")
        
        send_message("sam_session_3",
            "Talked to the school counselor like you suggested",
            "S10003")
        print(f"   💬 Sam: Following through on referral")
        time.sleep(1)
        
        send_message("sam_session_3",
            "She thinks I might have depression. Wants me to see a therapist",
            "S10003")
        print(f"   💬 Sam: Professional assessment")
        time.sleep(1)
        
        send_message("sam_session_3",
            "I'm scared to tell my parents. They'll think I'm weak",
            "S10003")
        print(f"   💬 Sam: Fear of stigma")
        time.sleep(1)
        
        # Session 4 - 1 week ago
        print("\n   Session 4 (1 week ago):")
        
        send_message("sam_session_4",
            "I told my mom. She cried but she's being supportive",
            "S10003")
        print(f"   💬 Sam: Family disclosure")
        time.sleep(1)
        
        send_message("sam_session_4",
            "First therapy appointment is next week. I'm nervous",
            "S10003")
        print(f"   💬 Sam: Starting treatment")
        time.sleep(1)
        
        send_message("sam_session_4",
            "I picked up my sketchbook yesterday. Didn't draw but I looked at old stuff",
            "S10003")
        print(f"   💬 Sam: Small signs of reconnection")
        time.sleep(1)
        
        # Session 5 - Today
        print("\n   Session 5 (Today):")
        
        send_message("sam_session_5",
            "Hey Connor. Had my first therapy session",
            "S10003")
        print(f"   💬 Sam: Treatment update")
        time.sleep(1)
        
        send_message("sam_session_5",
            "It was hard but I think it helped. She wants to see me weekly",
            "S10003")
        print(f"   💬 Sam: Engaging with treatment")
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("✅ DEMO STUDENTS SEEDED SUCCESSFULLY")
    print("=" * 70)
    
    print("\n📊 Summary:")
    print(f"   • Alex (S10001) - 1st session, academic stress, new student")
    print(f"   • Jordan (S10002) - 3rd session, anxiety, making progress")
    print(f"   • Sam (S10003) - 5th session, depression, in treatment")
    
    print("\n🎯 Test Scenarios:")
    print("   1. Login as Alex → See first-time greeting")
    print("   2. Login as Jordan → Connor remembers panic attacks")
    print("   3. Login as Sam → Connor references therapy journey")
    print("   4. Counselor Dashboard → See all 3 students with histories")
    
    print("\n🌐 Access:")
    print(f"   Frontend: http://localhost:3002")
    print(f"   Backend: {API_URL}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        print("\n⏳ Starting in 3 seconds (make sure backend is running)...")
        time.sleep(3)
        seed_students()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to backend at http://localhost:8000")
        print("   Make sure the backend is running: python backend/main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
