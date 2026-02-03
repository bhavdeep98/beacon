# Next Steps: Consensus Calculation Bug

## Summary

The UI shows **87.7%** consensus but the calculation should give **60.0%**.

**Expected**: (0.75 × 0.444) + (0.452 × 0.222) + (0.50 × 0.333) = **60.0%**  
**Actual**: **87.7%**  
**Difference**: 27.7 percentage points

## Changes Made

### 1. Added Detailed Debug Logging ✅

Modified `src/orchestrator/agent_graph.py` `analyze_fast()` function to log:
- Input scores (regex, semantic, mistral)
- Original weights
- Normalized weights
- Individual contributions
- Final score
- Full calculation string

### 2. Added Assertion to Catch Bugs ✅

Added validation that verifies:
```python
if abs(final_score - expected_score) > 0.001:
    raise ValueError("Consensus calculation mismatch")
```

This will **fail loud** if there's a calculation error (Tenet #4).

## Testing Instructions

### Step 1: Restart Backend

```bash
cd backend
python main.py
```

### Step 2: Open Consensus Demo

Navigate to: http://localhost:5173 (or your frontend port)

### Step 3: Send Test Message

Use the "Crisis with Plan" example: "I'm going to end my life tonight"

### Step 4: Check Backend Logs

Look for the `consensus_with_mistral` log entry. It should show:

```
consensus_with_mistral
  regex_score=0.XXX
  semantic_score=0.XXX
  mistral_score=0.XXX
  normalized_w_regex=0.444
  normalized_w_semantic=0.222
  normalized_w_mistral=0.333
  regex_contribution=0.XXX
  semantic_contribution=0.XXX
  mistral_contribution=0.XXX
  final_score=0.XXX  <-- This is the key value
  calculation=(0.XXX*0.444) + (0.XXX*0.222) + (0.XXX*0.333) = 0.XXX
```

### Step 5: Compare Values

**If `final_score` in logs = 0.600 (60.0%)**:
- ✅ Backend calculation is correct
- ❌ Bug is in data flow to UI
- Check: Is backend sending the right value?
- Check: Is UI reading the right field?

**If `final_score` in logs = 0.877 (87.7%)**:
- ❌ Backend calculation is wrong
- Check: What are the input scores?
- Check: Are the weights correct?
- The assertion should catch this and raise an error

**If backend crashes with ValueError**:
- ❌ Calculation mismatch detected
- The assertion caught a bug
- Check the error message for details

## Possible Scenarios

### Scenario A: Input Scores Are Different

The UI might be showing different scores than what's used in calculation.

**Example**:
- Backend calculates with: regex=0.95, semantic=0.80, mistral=0.90
- Backend sends for display: regex=0.75, semantic=0.452, mistral=0.50
- Result: UI shows wrong bars but "correct" consensus

**Check**: Compare scores in `risk_score` events vs `consensus_with_mistral` log

### Scenario B: Wrong Field Being Sent

Backend calculates 60.0% but sends `p_regex` (75.0%) instead of `final_score`.

**Check**: Verify `analysis_result["final_score"]` in `backend/main.py` line ~760

### Scenario C: UI Caching Issue

Old cached data showing wrong scores.

**Fix**: Hard refresh browser (Ctrl+Shift+R) or clear cache

### Scenario D: Weights Are Wrong

Config file has different weights than expected.

**Check**: `src/orchestrator/consensus_config.py` should have:
- w_regex = 0.40
- w_semantic = 0.20
- w_mistral = 0.30

## Expected Log Output

```
2026-01-23 XX:XX:XX [info] calculating_consensus
  regex_score=0.75
  semantic_score=0.452
  mistral_score=0.50
  w_regex=0.4
  w_semantic=0.2
  w_mistral=0.3

2026-01-23 XX:XX:XX [info] consensus_with_mistral
  regex_score=0.75
  semantic_score=0.452
  mistral_score=0.5
  w_regex_original=0.4
  w_semantic_original=0.2
  w_mistral_original=0.3
  total_weight=0.9
  normalized_w_regex=0.444
  normalized_w_semantic=0.222
  normalized_w_mistral=0.333
  weights_sum=1.0
  regex_contribution=0.333
  semantic_contribution=0.100
  mistral_contribution=0.167
  final_score=0.600
  calculation=(0.750*0.444) + (0.452*0.222) + (0.500*0.333) = 0.333 + 0.100 + 0.167 = 0.600

2026-01-23 XX:XX:XX [info] fast_consensus_complete
  final_score=0.6
  risk_level=SAFE

2026-01-23 XX:XX:XX [info] sending_consensus_verdict
  final_score=0.6
  risk_level=SAFE
```

## What to Report Back

Please share:

1. **Backend log output** for `consensus_with_mistral`
2. **UI consensus score** displayed
3. **UI layer scores** (regex, semantic, mistral percentages)
4. **Any errors** or crashes

This will help identify exactly where the bug is.

---

**Status**: AWAITING TEST RESULTS  
**Priority**: P1 - Affects decision-making accuracy  
**Tenet**: #9 (Visibility), #10 (Observable Systems)
