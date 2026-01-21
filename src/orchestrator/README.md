# Consensus Orchestrator

The brain of PsyFlo's crisis detection system. Coordinates parallel execution of multiple detection layers and combines their scores using weighted consensus.

## Architecture

```
Student Message
       │
       ▼
ConsensusOrchestrator
       │
       ├─────────────┬─────────────┬─────────────┐
       ▼             ▼             ▼             ▼
   Regex        Semantic       Mistral       History
   Layer         Layer         Layer         Layer
   (5-10ms)     (10-20ms)     (500-2000ms)  (future)
       │             │             │             │
       └─────────────┴─────────────┴─────────────┘
                     │
                     ▼
            Weighted Consensus
         S_c = Σ(w_i × P_i)
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   S_c ≥ 0.90   0.65 ≤ S_c < 0.90  S_c < 0.65
   CRISIS        CAUTION           SAFE
       │             │             │
       ▼             ▼             ▼
  Event Bus     Flag for       Continue
  (notify)      Review         Conversation
```

## Design Patterns

### 1. Observer Pattern (Event-Driven Crisis Response)
When a crisis is detected, the orchestrator publishes an event to the event bus. Multiple observers can subscribe:
- Notification service (alert counselor)
- Audit logger (compliance trail)
- Analytics service (track trends)

### 2. Circuit Breaker (Graceful Degradation)
If Mistral service fails repeatedly, the circuit breaker opens and requests are handled by Safety Service only. This prevents cascading failures.

### 3. Immutable Results
All results are frozen dataclasses that cannot be modified after creation. This prevents accidental state corruption and makes debugging easier.

## Components

### ConsensusOrchestrator
Main coordinator that:
- Runs detection layers in parallel using `asyncio.gather()`
- Combines scores using weighted formula
- Makes final CRISIS/CAUTION/SAFE decision
- Publishes crisis events to event bus

### ConsensusConfig
Configuration for weights, thresholds, and timeouts:
```python
config = ConsensusConfig(
    w_regex=0.40,        # Regex weight
    w_semantic=0.20,     # Semantic weight
    w_mistral=0.30,      # Mistral weight
    w_history=0.10,      # History weight (future)
    crisis_threshold=0.90,
    caution_threshold=0.65,
    mistral_timeout=3.0
)
```

### ConsensusResult
Immutable result containing:
- Final risk level (CRISIS/CAUTION/SAFE)
- Final consensus score
- Individual layer scores (for explainability)
- Reasoning trace (human-readable)
- Performance metrics (latency, timeouts)

## Usage

### Basic Usage
```python
from src.orchestrator import ConsensusOrchestrator, ConsensusConfig
from src.safety.safety_analyzer import SafetyAnalyzer
from src.reasoning.mistral_reasoner import MistralReasoner

# Initialize services
safety = SafetyAnalyzer()
mistral = MistralReasoner()

# Create orchestrator
orchestrator = ConsensusOrchestrator(
    safety_service=safety,
    mistral_reasoner=mistral,
    config=ConsensusConfig()
)

# Analyze message
result = await orchestrator.analyze(
    message="I want to die",
    session_id="session_123"
)

# Check result
if result.is_crisis():
    print(f"CRISIS detected! Score: {result.final_score}")
    print(f"Reasoning: {result.reasoning}")
```

### Subscribe to Crisis Events
```python
def handle_crisis(result: ConsensusResult):
    """Handle crisis event."""
    print(f"Crisis detected: {result.final_score}")
    # Send notification, log to audit trail, etc.

# Subscribe
orchestrator.event_bus.subscribe(handle_crisis)
```

### Custom Configuration
```python
# High-sensitivity config (more false positives, fewer false negatives)
high_sensitivity = ConsensusConfig(
    w_regex=0.50,           # Higher weight on deterministic layer
    w_semantic=0.20,
    w_mistral=0.20,
    w_history=0.10,
    crisis_threshold=0.85,  # Lower threshold
    caution_threshold=0.60
)

orchestrator = ConsensusOrchestrator(
    safety_service=safety,
    mistral_reasoner=mistral,
    config=high_sensitivity
)
```

## Consensus Formula

The weighted consensus score is calculated as:

```
S_c = (w_reg × P_reg) + (w_sem × P_sem) + (w_mistral × P_mistral) + (w_hist × P_hist)
```

Where:
- `P_reg`: Regex detection score (0.0-1.0)
- `P_sem`: Semantic similarity score (0.0-1.0)
- `P_mistral`: Mistral reasoning score (0.0-1.0)
- `P_hist`: Historical trend score (0.0-1.0, future)

Default weights:
- `w_reg = 0.40` (deterministic safety floor)
- `w_sem = 0.20` (catches obfuscation)
- `w_mistral = 0.30` (deep reasoning)
- `w_hist = 0.10` (trajectory analysis, future)

**Note**: These weights are initial values. The system will learn optimal weights via gradient descent optimization (see `evaluation/calibrate_weights.py`).

## Safety Floor

The orchestrator implements a "safety floor" - if the regex layer detects a crisis with very high confidence (≥0.95), the final decision is CRISIS regardless of other layers' scores.

This ensures that explicit crisis keywords always trigger the crisis protocol, even if other layers disagree.

## Graceful Degradation

If Mistral times out or fails:
1. Mistral's weight is redistributed to the regex layer (safety floor)
2. Consensus is calculated using only regex and semantic scores
3. System continues to function (no crash)
4. Timeout is logged and tracked

After multiple failures, the circuit breaker opens and Mistral requests are skipped entirely until the service recovers.

## Performance

Target latencies:
- Regex layer: <10ms
- Semantic layer: <20ms
- Mistral layer: <2000ms (2s)
- Total: <2000ms (P95)

Actual performance depends on hardware and model size.

## Testing

Run tests:
```bash
pytest tests/test_consensus_orchestrator.py -v
```

Run demo:
```bash
# Interactive mode
python tools/consensus_demo.py

# Batch mode with test cases
python tools/consensus_demo.py --batch

# Single message
python tools/consensus_demo.py --message "I want to die"
```

## Explainability

Every result includes a human-readable reasoning trace:

```
Risk Level: CRISIS
Final Score: 0.9250

Layer Scores:
  Regex: 0.9500 (weight: 0.4)
  Semantic: 0.8500 (weight: 0.2)
  Mistral: 0.9000 (weight: 0.3)

Evidence:
  Regex matched: suicidal_ideation, explicit_intent
  Semantic matched: death_wish
  Mistral detected: PHQ9_ITEM_9, C-SSRS_IDEATION
```

This trace is:
- Stored in audit logs (compliance)
- Shown to counselors (context for triage)
- Used for debugging (when crisis is missed)

## Tenets Compliance

- ✅ **Tenet #1 (Safety First)**: Safety floor cannot be overridden
- ✅ **Tenet #3 (Explicit Over Clever)**: Simple asyncio.gather, linear flow
- ✅ **Tenet #4 (Fail Loud)**: All errors logged and raised
- ✅ **Tenet #6 (Event-Driven)**: Crisis events published to bus
- ✅ **Tenet #7 (Immutability)**: All results are frozen dataclasses
- ✅ **Tenet #9 (Visibility)**: Every step logged, reasoning trace included
- ✅ **Tenet #10 (Observable)**: Latency and scores instrumented
- ✅ **Tenet #11 (Graceful Degradation)**: Falls back to Safety if Mistral fails

## Future Enhancements

1. **Weight Learning**: Train optimal weights using gradient descent
2. **History Layer**: Add longitudinal trajectory analysis
3. **Multi-Model Ensemble**: Support multiple Mistral models
4. **A/B Testing**: Test different weight configurations
5. **School-Specific Tuning**: Custom weights per school district
