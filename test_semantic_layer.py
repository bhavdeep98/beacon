"""
Quick test to verify semantic layer is working properly.
"""

from pathlib import Path
from src.safety.safety_analyzer import SafetyService

# Initialize service
config_path = Path("config/crisis_patterns.yaml")
service = SafetyService(patterns_path=str(config_path))

# Test messages
test_cases = [
    ("I want to kill myself", "Should trigger regex AND semantic"),
    ("I'm checking out early", "Should trigger semantic with context"),
    ("Time to disappear forever", "Should trigger semantic (obfuscated)"),
    ("I feel hopeless and worthless", "Should trigger semantic"),
    ("This homework is killing me", "Should NOT trigger (hyperbole)"),
    ("I'm stressed about exams", "Should NOT trigger (safe)"),
]

print("\n" + "="*80)
print("SEMANTIC LAYER TEST")
print("="*80 + "\n")

for message, expected in test_cases:
    result = service.analyze(message)
    
    print(f"Message: {message}")
    print(f"Expected: {expected}")
    print(f"  Regex Score:    {result.p_regex:.3f}")
    print(f"  Semantic Score: {result.p_semantic:.3f}")
    print(f"  Sarcasm Score:  {result.p_sarcasm:.3f}")
    print(f"  Is Crisis:      {result.is_crisis}")
    print(f"  Patterns:       {result.matched_patterns}")
    print(f"  Sarcasm Filter: {result.sarcasm_filtered}")
    print(f"  Latency:        {result.latency_ms:.1f}ms")
    print()

# Test with context
print("\n" + "="*80)
print("SEMANTIC LAYER WITH CONTEXT TEST")
print("="*80 + "\n")

context = ["I can't take it anymore", "Everything is hopeless"]
message = "I'm checking out early"

result = service.analyze(message, context=context)

print(f"Context: {context}")
print(f"Message: {message}")
print(f"  Regex Score:    {result.p_regex:.3f}")
print(f"  Semantic Score: {result.p_semantic:.3f}")
print(f"  Sarcasm Score:  {result.p_sarcasm:.3f}")
print(f"  Is Crisis:      {result.is_crisis}")
print(f"  Patterns:       {result.matched_patterns}")
print()

print("="*80)
print("If semantic scores are all 0.0, there's an issue with the model.")
print("="*80)
