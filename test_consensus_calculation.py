"""
Test consensus calculation to verify math is correct.

Expected with scores:
- Regex: 75.0%
- Semantic: 45.2%
- Mistral: 50.0%

Weights (from config):
- w_regex = 0.40
- w_semantic = 0.20
- w_mistral = 0.30
- w_history = 0.10 (not used)

Total weight (excluding history): 0.90

Normalized weights:
- regex: 0.40 / 0.90 = 0.444 (44.4%)
- semantic: 0.20 / 0.90 = 0.222 (22.2%)
- mistral: 0.30 / 0.90 = 0.333 (33.3%)

Expected result:
(0.75 × 0.444) + (0.452 × 0.222) + (0.50 × 0.333)
= 0.333 + 0.100 + 0.167
= 0.600 (60.0%)
"""

from src.orchestrator.consensus_config import ConsensusConfig

def test_consensus_calculation():
    """Test consensus calculation with known values."""
    
    # Scores from screenshot
    regex_score = 0.75
    semantic_score = 0.452
    mistral_score = 0.50
    
    # Config
    config = ConsensusConfig()
    
    print("=" * 80)
    print("CONSENSUS CALCULATION TEST")
    print("=" * 80)
    
    print(f"\nInput Scores:")
    print(f"  Regex:    {regex_score:.3f} ({regex_score*100:.1f}%)")
    print(f"  Semantic: {semantic_score:.3f} ({semantic_score*100:.1f}%)")
    print(f"  Mistral:  {mistral_score:.3f} ({mistral_score*100:.1f}%)")
    
    print(f"\nOriginal Weights:")
    print(f"  w_regex:    {config.w_regex:.2f}")
    print(f"  w_semantic: {config.w_semantic:.2f}")
    print(f"  w_mistral:  {config.w_mistral:.2f}")
    print(f"  w_history:  {config.w_history:.2f} (not used)")
    
    # Calculate total weight (excluding history)
    total_weight = config.w_regex + config.w_semantic + config.w_mistral
    print(f"\nTotal Weight (excluding history): {total_weight:.2f}")
    
    # Normalize weights
    normalized_w_regex = config.w_regex / total_weight
    normalized_w_semantic = config.w_semantic / total_weight
    normalized_w_mistral = config.w_mistral / total_weight
    
    print(f"\nNormalized Weights (sum to 1.0):")
    print(f"  regex:    {normalized_w_regex:.3f} ({normalized_w_regex*100:.1f}%)")
    print(f"  semantic: {normalized_w_semantic:.3f} ({normalized_w_semantic*100:.1f}%)")
    print(f"  mistral:  {normalized_w_mistral:.3f} ({normalized_w_mistral*100:.1f}%)")
    print(f"  SUM:      {normalized_w_regex + normalized_w_semantic + normalized_w_mistral:.3f}")
    
    # Calculate consensus
    final_score = (
        regex_score * normalized_w_regex +
        semantic_score * normalized_w_semantic +
        mistral_score * normalized_w_mistral
    )
    
    print(f"\nCalculation:")
    print(f"  ({regex_score:.3f} × {normalized_w_regex:.3f}) + ({semantic_score:.3f} × {normalized_w_semantic:.3f}) + ({mistral_score:.3f} × {normalized_w_mistral:.3f})")
    print(f"  = {regex_score * normalized_w_regex:.3f} + {semantic_score * normalized_w_semantic:.3f} + {mistral_score * normalized_w_mistral:.3f}")
    print(f"  = {final_score:.3f}")
    
    print(f"\nFinal Consensus Score: {final_score:.4f} ({final_score*100:.1f}%)")
    
    print(f"\n" + "=" * 80)
    print(f"EXPECTED: 60.0%")
    print(f"ACTUAL:   {final_score*100:.1f}%")
    
    if abs(final_score - 0.60) < 0.01:
        print("✅ CALCULATION CORRECT")
    else:
        print("❌ CALCULATION WRONG")
    
    print("=" * 80)
    
    # Now test what happens if we DON'T normalize
    print("\n\n" + "=" * 80)
    print("TESTING WITHOUT NORMALIZATION (WRONG)")
    print("=" * 80)
    
    wrong_score = (
        regex_score * config.w_regex +
        semantic_score * config.w_semantic +
        mistral_score * config.w_mistral
    )
    
    print(f"\nCalculation (using original weights):")
    print(f"  ({regex_score:.3f} × {config.w_regex:.2f}) + ({semantic_score:.3f} × {config.w_semantic:.2f}) + ({mistral_score:.3f} × {config.w_mistral:.2f})")
    print(f"  = {regex_score * config.w_regex:.3f} + {semantic_score * config.w_semantic:.3f} + {mistral_score * config.w_mistral:.3f}")
    print(f"  = {wrong_score:.3f}")
    
    print(f"\nWrong Score: {wrong_score:.4f} ({wrong_score*100:.1f}%)")
    print("=" * 80)
    
    # Test if 87.7% could come from somewhere
    print("\n\n" + "=" * 80)
    print("REVERSE ENGINEERING 87.7%")
    print("=" * 80)
    
    target = 0.877
    
    # Could it be using different scores?
    print(f"\nTarget: {target:.3f} ({target*100:.1f}%)")
    print("\nTrying different combinations...")
    
    # Maybe it's using p_regex directly without normalization?
    if abs(regex_score - target) < 0.01:
        print(f"❌ Could be using regex_score directly: {regex_score}")
    
    # Maybe it's max of all scores?
    max_score = max(regex_score, semantic_score, mistral_score)
    if abs(max_score - target) < 0.01:
        print(f"❌ Could be using max(scores): {max_score}")
    
    # Maybe it's average?
    avg_score = (regex_score + semantic_score + mistral_score) / 3
    print(f"Average of scores: {avg_score:.3f} ({avg_score*100:.1f}%)")
    
    # Maybe it's weighted but with wrong weights?
    # Let's solve: 0.75*a + 0.452*b + 0.50*c = 0.877 where a+b+c=1
    # If a=0.8, b=0.1, c=0.1: 0.75*0.8 + 0.452*0.1 + 0.50*0.1 = 0.6952
    # If a=0.9, b=0.05, c=0.05: 0.75*0.9 + 0.452*0.05 + 0.50*0.05 = 0.7226
    
    # Maybe it's using regex score with some multiplier?
    multiplier = target / regex_score
    print(f"Multiplier to get from regex to target: {multiplier:.3f}")
    
    print("=" * 80)


if __name__ == "__main__":
    test_consensus_calculation()
