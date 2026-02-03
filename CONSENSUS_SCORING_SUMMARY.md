# Beacon Consensus Scoring System - Technical Summary

## Overview

The consensus scoring system is Beacon's multi-layer crisis detection engine that combines three independent detection strategies to make final risk assessments. It uses weighted scoring with graceful degradation and safety-first principles.

## Architecture

```
Student Message
       ↓
┌──────────────────────────────────────┐
│   Consensus Orchestrator             │
│   (Parallel Execution)               │
└──────────────────────────────────────┘
       ↓
┌──────┴──────┬──────────────┬─────────┐
│             │              │         │
│  Regex      │  Semantic    │ Mistral │
│  Layer      │  Layer       │ Layer   │
│  (Fast)     │  (Fast)      │ (Slow)  │
│  ~5ms       │  ~25ms       │ ~2min   │
│             │              │         │
└──────┬──────┴──────────────┴─────────┘
       ↓
┌──────────────────────────────────────┐
│   Weighted Consensus Calculation     │
│   S_c = Σ(weight × score)            │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Risk Level Decision                │
│   CRISIS / CAUTION / SAFE            │
└──────────────────────────────────────┘
```

## Three Detection Layers

### 1. Regex Layer (Deterministic)
- **Purpose**: Fast keyword matching for explicit crisis language
- **Weight**: 40% (highest trust)
- **Latency**: ~5ms
- **Method**: Compiled regex patterns against crisis keywords
- **Examples**:
  - "kill myself" → 0.95 confidence (suicidal_ideation)
  - "hurt myself" → 0.85 confidence (self_harm)
  - "end my life" → 0.95 confidence (suicidal_ideation)

**Safety Floor**: If regex detects crisis with ≥0.95 confidence, final decision is CRISIS regardless of other layers.

### 2. Semantic Layer (Embedding-Based)
- **Purpose**: Catch obfuscated/paraphrased crisis language
- **Weight**: 20%
- **Latency**: ~25ms
- **Method**: Sentence embeddings + cosine similarity to crisis patterns
- **Examples**:
  - "checking out early" (with crisis context) → 0.85
  - "not worth being here" → 0.80
  - "want to disappear" → 0.75

**Sarcasm Filter**: If hyperbole detected (p_sarcasm > 0.7), semantic score reduced by 90%
- "This homework is killing me" → sarcasm filtered → score × 0.1

### 3. Mistral Layer (Clinical Reasoning)
- **Purpose**: Deep clinical pattern analysis with context
- **Weight**: 30%
- **Latency**: ~2 minutes (with timeout protection)
- **Method**: DistilBERT emotion detection + rule-based clinical markers
- **Features**:
  - Maps to PHQ-9 (depression), GAD-7 (anxiety), C-SSRS (suicide risk)
  - Context-aware (uses conversation history)
  - Explainable reasoning traces
  - Intelligent strategy selection (Fast vs Expert)

**Graceful Degradation**: If Mistral times out or fails, its weight (30%) is redistributed to regex layer (safety floor).

## Consensus Scoring Formula

### Standard Formula (All Layers Available)
```
S_c = (w_regex × P_regex) + (w_semantic × P_semantic) + (w_mistral × P_mistral) + (w_history × P_history)

Where:
- w_regex = 0.40 (deterministic safety floor)
- w_semantic = 0.20 (catches obfuscation)
- w_mistral = 0.30 (clinical reasoning)
- w_history = 0.10 (future: conversation patterns)
- Weights sum to 1.0
```

### Fallback Formula (Mistral Timeout)
```
S_c = (w_adjusted_regex × P_regex) + (w_semantic × P_semantic)

Where:
- w_adjusted_regex = 0.40 + 0.30 = 0.70 (absorbs Mistral's weight)
- w_semantic = 0.20
```

## Risk Level Decision

```python
if regex_score >= 0.95:
    return CRISIS  # Safety floor override
elif final_score >= 0.90:
    return CRISIS
elif final_score >= 0.65:
    return CAUTION
else:
    return SAFE
```

### Thresholds
- **CRISIS**: ≥0.90 (immediate counselor notification)
- **CAUTION**: ≥0.65 (weekly check-in)
- **SAFE**: <0.65 (no action)

## Example Scenarios

### Scenario 1: Explicit Crisis (Regex Dominant)
```
Message: "I want to kill myself"

Layer Scores:
- Regex: 0.95 (matched: suicidal_ideation)
- Semantic: 0.90 (high similarity)
- Mistral: 0.92 (C-SSRS: ideation_with_intent)

Calculation:
S_c = (0.40 × 0.95) + (0.20 × 0.90) + (0.30 × 0.92)
    = 0.38 + 0.18 + 0.276
    = 0.836

Safety Floor Override: regex_score (0.95) >= 0.95
Final Decision: CRISIS (via safety floor)
```

### Scenario 2: Obfuscated Crisis (Semantic + Mistral)
```
Message: "I'm checking out early tonight"
Context: ["I can't take it anymore", "Everything is hopeless"]

Layer Scores:
- Regex: 0.0 (no keyword match)
- Semantic: 0.85 (context clarifies intent)
- Mistral: 0.88 (C-SSRS: ideation, context-aware)

Calculation:
S_c = (0.40 × 0.0) + (0.20 × 0.85) + (0.30 × 0.88)
    = 0.0 + 0.17 + 0.264
    = 0.434

Final Decision: SAFE (below 0.65 threshold)
Note: This demonstrates need for history weight (future milestone)
```

### Scenario 3: Hyperbole Filtered
```
Message: "This homework is killing me"

Layer Scores:
- Regex: 0.0 (no crisis keyword)
- Semantic: 0.60 (before filter)
- Sarcasm: 0.85 (hyperbole detected)
- Semantic (filtered): 0.06 (0.60 × 0.1)
- Mistral: 0.05 (low risk)

Calculation:
S_c = (0.40 × 0.0) + (0.20 × 0.06) + (0.30 × 0.05)
    = 0.0 + 0.012 + 0.015
    = 0.027

Final Decision: SAFE
```

### Scenario 4: Mistral Timeout (Graceful Degradation)
```
Message: "I'm feeling really down lately"

Layer Scores:
- Regex: 0.0 (no crisis keyword)
- Semantic: 0.55 (mild concern)
- Mistral: TIMEOUT (circuit breaker open)

Fallback Calculation:
S_c = (0.70 × 0.0) + (0.20 × 0.55)
    = 0.0 + 0.11
    = 0.11

Final Decision: SAFE
Note: Mistral's weight redistributed to regex (safety floor)
```

## Intelligent Strategy Selection (Mistral Layer)

The Mistral layer uses dynamic strategy selection to balance speed and accuracy:

### Fast Strategy (Default)
- **Latency**: <100ms
- **Method**: DistilBERT emotion classification + rule-based markers
- **Use Cases**: Routine conversations, low preliminary risk

### Expert Strategy (High-Risk Cases)
- **Latency**: ~2 minutes (with timeout)
- **Method**: Deep clinical reasoning with context
- **Triggers**:
  - Crisis keywords detected
  - High preliminary risk (>0.7)
  - Ambiguous content (short + negative words)

### Selection Logic
```python
1. Run Fast Strategy for preliminary assessment
2. If crisis keywords → Use Expert
3. If preliminary_risk > 0.7 → Use Expert
4. If ambiguous content → Use Expert
5. Otherwise → Return Fast result (meets SLA)
```

### Circuit Breaker
- **Threshold**: 5 consecutive Expert failures
- **Action**: Automatically fall back to Fast Strategy
- **Reset**: On first Expert success
- **Timeout**: 30 seconds before retry

## Performance Characteristics

### Latency Targets
- **Regex Layer**: <10ms (typically ~5ms)
- **Semantic Layer**: <50ms (typically ~25ms)
- **Mistral Fast**: <200ms (typically ~100ms)
- **Mistral Expert**: <120s (2 minutes with timeout)
- **Total (without Mistral)**: <50ms
- **Total (with Mistral Fast)**: <200ms
- **Total (with Mistral Expert)**: <120s

### Parallel Execution
All three layers run in parallel using `asyncio.gather()`:
```python
results = await asyncio.gather(
    regex_task,
    semantic_task,
    mistral_task,
    return_exceptions=True
)
```

### Timeout Protection
- **Mistral Timeout**: 120 seconds (configurable)
- **Total Timeout**: 150 seconds (2.5 minutes)
- **Behavior**: Return partial results if timeout occurs

## Safety Guarantees

### 1. Safety Floor (Tenet #1: Safety First)
Regex layer acts as safety floor - if it detects crisis with high confidence (≥0.95), that decision is final regardless of other layers.

### 2. Fail Loud (Tenet #4)
- Safety layer failures raise exceptions (critical)
- Mistral failures log warnings and fall back gracefully
- All errors include full context for debugging

### 3. Immutable Results (Tenet #7)
All result objects are frozen dataclasses:
- `ConsensusResult` (final decision)
- `LayerScore` (individual layer)
- `ReasoningResult` (Mistral output)

### 4. Event-Driven Crisis Response (Tenet #6)
When crisis detected, event published to CrisisEventBus:
```python
if result.is_crisis():
    event_bus.publish(result)
```

Observers (notification service, audit logger, analytics) receive event independently.

### 5. Observable (Tenet #10)
Every step logged with structured context:
- Layer scores and latency
- Consensus calculation breakdown
- Final decision with reasoning
- Timeout occurrences

## Configuration

### Default Weights (ConsensusConfig)
```python
w_regex = 0.40      # Deterministic safety floor
w_semantic = 0.20   # Catches obfuscation
w_mistral = 0.30    # Clinical reasoning
w_history = 0.10    # Future: conversation patterns
```

### Thresholds
```python
crisis_threshold = 0.90    # CRISIS level
caution_threshold = 0.65   # CAUTION level
```

### Timeouts
```python
mistral_timeout = 120.0    # 2 minutes for clinical reasoning
total_timeout = 150.0      # 2.5 minutes total
```

### Circuit Breaker
```python
circuit_breaker_enabled = True
circuit_breaker_threshold = 5    # failures before opening
circuit_breaker_timeout = 30     # seconds before retry
```

## Explainability

Every consensus result includes:

### 1. Reasoning Trace
```
Risk Level: CRISIS
Final Score: 0.8360

Layer Scores:
  Regex: 0.9500 (weight: 0.40)
  Semantic: 0.9000 (weight: 0.20)
  Mistral: 0.9200 (weight: 0.30)

Evidence:
  Regex matched: suicidal_ideation
  Semantic matched: crisis_intent
  Mistral detected: cssrs_ideation_with_intent
```

### 2. Matched Patterns
List of all crisis categories detected across layers:
- `suicidal_ideation` (regex)
- `crisis_intent` (semantic)
- `cssrs_ideation_with_intent` (Mistral)

### 3. Performance Metrics
- Individual layer latencies
- Total analysis time
- Timeout occurrences
- Weights used

## Testing & Validation

### Golden Test Sets
- MentalChat16K: 16,000 mental health conversations
- Custom crisis test set: 193 cases (expanding to 10,000+)

### Target Metrics
- **Crisis Recall**: ≥99.5% (catch all real crises)
- **False Positive Rate**: <10% (minimize alert fatigue)
- **Latency P95**: <2s (including Mistral)
- **Latency P95 (Fast Path)**: <50ms (without Mistral)

### Validation Tests
```python
# Test consensus calculation
def test_consensus_calculation():
    result = orchestrator.analyze("I want to die")
    assert result.risk_level == RiskLevel.CRISIS
    assert result.final_score >= 0.90

# Test safety floor override
def test_safety_floor_override():
    result = orchestrator.analyze("kill myself")
    assert result.risk_level == RiskLevel.CRISIS
    assert result.regex_score.score >= 0.95

# Test graceful degradation
def test_mistral_timeout_fallback():
    # Simulate Mistral timeout
    result = orchestrator.analyze("test message")
    assert result.timeout_occurred == True
    # Should still return valid result using regex + semantic
```

## Future Enhancements

### 1. History Weight (Milestone 3)
```python
w_history = 0.10  # Conversation pattern analysis
P_history = analyze_conversation_patterns(session_history)
```

### 2. Weight Learning
- A/B testing different weight configurations
- School-specific tuning based on demographics
- Adaptive weights based on counselor feedback

### 3. Multi-Model Ensemble
- Add GPT-4 as fourth layer for complex cases
- Ensemble voting for ambiguous scenarios
- Model-specific circuit breakers

### 4. Real-Time Calibration
- Adjust thresholds based on false positive rate
- Dynamic weight adjustment based on layer performance
- Seasonal/temporal pattern recognition

## Key Design Principles

1. **Safety First**: Regex safety floor cannot be overridden
2. **Explicit Over Clever**: Simple weighted sum, no black box
3. **Fail Loud**: All errors logged with full context
4. **Graceful Degradation**: System works even if Mistral fails
5. **Immutability**: All results frozen for audit trail
6. **Event-Driven**: Crisis events published to observers
7. **Observable**: Every decision traceable and explainable
8. **Performance**: Fast path (<50ms) for routine conversations

## Summary

The consensus scoring system provides robust, explainable crisis detection by:
- Combining three independent detection strategies
- Using weighted scoring with safety floor override
- Providing graceful degradation when components fail
- Maintaining <50ms latency for routine conversations
- Offering full explainability for counselors and auditors
- Ensuring immutable audit trail for compliance

The system prioritizes safety (high recall) while managing alert fatigue (acceptable false positive rate) through intelligent layer weighting and sarcasm filtering.
