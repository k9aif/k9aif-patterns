# Critic-Actor Pattern

## Intent

Enable an agent to produce a draft output, have it evaluated by a Critic, and refine it based on structured feedback — repeating until the Critic accepts the output, a round cap is hit, or an unresolvable condition triggers escalation.

The **Critic-Actor Pattern** (also known as the Self-Correction or Refinement pattern) gives agents a structured skeleton for problems where the answer must be *improved to meet a quality bar*, rather than merely validated as true or false.

## Motivation

Standard agents are one-shot: payload in, result out. This is correct for many tasks — routing, classification, audit, guard.

It breaks down the moment output quality must be evaluated and improved:

- A contract drafting agent that produces a clause without checking it against a compliance checklist may miss regulatory requirements
- A structured data extraction agent that outputs JSON without validating required fields will silently produce incomplete records
- A code generation agent that writes a function without running tests has no way to know if it works

Without a formal pattern, teams wire ad-hoc feedback loops — output sent back as input, uncapped retries, no structured critique history, no clean escalation when the loop cannot converge.

The **Critic-Actor Pattern** addresses this once, at the framework level.

## Architecture

```text
Agent.execute(payload)
        ↓
  [Round 1] generate()          ← Actor produces initial draft
        ↓
  critique(draft)               ← Critic evaluates: accepted?, score, issues
        ↓
  should_accept(feedback)
    ├── ACCEPTED  → finalize()
    ├── REJECTED  → refine(draft, feedback) → critique() → ...
    ├── ESCALATE  → route to human-in-the-loop
    └── FAIL      → definitive rejection
```

The loop alternates between Actor refinement and Critic evaluation until a terminal disposition is reached or `max_rounds` is hit.

## Responsibilities

**Agent (caller)**
- calls `execute(payload)` — receives a `dict` result
- has no knowledge of how many rounds ran internally

**CriticActorAgent**
- manages the round lifecycle, step history, telemetry, and cap enforcement
- delegates all domain logic to five abstract methods

**Five abstract methods (domain contract)**

| Method | Responsibility |
|---|---|
| `generate()` | Actor: produce the initial draft from the payload (called on round 1 only) |
| `critique()` | Critic: evaluate the draft; return structured feedback with `accepted`, `score`, `issues` |
| `refine()` | Actor: produce an improved draft using the Critic's feedback (round 2+) |
| `should_accept()` | Return disposition: ACCEPTED / REJECTED / ESCALATE / FAIL |
| `finalize()` | Produce the final accepted output |

**The Critic**
- may be an LLM with a critic system prompt, a test runner, a Pydantic schema validator, a compliance checker, or any callable that returns structured feedback
- returns `accepted` (bool), `score` (float 0–1), `issues` (list), `summary` (string)

## Key Characteristics

### Structured feedback drives refinement
The Critic does not just score — it returns specific issues. The Actor uses those issues in `refine()` to produce a targeted improvement, not a blind retry.

### Actor and Critic are separable
In the OOB implementation both roles are played by the LLM with role-switched prompts. In domain implementations the Critic can be replaced with any external evaluator — test runner, schema validator, compliance checker — without touching the Actor or the loop skeleton.

### Structured round history
Every round is recorded — draft, critique, disposition, score. The full history is available inside the loop and in the final output for audit trails, human review, and Neo4j lineage.

### Clean escalation path
If the Critic cannot be satisfied within the round cap, the agent either finalizes with best-effort output or escalates to human-in-the-loop — configurable per deployment. Critic exceptions are caught and converted to FAIL or ESCALATE.

### Invisible to the caller
From the Squad or Orchestrator perspective, a `CriticActorAgent` is indistinguishable from any other agent. The rounds are an internal implementation detail.

## Dispositions

| Disposition | Meaning |
|---|---|
| `ACCEPTED` | Critic is satisfied — produce final output |
| `REJECTED` | Issues found — Actor refines and retries |
| `ESCALATE` | Cannot converge — route to human-in-the-loop |
| `FAIL` | Definitively unacceptable — cannot be fixed |

## Config

```yaml
max_rounds:               3       # hard cap — loop never runs forever
acceptance_threshold:     0.8     # score threshold used in should_accept()
finalize_on_max_rounds:   true    # true → finalize with best effort; false → escalate
escalate_on_critic_error: false   # false → FAIL on critique() exception; true → ESCALATE
```

All keys are optional. Defaults are reasonable for most domains.

## When to use

Use the Critic-Actor Pattern when the agent's question is:

> *"Is this output good enough — and if not, what specifically should be fixed?"*

| Domain | Example |
|---|---|
| Contract drafting | Actor writes clause; Critic checks compliance checklist |
| Schema extraction | Actor extracts JSON; Critic validates required fields |
| Code generation | Actor writes function; Critic runs unit tests and returns error traces |
| Report improvement | Actor drafts; Critic scores quality and lists issues |
| Policy language | Actor writes; Critic checks regulatory alignment |
| RAG quality control | Actor drafts answer; Critic verifies claims against source documents |

## Benefits

- Eliminates ad-hoc feedback loops across solution teams
- Structured critique history enables audit trails and human review
- Critic is fully pluggable — swap LLM for test runner or schema validator with one override
- Critic errors are caught and converted to FAIL or ESCALATE — never crash the caller
- Telemetry hooks emit structured events at every stage
- Draft content is excluded from step output by default — sensitive content protection

## Tradeoffs

- Two LLM calls per round (Actor + Critic) — higher latency and cost than one-shot
- Requires a well-prompted Critic — a weak Critic becomes a rubber stamp or an infinite objector
- Round cap means some problems will escalate rather than converge autonomously

## Distinction from Validation Loop Pattern

| | Critic-Actor | Validation Loop |
|---|---|---|
| Question | *"Is this output good enough?"* | *"Is this hypothesis true?"* |
| Loop driver | Critic provides structured feedback to Actor | Agent tests hypothesis against an oracle |
| Typical tool | LLM, test runner, schema validator, compliance checker | Rule engine, database, sandbox, LLM |

## Related Patterns

- **Validation Loop Pattern** — complementary iterative pattern for confidence-driven hypothesis testing
- **Agent Squad Pattern** — the Squad calls `execute()` without knowing how many rounds ran
- **Model Router Pattern** — routes LLM calls inside `generate()`, `critique()`, and `refine()` to the appropriate model
- **External Connector Pattern** — connects the Critic to external validators (test runners, schema APIs, compliance services)
- **Factory Pattern** — constructs the CriticActorAgent with merged config at runtime

## Usage in K9-AIF

The Critic-Actor Pattern is implemented in K9-AIF as `BaseCriticActorAgent` (`k9_aif_abb/k9_agents/critic_actor/`). The OOB implementation `K9CriticActorAgent` uses the LLM for both Actor and Critic roles and requires no domain code for the common case. Domain teams extend it and override only `critique()` to plug in a real external evaluator.
