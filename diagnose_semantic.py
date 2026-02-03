"""
Diagnostic script to check semantic layer in detail.
"""

import sys
import logging
from pathlib import Path

# Configure logging to show DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

from src.safety.safety_analyzer import SafetyService

# Initialize service
config_path = Path("config/crisis_patterns.yaml")
print(f"\n{'='*80}")
print(f"Loading SafetyService from: {config_path}")
print(f"{'='*80}\n")

service = SafetyService(patterns_path=str(config_path))

# Test message
message = "I feel hopeless and worthless"

print(f"\n{'='*80}")
print(f"Testing message: '{message}'")
print(f"{'='*80}\n")

result = service.analyze(message)

print(f"\n{'='*80}")
print("RESULTS:")
print(f"{'='*80}")
print(f"  Regex Score:    {result.p_regex:.4f}")
print(f"  Semantic Score: {result.p_semantic:.4f}")
print(f"  Sarcasm Score:  {result.p_sarcasm:.4f}")
print(f"  Is Crisis:      {result.is_crisis}")
print(f"  Patterns:       {result.matched_patterns}")
print(f"  Latency:        {result.latency_ms:.1f}ms")
print(f"{'='*80}\n")

# Check if semantic strategy exists
if 'semantic' in service.strategy_map:
    semantic_strategy = service.strategy_map['semantic']
    print(f"Semantic strategy found!")
    print(f"  Model: {semantic_strategy.model}")
    print(f"  Threshold: {semantic_strategy.similarity_threshold}")
    print(f"  Categories: {list(semantic_strategy.crisis_embeddings.keys())}")
    print(f"  Total patterns: {sum(len(v['phrases']) for v in semantic_strategy.crisis_embeddings.values())}")
    
    # Show patterns for each category
    for category, config in semantic_strategy.crisis_embeddings.items():
        print(f"\n  {category}: {len(config['phrases'])} patterns")
        for phrase in config['phrases'][:3]:  # Show first 3
            print(f"    - {phrase}")
        if len(config['phrases']) > 3:
            print(f"    ... and {len(config['phrases']) - 3} more")
else:
    print("ERROR: Semantic strategy not found!")
    print(f"Available strategies: {list(service.strategy_map.keys())}")
