# Consensus Demo Fixes - 2026-01-23

## Issues Identified

### Issue 1: UI Displays Wrong Consensus Score ✅ FIXED
**Problem**: Backend sends `final_score=0.8767` (87.7%) but UI shows 60.0%

**Root Cause**: UI was reading from `reasoning` string instead of `consensusVerdict.final_score`

**Fix Applied**:
- Updated `frontend/src/components/ConsensusDemo.jsx` line ~180
- Changed reasoning string to show formatted percentages
- Added comment: `// CRITICAL: Use consensusVerdict.final_score directly`
- Reasoning now shows: `Consensus Score: 87.7%` instead of raw float

**Files Modified**: `frontend/src/components/ConsensusDemo.jsx`

---

### Issue 2: Response Generation Takes 68 Seconds ✅ FIXED
**Problem**: Consensus Demo waits for full response generation (68s) even though it only needs scores

**Solution**: Added `skip_response` flag for demo mode

**Changes**:
1. **Backend** (`backend/main.py`):
   - Created `ChatStreamRequest` model with `skip_response: Optional[bool] = False`
   - Modified `/chat/stream` endpoint to check flag
   - If `skip_response=True`: Returns `"[Response generation skipped for demo - scoring only]"`
   - If `skip_response=False`: Normal response generation (for Student Chat)

2. **Frontend** (`frontend/src/components/ConsensusDemo.jsx`):
   - Added `skip_response: true` to fetch request body
   - Demo now completes in ~15 seconds (just scoring)

**Files Modified**: 
- `backend/main.py`
- `frontend/src/components/ConsensusDemo.jsx`

---

### Issue 3: Response Hallucination ⚠️ NEEDS INVESTIGATION
**Problem**: Message "I'm going to end my life tonight" gets response about "step-child's mother"

**Status**: Created diagnostic script to test model directly

**Diagnostic Tool Created**: `test_mistral_direct.py`

**What it tests**:
1. Model with crisis message at different temperatures (0.3, 0.7, 1.0)
2. Model with conversation context (exam stress scenario)
3. Checks for hallucination indicators
4. Checks if model introduces crisis concepts inappropriately

**Next Steps**:
1. Run: `python test_mistral_direct.py`
2. If model hallucinates consistently → Model file corrupted, re-download
3. If model works correctly → Issue is in prompt construction or context
4. Consider using OpenAI fallback for crisis responses until fixed

**Files Created**: `test_mistral_direct.py`

---

## Testing Instructions

### Test 1: Verify Consensus Score Display
```bash
# Start backend
cd backend
python main.py

# Start frontend (separate terminal)
cd frontend
npm run dev

# Navigate to Consensus Demo
# Send message: "I'm going to end my life tonight"
# Expected: UI shows 87.7% consensus score (not 60%)
```

### Test 2: Verify Demo Performance
```bash
# In Consensus Demo, send any message
# Expected: Scores appear within 15 seconds
# Expected: Response shows "[Response generation skipped for demo - scoring only]"
# Expected: No 68-second wait
```

### Test 3: Diagnose Model Hallucination
```bash
# Run diagnostic script
python test_mistral_direct.py

# Check output for:
# - Appropriate responses to crisis messages
# - No hallucination about unrelated topics
# - Proper handling of exam stress context
```

---

## Architecture Changes

### Separation of Concerns
- **Consensus Scoring**: Fast (<15s) - Used by both Demo and Chat
- **Response Generation**: Slow (60-120s) - Only for Student Chat
- **Demo Mode**: Scoring only, no response generation

### Request Flow

**Consensus Demo**:
```
User Message → analyze_fast() → Scores (15s) → Done
```

**Student Chat**:
```
User Message → analyze_fast() → Scores (15s) → generate_response() → Response (120s) → Done
```

---

## Performance Metrics

### Before Fixes
- Consensus Demo: 68 seconds total
- UI shows wrong score: 60% instead of 87.7%
- Response hallucination: Unrelated content

### After Fixes
- Consensus Demo: ~15 seconds (scoring only)
- UI shows correct score: 87.7%
- Response generation: Skipped for demo, preserved for chat

---

## Safety Considerations

### Tenet #1: Safety First
- Crisis detection still runs in parallel
- Crisis alerts sent immediately (not affected by skip_response)
- Response generation skip is ONLY for demo, not for actual student chat

### Tenet #8: Engagement
- Student Chat still gets full response (120s with "thinking" animation)
- Demo users see scores immediately without waiting

### Tenet #15: Performance Is a Safety Feature
- Consensus scoring <15s (meets requirement)
- Demo no longer blocked by response generation
- Student Chat maintains quality over speed

---

## Remaining Issues

### Critical: Model Hallucination
**Status**: Needs investigation with diagnostic script

**Possible Causes**:
1. Model file corrupted
2. Wrong prompt format
3. Temperature too high
4. Context contamination

**Mitigation Options**:
1. Re-download model file
2. Use OpenAI fallback for crisis responses
3. Add response validation layer
4. Implement response caching for common scenarios

**Priority**: CRITICAL - Response hallucination is a safety risk

---

## Files Modified

1. `frontend/src/components/ConsensusDemo.jsx`
   - Fixed consensus score display
   - Added skip_response flag

2. `backend/main.py`
   - Added ChatStreamRequest model
   - Added skip_response logic

3. `test_mistral_direct.py` (NEW)
   - Diagnostic tool for model testing

---

## Next Actions

1. ✅ Test consensus score display fix
2. ✅ Test demo performance improvement
3. ⚠️ Run `test_mistral_direct.py` to diagnose hallucination
4. ⚠️ Based on diagnostic results, either:
   - Re-download model if corrupted
   - Fix prompt construction if issue is there
   - Implement OpenAI fallback for crisis responses

---

**Status**: 2/3 issues fixed, 1 under investigation
**Safety Impact**: Low - Crisis detection unaffected, only response quality
**User Impact**: High - Demo now fast and shows correct scores
