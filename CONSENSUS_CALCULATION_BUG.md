# Consensus Calculation Bug - 2026-01-23

## Problem

UI shows consensus score of **87.7%** but manual calculation gives **60.0%**

### UI Display:
- Regex: 75.0%
- Semantic: 45.2%
- Mistral: 50.0%
- **Consensus: 87.7%** ❌

### Expected Calculation:

**Weights** (from `consensus_config.py`):
- w_regex = 0.40
- w_semantic = 0.20
- w_mistral = 0.30
- w_history = 0.10 (not used)

**Total weight** (excluding history): 0.90

**Normalized weights**:
- regex: 0.40 / 0.90 = 0.444 (44.4%)
- semantic: 0.20 / 0.90 = 0.222 (22.2%)
- mistral: 0.30 / 0.90 = 0.333 (33.3%)

**Calculation**:
```
(0.75 × 0.444) + (0.452 × 0.222) + (0.50 × 0.333)
= 0.333 + 0.100 + 0.167
= 0.600 (60.0%)
```

**Expected**: 60.0%  
**Actual**: 87.7%  
**Difference**: 27.7 percentage points!

---

## Possible Causes

### 1. Wrong Scores Being Used
The backend might be using different scores than what's displayed in the UI.

**Check**: Look at backend logs for `consensus_with_mistral` or `fast_consensus_complete` entries

### 2. Calculation Bug
There might be a bug in the consensus calculation logic.

**Status**: Code review shows calculation is correct

### 3. Wrong Score Being Sent
The backend might calculate 60.0% but send a different value (like `p_regex` instead of `final_score`)

**Check**: Verify `analysis_result["final_score"]` is what's being sent

### 4. UI Reading Wrong Field
The UI might be reading from the wrong field in the response.

**Status**: Fixed - UI now reads `consensusVerdict.final_score` directly

### 5. Caching Issue
Old cached data might be showing wrong scores.

**Check**: Clear browser cache and test again

---

## Investigation Steps

### Step 1: Check Backend Logs ✅ NEEDED

Run the Consensus Demo and check backend logs for:

```
consensus_with_mistral
  regex_score=0.75
  semantic_score=0.452
  mistral_score=0.50
  normalized_w_regex=0.444
  normalized_w_semantic=0.222
  normalized_w_mistral=0.333
  calculation=(0.75*0.444) + (0.452*0.222) + (0.50*0.333)
  final_score=0.600  <-- Should be 0.600, not 0.877
```

If `final_score=0.877` in logs → Bug is in calculation  
If `final_score=0.600` in logs → Bug is in data flow

### Step 2: Test with Real Backend

Run: `python test_backend_calculation.py`

This will show what the backend actually calculates.

### Step 3: Check Data Flow

Verify the flow:
1. `council_graph.analyze_fast()` returns `final_score`
2. Backend sends `analysis_result["final_score"]` in consensus_verdict
3. UI reads `consensusVerdict.final_score`

---

## Potential Bugs Found

### Bug Hypothesis #1: Using Wrong Score Variable

Maybe somewhere in the code, we're using `safety_result.p_regex` instead of `final_score`?

**Check locations**:
- `backend/main.py` line ~775: `final_score = analysis_result["final_score"]`
- `src/orchestrator/agent_graph.py` line ~410: `return {"final_score": final_score}`

### Bug Hypothesis #2: Scores Are Different

Maybe the scores displayed in UI (75%, 45.2%, 50%) are NOT the scores used in calculation?

**Possible scenario**:
- Backend calculates with scores: (0.95, 0.80, 0.90) → 87.7%
- But sends display scores: (0.75, 0.452, 0.50) for UI bars
- UI shows wrong bars but correct consensus

**Check**: Compare scores in `risk_score` events vs scores in `consensus_verdict`

---

## Fix Strategy

### Immediate Fix: Add Explicit Logging

Add detailed logging to trace exact values:

```python
# In agent_graph.py analyze_fast()
logger.info(
    "CONSENSUS_DEBUG",
    regex_input=regex_score,
    semantic_input=semantic_score,
    mistral_input=mistral_score,
    normalized_w_regex=normalized_w_regex,
    normalized_w_semantic=normalized_w_semantic,
    normalized_w_mistral=normalized_w_mistral,
    regex_contribution=regex_score * normalized_w_regex,
    semantic_contribution=semantic_score * normalized_w_semantic,
    mistral_contribution=mistral_score * normalized_w_mistral,
    final_score_calculated=final_score,
    final_score_type=type(final_score).__name__
)
```

### Verification Fix: Add Assertion

```python
# After calculation
expected = (
    regex_score * normalized_w_regex +
    semantic_score * normalized_w_semantic +
    mistral_score * normalized_w_mistral
)

if abs(final_score - expected) > 0.001:
    logger.error(
        "CONSENSUS_CALCULATION_MISMATCH",
        final_score=final_score,
        expected=expected,
        difference=abs(final_score - expected)
    )
    raise ValueError(f"Consensus calculation mismatch: {final_score} != {expected}")
```

---

## Next Steps

1. ✅ Run Consensus Demo and capture backend logs
2. ✅ Look for `consensus_with_mistral` log entry
3. ✅ Check if `final_score` in logs is 0.600 or 0.877
4. ⚠️ If 0.877 → Bug is in calculation logic
5. ⚠️ If 0.600 → Bug is in data flow to UI

---

**Status**: INVESTIGATION NEEDED  
**Priority**: P1 - Incorrect consensus scores affect decision-making  
**Safety Impact**: HIGH - Wrong scores could lead to missed crises or false alarms

**Tenet Violation**: Tenet #9 (Visibility and Explainability) - Scores don't match calculation
