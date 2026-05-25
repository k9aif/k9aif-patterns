# Validation Loop Pattern

## Intent

Enable an agent to iteratively test a hypothesis, observe the result, and decide whether to continue — repeating until confidence is sufficient, a definitive result is reached, or the iteration cap is hit.

The **Validation Loop Pattern** gives agents a structured skeleton for problems that cannot be answered in a single pass, where the answer must be *earned through iteration*.

## Motivation

Standard agents are one-shot: payload in, result out. This is correct for deterministic tasks — classification, formatting, extraction with a clear schema.

It breaks down the moment the answer is uncertain and must be tested:

- A fraud detection agent that calls the LLM once and reports is less reliable than one that correlates signals across multiple passes and converges on a risk score
- A claims adjudication agent that returns 60% confidence has nowhere to put that uncertainty without a loop structure
- A compliance gap agent that finds one clause gap cannot know whether additional gaps exist without re-querying with a refined hypothesis

Without a formal pattern, teams reinvent ad-hoc while loops with uncapped retries, no structured step history, and no clean escalation path.

The **Validation Loop Pattern** addresses this once, at the framework level.

## Architecture

```text
Agent.execute(payload)
        ↓
  Generate Hypothesis
        ↓
  Run Validation (tool / rule engine / LLM / database)
        ↓
  Evaluate Observation  →  confidence score
        ↓
  Decide
    ├── CONTINUE   → next iteration
    ├── FINALIZE   → produce validated output
    ├── ESCALATE   → route to human-in-the-loop
    └── FAIL       → definitive negative result
```

The loop runs until a terminal disposition is reached or `max_iterations` is hit.

## Responsibilities

**Agent (caller)**
- calls `execute(payload)` — receives a `dict` result
- has no knowledge of how many iterations ran internally

**ValidationLoopAgent**
- manages the iteration lifecycle, step history, telemetry, and cap enforcement
- delegates all domain logic to five abstract methods

**Five abstract methods (domain contract)**

| Method | Responsibility |
|---|---|
| `generate_hypothesis()` | Form the next thing to test, informed by prior iterations |
| `run_validation()` | Invoke the tool, rule engine, database, or LLM |
| `evaluate_observation()` | Interpret raw result into structured observation with confidence score |
| `should_continue()` | Return disposition: CONTINUE / FINALIZE / ESCALATE / FAIL |
| `finalize()` | Produce the validated output when confidence is sufficient |

**Validation tool**
- may be a rule engine, database query, sandbox, LLM, or any callable
- returns raw results — interpretation is handled by `evaluate_observation()`

## Key Characteristics

### Confidence-driven termination
The loop continues only while confidence is below a configurable threshold. Once the threshold is reached, the loop finalizes with a confidence-backed result.

### Structured step history
Every iteration is recorded as an immutable step — hypothesis, observation, disposition, confidence. The full history is available inside the loop (to inform the next hypothesis) and in the final output for audit trails and human review.

### Pluggable validation tool
The validation tool is a domain concern — the loop skeleton is independent of it. The same ABB drives a fraud rule engine, a policy database, an LLM, and a sandbox without modification.

### Clean escalation path
If confidence cannot be achieved within the iteration cap, the agent either finalizes with best-effort output or escalates to human-in-the-loop — configurable per deployment. No uncaught exceptions reach the caller.

### Invisible to the caller
From the Squad or Orchestrator perspective, a `ValidationLoopAgent` is indistinguishable from any other agent. The loop is an internal implementation detail.

## Dispositions

| Disposition | Meaning |
|---|---|
| `CONTINUE` | Confidence insufficient — run another iteration |
| `FINALIZE` | Confidence sufficient — produce validated output |
| `ESCALATE` | Unresolvable uncertainty — route to human-in-the-loop |
| `FAIL` | Definitive negative result |

## Config

```yaml
max_iterations:             5       # hard cap — loop never runs forever
confidence_threshold:       0.8     # available to should_continue()
finalize_on_max_iterations: true    # true → finalize with best effort; false → escalate
escalate_on_tool_error:     false   # false → FAIL on tool exception; true → ESCALATE
```

All keys are optional. Defaults are reasonable for most domains.

## When to use

Use the Validation Loop Pattern when the agent's question is:

> *"Is this hypothesis true — and am I confident enough to act on it?"*

| Domain | Example |
|---|---|
| Fraud detection | Correlate signals until risk confidence is sufficient |
| Claims adjudication | Check policy coverage until adjudication confidence is sufficient |
| Security | Attempt exploit in sandbox until confirmed or ruled out |
| Compliance | Match regulations until gap coverage is sufficient |
| Document extraction | Re-extract until required fields are present with confidence |
| Diagnostics | Query symptoms until differential is narrowed |

## Benefits

- Eliminates ad-hoc while loops across solution teams
- Structured step history enables audit trails and Neo4j lineage
- Confidence clamping and safe config parsing prevent subtle bugs
- Sensitive tool output is excluded from the result by default
- Telemetry hooks emit structured events at every stage
- Tool errors are caught and converted to FAIL or ESCALATE — never crash the caller

## Tradeoffs

- Multiple LLM or tool calls per agent execution — higher latency and cost than one-shot
- Requires domain knowledge to set meaningful confidence thresholds
- Cap enforcement means some problems will escalate rather than resolve autonomously

## Distinction from Critic-Actor Pattern

| | Validation Loop | Critic-Actor |
|---|---|---|
| Question | *"Is this hypothesis true?"* | *"Is this output good enough?"* |
| Loop driver | Agent tests hypothesis against an oracle | Critic gives structured feedback to Actor |
| Typical tool | Rule engine, database, sandbox, LLM | LLM, test runner, schema validator, compliance checker |

## Related Patterns

- **Critic-Actor Pattern** — complementary iterative pattern for quality-driven output refinement
- **Agent Squad Pattern** — the Squad calls `execute()` without knowing how many iterations ran
- **Model Router Pattern** — routes LLM calls inside `run_validation()` to the appropriate model
- **Factory Pattern** — constructs the ValidationLoopAgent with merged config at runtime

## Usage in K9-AIF

The Validation Loop Pattern is implemented in K9-AIF as `BaseValidationLoopAgent` (`k9_aif_abb/k9_agents/validation/`). The OOB implementation `K9ValidationLoopAgent` uses the LLM as the validation tool and requires no domain code for the common case. Domain teams extend it and override only the method(s) that differ.

EOC reference implementations: `FraudDetectionAgent`, `DocumentExtractorAgent`.
