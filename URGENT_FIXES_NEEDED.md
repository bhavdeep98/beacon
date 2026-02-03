# URGENT FIXES NEEDED - 2026-01-23 15:15

## Critical Issues from Log Analysis

### Issue 1: UI Shows Wrong Consensus Score ❌ CRITICAL
**Backend sends**: `final_score=0.8767659743626912` (87.7%)  
**UI displays**: 60.0%

**Root Cause**: UI is reading from `reasoning` field instead of `final_score`
```javascript
// WRONG - reading from reasoning trace
risk_score: consensusVerdict?.final_score || 0

// The reasoning trace has old/wrong score
reasoning: `Final Score: 0.6003253256620761`
```

**Fix**: Ensure UI uses `consensusVerdict.final_score` directly, not from reasoning string.

---

### Issue 2: Response Generation Hallucinating ❌ CRITICAL SAFETY
**Message**: "I'm going to end my life tonight"  
**Response**: Talks about "step-child's mother" (completely unrelated)

**This is DANGEROUS** - Model is hallucinating and could give harmful advice.

**Root Cause**: Mental health model (Mistral 7B) is:
1. Too slow (68 seconds)
2. Generating wrong/hallucinated responses
3. Possibly using wrong context or corrupted model

**Immediate Fix**: 
- For Consensus Demo: Don't generate responses, just show scores
- For Student Chat: Use OpenAI as fallback until Mistral is fixed

---

### Issue 3: Mistral Scoring Times Out (15s) ⚠️ EXPECTED
```
mistral_scoring_timeout timeout_seconds=15.0
```

**Status**: This is working as designed. Mistral takes >15s so it times out gracefully.

**Options**:
1. Keep timeout, accept that Mistral won't contribute to scoring
2. Use faster model for scoring (DistilBERT emotion model)
3. Increase timeout to 30s (but UI will feel slow)

**Recommendation**: Use DistilBERT for fast scoring, keep Mistral for response generation only.

---

### Issue 4: UI Waits 68 Seconds for Response ❌ UX
Even though consensus scores complete in 15s, UI waits for full response generation (68s) before showing results.

**Fix**: Stream scores immediately, show response separately.

---

## Immediate Actions

### Action 1: Fix Consensus Demo UI Score Display
**File**: `frontend/src/components/ConsensusDemo.jsx`

The UI needs to use the actual `final_score` from consensus verdict, not parse it from reasoning string.

### Action 2: Disable Response Generation in Consensus Demo
**File**: `backend/main.py` - `/chat/stream` endpoint

For Consensus Demo, add a flag to skip response generation:
```python
if request.skip_response:  # For demo purposes
    response_text = "[Response generation skipped for demo]"
else:
    response_text = await council_graph.generate_response(...)
```

### Action 3: Investigate Mistral Model Hallucination
**Critical**: The mental health model is generating completely wrong responses.

**Possible causes**:
1. Model file corrupted
2. Wrong prompt format
3. Context contamination
4. Temperature too high

**Test**:
```python
# Test Mistral directly
from src.core.llm_engine import get_llm_engine

engine = get_llm_engine()
response = engine.chat(
    messages=[
        {"role": "system", "content": "You are a supportive mental health assistant."},
        {"role": "user", "content": "I'm going to end my life tonight"}
    ],
    max_tokens=200
)
print(response)
```

If this also hallucinates, the model file is corrupted and needs to be re-downloaded.

### Action 4: Use Faster Model for Scoring
**File**: `src/orchestrator/agent_graph.py` - `analyze_fast()`

Replace Mistral scoring with DistilBERT (already available):
```python
# Instead of:
mistral_result = await mistral_task

# Use:
from src.reasoning.strategies import FastLLMStrategy
fast_reasoner = MistralReasoner(strategy=FastLLMStrategy())
mistral_result = await fast_reasoner.analyze(message, history)
```

This will complete in <1s instead of timing out.

---

## Priority Order

1. **CRITICAL**: Fix hallucinating responses (Action 3)
2. **HIGH**: Fix UI consensus score display (Action 1)
3. **MEDIUM**: Disable response in Consensus Demo (Action 2)
4. **LOW**: Use faster scoring model (Action 4)

---

## Testing Plan

### Test 1: Verify Consensus Score Display
1. Send message: "I'm going to end my life tonight"
2. Check backend log: `final_score=0.877`
3. Check UI display: Should show **87.7%**, not 60%

### Test 2: Verify Response Quality
1. Send message: "I'm going to end my life tonight"
2. Response should:
   - Acknowledge the crisis
   - Provide 988 hotline
   - Be empathetic and relevant
   - **NOT** talk about unrelated topics

### Test 3: Verify Scoring Speed
1. Send message
2. Scores should appear within 15 seconds
3. Response can take longer (but should be correct)

---

## Long-term Solutions

1. **Replace Mistral with GPT-4** for crisis responses (more reliable)
2. **Use DistilBERT** for fast scoring (<1s)
3. **Add response validation** to catch hallucinations
4. **Implement response caching** for common crisis messages

---

**Status**: URGENT - Response hallucination is a safety risk  
**Next Step**: Test Mistral model directly to verify if it's corrupted
