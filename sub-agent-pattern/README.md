# Sub-Agent Pattern (K9AgentSpawner + ChildAgent)

## Intent

Enable a parent agent to spawn lightweight **ChildAgents** that execute concurrently and independently, then merge their results — applying the multithreading model to enterprise agentic AI.

---

## Motivation

The K9-AIF Squad executes agents sequentially — each agent enriches shared context and passes it to the next. This is the right model for dependent steps.

But many workflows contain **independent work units** that do not need to wait on each other: generating 20 scaffold files, extracting independent data slices from a document, validating a transaction across multiple systems simultaneously.

Sequential execution in these cases is pure waste. The Sub-Agent Pattern solves this.

---

## How It Fits in the Hierarchy

```
K9EventRouter → Orchestrator → Squad → K9AgentSpawner (parent)
                                              ├── ChildAgent (parallel)
                                              ├── ChildAgent (parallel)
                                              └── ChildAgent (parallel)
                                                     ↓
                                              merge_results()
```

`K9AgentSpawner` sits in the Squad's flow like any other agent. The Squad calls `execute()` and receives a merged result. The spawning is entirely encapsulated inside the agent.

---

## Structure

```
BaseAgent
├── ChildAgent            ← leaf node, cannot spawn (NEW)
└── K9AgentSpawner        ← spawns ChildAgents (NEW)
      └── K9TransactionAgent  ← 2-Phase Commit variant (NEW)
```

### K9AgentSpawner
The parent agent. Dynamically spawns ChildAgents at runtime and merges their results.

**Three execution modes:**
- `spawn_parallel(children, payloads, timeout)` — all children simultaneously, parent joins
- `spawn_sequential(children, payload)` — children in order, each enriches shared context
- Tree — spawner spawns spawners, bounded to depth 2

### ChildAgent
A `BaseAgent` that cannot spawn. Enforced at design time:
```python
class ChildAgent(BaseAgent):
    def spawn(self, *args, **kwargs):
        raise NotImplementedError("ChildAgents are leaf nodes.")
```

### K9TransactionAgent
Extends `K9AgentSpawner` with 2-Phase Commit — for scenarios requiring all-or-nothing execution:
- **Phase 1 — PREPARE:** each child votes YES or NO
- **Phase 2 — COMMIT** if all YES, **ROLLBACK** if any NO

---

## Guarantees

**No Orphan Children**
`ChildRegistry` + `try/finally` ensures all children are cancelled if parent fails.

**No Deadlocks — 4 Structural Rules**

| Rule | What it prevents |
|---|---|
| Leaf Node Rule — ChildAgent.spawn() raises NotImplementedError | Circular spawning |
| Mandatory Timeout — no indefinite waits | Indefinite blocking |
| No Shared Mutable State — payloads deep-copied | Resource contention |
| Bounded Concurrency — max 20 children, dedicated pool | Thread exhaustion |

**Governance Inheritance**
Children execute within parent's governance boundary.

**Result Policy — SBB Decides**
Override `merge_results()` to define behaviour on partial failure.

---

## K9Newfoundland

The monitoring companion to `K9AgentSpawner`. Combines `K9HeartBeat` and `K9Remediation` — monitors every spawned ChildAgent, detects silence, raises alerts, and remediates failures.

> *"Never leaves a child behind."*

---

## Use Cases

- **Scaffold generation** — one ChildAgent per file, all parallel
- **Spec document analysis** — parallel extraction of independent data slices
- **Multi-system validation** — concurrent fraud, balance, and compliance checks
- **Claims processing** — parallel FNOL intake, policy verification, document retrieval
- **Reporting** — simultaneous generation of independent analytics

---

## When to Use

Use `K9AgentSpawner` when:
- Work units are **independent** — no output-to-input dependency
- Latency matters — parallel is significantly faster than sequential
- You need structural safety — lifecycle, deadlock, governance guarantees

Use plain `BaseAgent` or `K9ValidationLoopAgent` when:
- Steps are **dependent** — each step needs the previous result
- Iterative convergence is needed

---

## Related Patterns

- [Agent Squad Pattern](../agent-squad-pattern) — sequential agent execution
- [Validation Loop Pattern](../validation-loop-pattern) — iterative convergence
- [Critic-Actor Pattern](../critic-actor-pattern) — generate-critique-refine

## Further Reading

- [Blog: Applying the Multithreading Pattern to Agentic AI](https://blog.k9x.ai/k9-aif-sub-agent-pattern/)
- Butenhof, D.R. — *Programming with POSIX Threads* (1997)
