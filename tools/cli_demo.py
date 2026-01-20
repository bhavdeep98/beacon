#!/usr/bin/env python3
"""
High-Throughput CLI Demo Tool

Demonstrates Safety Service capabilities:
- Real-time crisis detection
- Latency measurement
- Pattern matching visualization
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.safety.service import SafetyService
import structlog


def setup_logging():
    """Configure structured logging for demo."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer()
        ]
    )


def print_result(message: str, result):
    """Pretty print analysis result."""
    print("\n" + "="*70)
    print(f"MESSAGE: {message}")
    print("="*70)
    print(f"🚨 CRISIS DETECTED: {'YES' if result.is_crisis else 'NO'}")
    print(f"📊 Regex Score:     {result.p_regex:.3f}")
    print(f"🧠 Semantic Score:  {result.p_semantic:.3f}")
    print(f"⚡ Latency:         {result.latency_ms:.2f}ms")
    
    if result.matched_patterns:
        print(f"🎯 Matched Patterns: {', '.join(result.matched_patterns)}")
    
    # Visual indicator
    if result.is_crisis:
        print("\n🆘 CRISIS PROTOCOL ACTIVATED")
        print("   → Counselor notification triggered")
        print("   → Crisis resources displayed to student")
    else:
        print("\n✅ SAFE - Continue conversation")
    
    print("="*70)


def interactive_mode(service: SafetyService):
    """Interactive CLI mode."""
    print("\n" + "="*70)
    print("PsyFlo Safety Service - Interactive Demo")
    print("="*70)
    print("Type messages to analyze (or 'quit' to exit)")
    print("="*70 + "\n")
    
    while True:
        try:
            message = input("Student message: ").strip()
            
            if message.lower() in ['quit', 'exit', 'q']:
                print("\nExiting...")
                break
            
            if not message:
                continue
            
            result = service.analyze(message)
            print_result(message, result)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def batch_mode(service: SafetyService, test_cases: list):
    """Batch processing mode with predefined test cases."""
    print("\n" + "="*70)
    print("PsyFlo Safety Service - Batch Demo")
    print("="*70 + "\n")
    
    results = []
    
    for message in test_cases:
        result = service.analyze(message)
        results.append((message, result))
        print_result(message, result)
    
    # Summary statistics
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    total = len(results)
    crisis_count = sum(1 for _, r in results if r.is_crisis)
    avg_latency = sum(r.latency_ms for _, r in results) / total
    max_latency = max(r.latency_ms for _, r in results)
    
    print(f"Total Messages:    {total}")
    print(f"Crisis Detected:   {crisis_count} ({crisis_count/total*100:.1f}%)")
    print(f"Average Latency:   {avg_latency:.2f}ms")
    print(f"Max Latency:       {max_latency:.2f}ms")
    print(f"SLA Compliance:    {'✅ PASS' if max_latency < 50 else '❌ FAIL'} (<50ms)")
    print("="*70 + "\n")


def main():
    """Main entry point."""
    setup_logging()
    
    print("\n🔧 Initializing Safety Service...")
    service = SafetyService(patterns_path="config/crisis_patterns.yaml")
    print("✅ Safety Service initialized\n")
    
    # Check if batch mode requested
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        # Predefined test cases
        test_cases = [
            # Crisis cases
            "I want to die",
            "I'm going to kill myself tonight",
            "I have a plan to end my life",
            "I cut myself last night",
            
            # Boundary cases
            "This homework is killing me",
            "I'm dying of boredom",
            "I feel alive and happy",
            
            # Obfuscated cases
            "I'm checking out early",
            "Time to disappear forever",
            
            # Safe cases
            "I'm feeling anxious about the test",
            "Can you help me with my homework?",
            "I'm having a bad day"
        ]
        
        batch_mode(service, test_cases)
    else:
        interactive_mode(service)


if __name__ == "__main__":
    main()
