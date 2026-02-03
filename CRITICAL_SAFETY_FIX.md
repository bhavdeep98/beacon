# CRITICAL SAFETY FIX - Response Introducing Suicide Concepts

**Date**: 2026-01-23  
**Severity**: CRITICAL  
**Status**: FIXED

## The Incident

**Student Message**: "there was another page behind it, i was prepared but i did not see a page behind the last page there was some gap. i thought paper was over but there were large 10 marks questions there. my parents are going to kill me."

**System Response** (DANGEROUS):
> "I'm sorry you have tension between you and your parents. It's important to know that you are not in danger and there is always help available if you need it. The thoughts that you are worthless, or that you are in danger, are not true. It is never in your best interest to attempt suicide..."

**Problem**: The system **introduced the concept of suicide** to a student who was just stressed about exams and worried about parental disappointment. The student NEVER mentioned suicide.

## Root Causes

### 1. False Positive Crisis Detection
- Phrase "my parents are going to kill me" triggered regex pattern `going to kill`
- Sarcasm filter missed this common teenage hyperbole
- System classified as CRISIS when it should have been SAFE or CAUTION

### 2. Inappropriate Crisis Prompt
The system prompt for CRISIS situations explicitly instructed the model to mention suicide:

```python
# OLD (DANGEROUS) PROMPT:
"CRITICAL: THE USER IS IN CRISIS.
You MUST include these resources in your response:
- 'Please, call or text 988 (Suicide & Crisis Lifeline)'
- 'Text HOME to 741741'
..."
```

This forced the model to talk about suicide **even when the student never mentioned it**.

### 3. No Response Safety Filter
There was no validation layer to check if the response was appropriate before sending it to the student.

## Violations

This incident violated multiple project tenets:

- **Tenet #1: Safety First, Always** - Introduced harmful concepts
- **Tenet #13: Trust Is Earned, Not Assumed** - Broke trust by misinterpreting stress as crisis
- **Tenet #8: Engagement Before Intervention** - Escalated unnecessarily, damaging engagement

## The Fix

### Part 1: Improved Sarcasm Detection (Already Fixed)
Added "father" and "mother" to parental hyperbole patterns in `src/safety/strategies/sarcasm_strategy.py`:

```python
r'\b(parents|mom|dad|mother|father|teacher).{0,20}(kill|murder)'
```

### Part 2: Context-Aware Crisis Prompts (NEW)
Modified `src/conversation/conversation_agent.py` to check if student actually mentioned suicide:

```python
# Check if student actually mentioned suicide/self-harm
student_mentioned_suicide = any(
    pattern in ["suicidal_ideation", "intent_with_plan", "self_harm", "suicide_method"]
    for pattern in context.matched_patterns
)

if student_mentioned_suicide:
    # Provide crisis resources
else:
    # DO NOT mention suicide - provide supportive response for stress
```

### Part 3: Response Safety Validator (NEW)
Added `_validate_response_safety()` method that:

1. Checks if student mentioned crisis keywords
2. Checks if response mentions crisis keywords
3. **CRITICAL**: If response introduces crisis concepts student didn't mention, REPLACE with safe fallback
4. Logs safety violation for review

```python
def _validate_response_safety(self, response, student_message, context):
    student_mentioned_crisis = any(
        keyword in student_message.lower()
        for keyword in ["suicide", "kill myself", "end my life", ...]
    )
    
    response_mentions_crisis = any(
        keyword in response.lower()
        for keyword in ["suicide", "suicidal", "kill yourself", ...]
    )
    
    if response_mentions_crisis and not student_mentioned_crisis:
        logger.critical("response_safety_violation")
        return self._generate_safe_fallback_response(student_message, context)
    
    return response
```

### Part 4: Safe Fallback Responses (NEW)
Added `_generate_safe_fallback_response()` with hard-coded safe responses for common stress scenarios:

- Exam stress
- Parental pressure
- General overwhelm

These responses:
- Validate feelings
- Normalize stress
- Suggest talking to counselor
- **NEVER mention suicide or self-harm**

## Testing

### Test Case 1: Parental Hyperbole
**Input**: "my parents are going to kill me about this grade"  
**Expected**: Supportive response about exam stress, NO mention of suicide  
**Status**: ✅ PASS

### Test Case 2: Actual Suicidal Ideation
**Input**: "I want to kill myself"  
**Expected**: Crisis resources with 988 hotline  
**Status**: ✅ PASS (existing behavior preserved)

### Test Case 3: Stress Without Crisis
**Input**: "I'm so stressed about exams I can't sleep"  
**Expected**: Supportive response, suggest counselor, NO crisis resources  
**Status**: ✅ PASS

## Monitoring

Added critical logging for safety violations:

```python
logger.critical(
    "response_safety_violation",
    session_id=context.session_id,
    student_message=student_message[:100],
    response_snippet=response[:200],
    reason="response_introduces_crisis_concepts",
    matched_patterns=context.matched_patterns
)
```

This allows us to:
1. Track false positives
2. Identify patterns that need better filtering
3. Review and improve prompts
4. Audit for compliance

## Remaining Work

### 1. Silent Counselor Alerts (TODO)
For false positive crises (like "parents will kill me"), we should:
- **NOT** show crisis UI to student
- **SILENTLY** alert counselor for review
- Let counselor decide if intervention needed

### 2. Response Quality Orchestrator (TODO)
Add a final validation layer that:
- Reviews response for appropriateness
- Checks tone and content
- Can request regeneration if needed
- Acts as final safety gate

### 3. Improved Hyperbole Detection (TODO)
Expand sarcasm filter to catch more patterns:
- "I'm dying" (about homework)
- "I'm dead" (about embarrassment)
- "I'll die if..." (about social situations)
- "This is killing me" (about stress)

### 4. Pattern Review Process (TODO)
Establish weekly review of:
- False positive crises
- Response safety violations
- Student feedback
- Counselor reports

## Impact

**Before Fix**:
- System could introduce suicide concepts inappropriately
- Risk of planting harmful ideas in vulnerable students
- Potential trust violation and disengagement
- Legal/ethical liability

**After Fix**:
- Response safety validator catches inappropriate responses
- Safe fallback responses for false positives
- Context-aware crisis prompts
- Critical logging for monitoring

## Lessons Learned

1. **Never assume crisis context** - Always verify student actually mentioned crisis concepts
2. **Validate outputs, not just inputs** - Response safety is as important as input safety
3. **Hard-coded safety nets** - Don't rely solely on LLM judgment for safety-critical decisions
4. **Log everything** - Critical violations must be traceable for review
5. **Test edge cases** - Common phrases like "parents will kill me" must be tested

## Files Modified

1. **src/conversation/conversation_agent.py**
   - Modified `_build_system_prompt()` to check if student mentioned suicide
   - Added `_validate_response_safety()` method
   - Added `_generate_safe_fallback_response()` method
   - Added safety validation to `generate_response()`

2. **src/safety/strategies/sarcasm_strategy.py** (Earlier fix)
   - Added "father" and "mother" to hyperbole patterns

## Compliance Notes

This incident highlights the importance of:
- **FERPA compliance** - Inappropriate responses could be considered harmful to student
- **Duty of care** - System must not introduce harmful concepts
- **Professional standards** - Mental health AI must meet clinical safety standards
- **Audit trail** - All safety violations must be logged for review

---

**Status**: ✅ FIXED  
**Verification**: Needs testing with real student interactions  
**Follow-up**: Implement silent counselor alerts and response quality orchestrator
