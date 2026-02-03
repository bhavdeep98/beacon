# Beacon Adaptive Consensus Algorithm (BACA) Strategy

## Core Philosophy
**"Better Late Than Sorry"**
In a high-stakes mental health environment, accuracy supersedes speed. However, we leverage **Empathic Latency** to turn processing time into a user experience feature—signaling care and "thinking" rather than lag.

## The Architecture: "The Consensus Council"

We leverage our meticulously developed `ConsensusOrchestrator` system to implement the **Distributed Council** architecture. This maps our abstract strategy directly to our existing, robust code components.

### The Agents (Implementation Map)

1.  **The Orchestrator (The Dispatcher)**: `ConsensusOrchestrator`
    *   **Code:** `src/orchestrator/consensus_orchestrator.py`
    *   **Role:** Coordinates the parallel execution of safety checks and reasoning.
    *   **Goal:** Routes traffic and determines the "Green/Yellow/Red" path based on consensus scores.

2.  **The Reflex Agent (The Sentry)**: `SafetyService`
    *   **Code:** `src/safety/safety_analyzer.py`
    *   **Tools:** Regex Patterns + Semantic Router (Embeddings).
    *   **Speed:** <50ms.
    *   **Role:** Immediate threat detection ("Safety Floor").

3.  **The Clinical Agent (The Expert)**: `MistralReasoner`
    *   **Code:** `src/reasoning/mistral_reasoner.py`
    *   **Tools:** DistilBERT Emotion + Rule-based Markers (PHQ-9, GAD-7).
    *   **Speed:** ~200-500ms.
    *   **Role:** Deep clinical reasoning and consensus verification.
    *   **Goal:** Provide the "Second Opinion" for the Orchestrator.

4.  **The Empathy Agent (The Peer)**: `ConversationAgent`
    *   **Code:** `src/conversation/conversation_agent.py`
    *   **Tools:** `GPT-4o-mini` (or Fine-Tuned Llama).
    *   **Speed:** Streamed.
    *   **Role:** The actual interface that speaks to the user.
    *   **Goal:** Synthesize the Orchestrator's decision into a warm, natural response.

---

## The Distributed Workflow

The `ConsensusOrchestrator` manages the flow between these components.

### Scenario A: The "Green Path" (Low Risk)
*Example: "I failed my math test today."*

1.  **Orchestrator** calls `SafetyService` (Reflex) & `MistralReasoner` (Expert) in parallel.
2.  **Reflex:** No matches (`p_regex < 0.85`).
3.  **Expert:** No markers (`risk_level: SAFE`).
4.  **Consensus:** SAFE.
5.  **Action:** `ConversationAgent` (Empathy) is called with standard prompt.
    *   *Result:* Fast, supportive response.

### Scenario B: The "Yellow Path" (Ambiguous)
*Example: "I just want to disappear sometimes."*

1.  **Orchestrator** calls Parallel analysis.
2.  **Reflex:** Matches "depressive_ideation" (`p_semantic > 0.8`).
3.  **Expert:** Detects "High Sadness" + "Ambiguous Marker".
4.  **Consensus:** CAUTION.
5.  **Action:** calling `ConversationAgent` with **CAUTION PROMPT**.
    *   *Prompt Injection:* "System: The user is ambiguous. Verify safety. Be gentle."
    *   *Result:* Careful, exploratory response.

### Scenario C: The "Red Path" (Crisis)
*Example: "I have a plan to kill myself tonight."*

1.  **Orchestrator** calls Parallel analysis.
2.  **Reflex:** **CRITICAL MATCH** (`p_regex > 0.95`).
3.  **Expert:** Confirms "Suicide Intent".
4.  **Consensus:** CRISIS (Safety Floor triggered).
5.  **Action:** `ConversationAgent` called with **CRISIS PROMPT**.
    *   *Override:* System forces inclusion of 988/Crisis Text Line logic.
    *   *Result:* Immediate, safe, resource-rich response.

---

## "Empathic Latency" as UI
We visualize this "Thinking" process via the `chat_stream` to match the backend effort.

| Time | Backend Action | Frontend UI Status |
| :--- | :--- | :--- |
| 0ms | `Orchestrator.analyze()` starts | *Message sent* |
| 100ms | `SafetyService` & `MistralReasoner` running | *"Connor is reading..."* |
| 500ms | Consensus Calculation | *"Connor is checking safety guidelines..."* |
| 800ms | `ConversationAgent` Generating | *"Connor is formulating a response..."* |
| 1500ms | Response Ready | *Typing animation...* |

---

## Summary of Changes
1.  **Strict Mapping:** We aren't building new agents; we are correctly identifying our existing `SafetyService`, `MistralReasoner`, and `ConversationAgent` as the Council members.
2.  **Orchestrator is King:** The `ConsensusOrchestrator` is the hard-coded logic that weighs the votes (scores) from the Council.
3.  **Leverage Existing Code:** We use the `ConsensusResult` object to pass the state to the `ConversationAgent` context.
