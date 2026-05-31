# Event Router Pattern

## Intent

Route incoming events to the correct domain orchestrator — deterministically when intent is known, or via a decoupled IntentOrchestrator when it is not — with a guaranteed response in all cases.

> **The Router is the single entry point. Always.**

---

## Motivation

Enterprise AI systems receive events from many sources: structured UI selections, API calls, document uploads, free-text chat messages. Some carry a clear signal — the user selected "Report a Claim." Others are ambiguous — the user typed "I need help with something."

The naive approach embeds classification logic inside the router itself. This couples routing and classification, makes the router harder to test, and violates single responsibility. When the classification strategy changes (rules → LLM → NLP), the router changes too.

A worse approach places an intent classification step *before* the router — making the router no longer the single entry point and adding an invisible pre-processing step that SBBs must know to wire up.

The **Event Router Pattern** solves this by separating routing from classification at the topology level: the Router is always first, and classification (when needed) is delegated to a decoupled `IntentOrchestrator` via a Kafka topic.

---

## Architecture

```
Event → K9EventRouter (single entry point)
    ├── event_type in routing table ──────────────────► domain topic
    └── event_type unknown ──────────► intent.in
                                            │
                              IntentOrchestrator (Kafka consumer)
                                  → IntentSquad → IntentAgent(s)
                                      ├── intent resolved ──► domain topic
                                      └── intent unclear  ──► responses.out

domain topic → Orchestrator → Squads → Agents → LLM
```

### Three routing outcomes

| Outcome | Path | Latency |
|---|---|---|
| Deterministic | event_type in routing table → domain topic directly | Zero — no LLM |
| Non-deterministic, resolved | intent.in → IntentOrchestrator → domain topic | Classification latency |
| Clarification required | intent.in → IntentOrchestrator → responses.out | Classification latency |

Nothing is silently dropped. Every event reaches one of these three outcomes.

---

## Components

| Component | Kind | Responsibility |
|---|---|---|
| `K9EventRouter` | OOB | Single entry point. Deterministic lookup; publishes to `intent.in` on miss. |
| `IntentOrchestrator` | OOB | Kafka consumer on `intent.in`. Runs IntentSquad, re-publishes or asks for clarification. |
| `IntentSquad` | ABB | Wraps one or more `BaseIntentAgent` implementations. Handles confidence gating. |
| `K9IntentAgent` | OOB | Three-step classification: `intent_map` rule lookup → LLM → fallback. |
| `BaseIntentAgent` | ABB abstract | Override `classify()` only — all lifecycle inherited. |

---

## Configuration

```yaml
routing:
  intent_topic:         intent.in       # Router → IntentOrchestrator handoff
  response_topic:       responses.out   # Clarification replies
  confidence_threshold: 0.6             # Below this → ask for clarification
  table:
    claims_submitted: claims.in         # Deterministic: event_type → topic
    fraud_alert:      fraud.in
  intent_map:                           # Fast-path rules for K9IntentAgent (no LLM)
    fraud_report: fraud
    claim_form:   claims
```

---

## SBB Extension Points

### Replace the classification strategy

Override `BaseIntentAgent.classify()` — the only method an SBB must implement:

```python
class DroolsIntentAgent(BaseIntentAgent):
    def classify(self, payload):
        return drools_engine.evaluate(payload)

class ConfigListIntentAgent(BaseIntentAgent):
    def classify(self, payload):
        text = payload.get("message", "").lower()
        for intent, keywords in self._keywords.items():
            if any(kw in text for kw in keywords):
                return intent
        return ""
```

Other strategies: NLP pipeline, Docling document classification, semantic similarity, rules engine (Drools), zero-shot LLM classifier.

### Add domain logic around classification

Override `IntentOrchestrator.execute_flow()`:

```python
class AcmeIntentOrchestrator(IntentOrchestrator):
    def execute_flow(self, payload):
        payload = self._enrich(payload)
        result  = super().execute_flow(payload)
        self._audit(result)
        return result

    def _clarification_message(self, intent, confidence, payload):
        return "Please choose: Report a Claim, Report Fraud, or Upload a Document."
```

---

## EIP Lineage

This pattern is a governed, extensible realisation of three Enterprise Integration Patterns (Hohpe & Woolf):

| EIP Pattern | K9-AIF realisation |
|---|---|
| **Content-Based Router** | `IntentOrchestrator` classifies and re-routes |
| **Message Channel** | `intent.in` / `responses.out` Kafka topics |
| **Pipes and Filters** | Router → `intent.in` → IntentOrchestrator → domain topic |

What K9-AIF adds: the classification strategy is pluggable via `BaseIntentAgent.classify()`, the topology is config-driven, and every step is governance-aware.

---

## OOB in k9-aif

Available from `pip install k9-aif>=1.2.0`

```python
from k9_aif_abb.k9_core.router.k9_event_router import K9EventRouter
from k9_aif_abb.k9_orchestrators.intent_orchestrator import IntentOrchestrator
from k9_aif_abb.k9_squad.intent_squad import IntentSquad
from k9_aif_abb.k9_agents.intent.k9_intent_agent import K9IntentAgent
from k9_aif_abb.k9_agents.intent.base_intent_agent import BaseIntentAgent
```

Working example with all three routing outcomes and SBB override demos:
`examples/k9routing/run.py` — runs without Kafka or a live LLM.
