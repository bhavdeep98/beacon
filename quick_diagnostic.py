"""
Quick diagnostic to check what's broken.
"""

print("="*80)
print("BEACON DIAGNOSTIC")
print("="*80)

# Test 1: Can we import modules?
print("\n1. Testing imports...")
try:
    from src.safety.safety_analyzer import SafetyService
    print("   ✅ SafetyService imports OK")
except Exception as e:
    print(f"   ❌ SafetyService import failed: {e}")

try:
    from src.orchestrator.agent_graph import CouncilGraph
    print("   ✅ CouncilGraph imports OK")
except Exception as e:
    print(f"   ❌ CouncilGraph import failed: {e}")

try:
    from src.conversation.conversation_agent import ConversationAgent
    print("   ✅ ConversationAgent imports OK")
except Exception as e:
    print(f"   ❌ ConversationAgent import failed: {e}")

# Test 2: Can we create instances?
print("\n2. Testing initialization...")
try:
    from pathlib import Path
    config_path = Path("config/crisis_patterns.yaml")
    service = SafetyService(patterns_path=str(config_path))
    print("   ✅ SafetyService initializes OK")
except Exception as e:
    print(f"   ❌ SafetyService init failed: {e}")

# Test 3: Can we analyze a message?
print("\n3. Testing analysis...")
try:
    result = service.analyze("test message")
    print(f"   ✅ Analysis works: regex={result.p_regex}, semantic={result.p_semantic}")
except Exception as e:
    print(f"   ❌ Analysis failed: {e}")

# Test 4: Check backend health
print("\n4. Testing backend connection...")
try:
    import requests
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print(f"   ✅ Backend is responding: {response.json()}")
    else:
        print(f"   ❌ Backend returned {response.status_code}")
except requests.exceptions.ConnectionError:
    print("   ❌ Backend is not running or not accessible")
except Exception as e:
    print(f"   ❌ Backend check failed: {e}")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
