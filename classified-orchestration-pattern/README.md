# Classified Orchestration Pattern

## Intent

A single Orchestrator coordinates two fundamentally different execution paths — agentic (Squad + Agents with LLM) and deterministic (Integration Adapters, no LLM) — selected at design time by the Solutions Architect and dispatched at runtime based on the event or payload type.

The **Classified Orchestration Pattern** establishes the decision boundary between AI-driven reasoning and deterministic system integration within a single orchestration unit.

## Motivation

Teams adopting agentic AI frequently make one of two mistakes:

- **Over-agentification** — routing every task through an LLM even when a workflow engine, rules engine, or message bus is the correct tool. This adds latency, cost, and non-determinism where none is needed.
- **Under-agentification** — avoiding LLM-based paths entirely and missing the reasoning capability needed for classification, extraction, or evidence correlation.

The Classified Orchestration Pattern resolves this by making the decision explicit and architectural. The Solutions Architect classifies each task at design time:

| Task requires... | Route to... |
|---|---|
| LLM reasoning, extraction, analysis | Agentic path (Squad + Agents) |
| Deterministic API call, rule evaluation | Integration Adapter (direct) |
| Event-driven chain across systems | Integration Adapter chain (Messaging → Workflow/Process) |

The Orchestrator enforces this topology. The boundary is not fuzzy — it is drawn in code.

## Architecture

### Two primary variants

**Variant A — Parallel Split**

The Orchestrator fires both an agentic path and a deterministic path for the same event, collecting and merging results:

```text
event
  ↓
ClassifiedOrchestrator
  ├── AGENTIC path  → Squad → Agent → Agent → LLM result
  └── ADAPTER path  → IntegrationAdapterFactory.create("api_adapter") → API result
  ↓
merge_results()
```

**Variant B — Event-Driven Chain**

The Orchestrator selects one path. The deterministic path uses a Messaging Adapter to trigger a downstream Workflow or Process Flow Adapter — enabling Kafka/SQS/RabbitMQ-driven orchestration without involving the LLM:

```text
event
  ↓
ClassifiedOrchestrator
  └── ADAPTER_CHAIN  → MessagingAdapter.publish(topic, payload)
                            ↓
                       WorkflowAdapter.trigger(workflow_id, params)
                            ↓
                       workflow result
```

**Direct adapter path** (no messaging layer):

```text
event
  ↓
ClassifiedOrchestrator
  └── ADAPTER_DIRECT → WorkflowAdapter.trigger(workflow_id, params)
```

### Classification is a design-time decision

The Orchestrator does not call the LLM to decide which path to take. Classification is declared by the SA via:

- Event type — `event_type: "claim_submitted"` → agentic, `event_type: "payment_approved"` → adapter
- Payload shape — presence of `document_uri` → agentic extraction, presence of `workflow_id` → adapter
- Configuration — routing table in `config.yaml`

This makes the topology deterministic and inspectable — no hidden LLM routing cost, no non-deterministic path selection at runtime.

### Classification Gate

```text
BPMN task type / event_type / payload shape
        ↓
  Classification Gate (design-time)
        ├── GREEN zone  (deterministic) → Integration Adapter path
        │     ├── ServiceTask / API call   → api_adapter
        │     ├── BusinessRuleTask         → rules_adapter
        │     ├── SendTask / ReceiveTask   → messaging_adapter → workflow_adapter or process_adapter
        │     ├── ScriptTask / flow step   → workflow_adapter
        │     ├── BPM process instance     → bpm_adapter
        │     └── Data read / write        → data_adapter
        └── AMBER/RED zone (uncertain / reasoning-required) → Agentic path (Squad + LLM)
```

## Responsibilities

**ClassifiedOrchestrator**
- Evaluates `PathDecision` from payload/event to select the path
- Executes agentic path via `execute_squads()`
- Executes deterministic path via `IntegrationAdapterFactory.create(adapter_type, config).execute(payload)`
- Merges results when both paths run in parallel
- Never passes path selection to an LLM at runtime

**BaseSquad / Agents**
- LLM-driven — agents enrich shared context progressively through the flow
- Appropriate for: reasoning, extraction, analysis, iterative validation

**BaseIntegrationAdapter subtypes**
- No LLM, no inference cost
- Template Method pattern: each concrete ABB defines one domain-specific abstract method
- Appropriate for: API calls, rule evaluation, event publishing, workflow triggering, BPM, data access

**IntegrationAdapterFactory**
- Registry + factory for adapter SBBs
- SBBs register themselves; factory resolves by adapter_type string
- Same static-factory pattern as `CacheFactory`, `ObjectStorageFactory`

## Integration Adapter Types

| Adapter ABB | Deterministic task | Domain abstract method |
|---|---|---|
| `BaseApiAdapter` | REST / GraphQL / webhook | `call_endpoint(url, method, headers, body)` |
| `BaseMessagingAdapter` | Kafka / RabbitMQ / SQS / SNS | `publish(topic, message)` |
| `BaseRulesAdapter` | Business rules / policy engine | `evaluate(ruleset, facts)` |
| `BaseWorkflowAdapter` | DAG / Airflow / Step Functions | `trigger(workflow_id, params)` |
| `BaseProcessFlowAdapter` | MuleSoft / TIBCO / AppConnect | `invoke(flow_id, payload)` |
| `BaseBpmAdapter` | Camunda / Appian / Pega | `start_process(process_key, variables)` |
| `BaseDataAdapter` | SQL / NoSQL / object store | `read(query, params)` |

## Key Characteristics

### Classification boundary is explicit and permanent
Once the SA classifies a task as agentic or deterministic, it stays classified. Runtime conditions may select between sub-variants, but the SA never leaves both options open for the LLM to decide.

### Topology is enforceable on K9X Studio canvas
K9X Studio enforces valid connections by component type:
- **Orchestrator → Squad** (agentic path)
- **Orchestrator → Messaging Adapter → Workflow Adapter or Process Flow Adapter** (event chain)
- **Orchestrator → Workflow Adapter** (direct)
- Messaging Adapter is not a leaf — it chains downstream

### Adapters are SBBs registered against ABBs
Teams implement `call_endpoint()`, `publish()`, `evaluate()`, etc. The Orchestrator never knows which vendor is behind the adapter — only the abstract contract.

### Parallel split merges cost-efficiently
Running an LLM squad and an API adapter in parallel is acceptable — the adapter returns quickly, the LLM result follows. Governance and audit trail apply to both paths.

## When to use

| Scenario | Pattern applies? |
|---|---|
| Same workflow requires both LLM extraction AND rules engine evaluation | Yes — parallel split |
| Event fan-out: Kafka message triggers BPM process downstream | Yes — event chain |
| Orchestrator calls a REST API, no reasoning needed | Yes — ADAPTER_DIRECT |
| All processing is agentic (Squad of agents) | No — Agent Squad Pattern suffices |
| All processing is deterministic (pipeline with no LLM) | No — adapters without the Classified Orchestration wrapper |

## Benefits

- Eliminates accidental LLM calls for deterministic tasks
- Reduces latency and inference cost by routing non-reasoning tasks to adapters
- Makes the agentic/deterministic boundary visible in code and on the canvas
- Integration Adapters are unit-testable without LLM, network, or Kafka
- Topology is enforceable — K9X Studio prevents invalid connections
- Governance applies at the Orchestrator level regardless of which path runs

## Tradeoffs

- Requires the SA to classify tasks at design time (not always obvious at project start)
- Parallel split adds orchestration complexity — result merge logic must handle partial failures
- Event-driven chains (Messaging → Workflow) introduce asynchrony — the Orchestrator may not receive the final result synchronously

## Related Patterns

- **Agent Squad Pattern** — the agentic path within this pattern
- **Event Router Pattern** — selects which Orchestrator to invoke; Classified Orchestration operates inside the Orchestrator
- **Provider Adapter Pattern** — each Integration Adapter SBB follows the same ABB/SBB/Factory structure
- **Factory Pattern** — `IntegrationAdapterFactory` follows the same static-registry pattern as `AgentRegistry`, `LLMFactory`
- **Validation Loop Pattern** — used inside agentic agents when iterative convergence is needed

## Usage in K9-AIF

Integration Adapter ABBs are in `k9_aif_abb/k9_adapters/integration/`. Factory is `IntegrationAdapterFactory`. The pattern is modelled and enforced on K9X Studio canvas — drop an Orchestrator, Squad, and adapter side by side; the canvas enforces valid connection topology.

SBBs register themselves:

```python
from k9_aif_abb.k9_adapters.integration import IntegrationAdapterFactory
from my_app.adapters import MyKafkaAdapter

IntegrationAdapterFactory.register("my_kafka", MyKafkaAdapter)
adapter = IntegrationAdapterFactory.create("my_kafka", config={"topic": "payments.out"})
result = adapter.execute(payload)
```
