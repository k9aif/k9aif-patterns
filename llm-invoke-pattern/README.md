# LLM Invoke Chain Pattern

## Intent

Provide a single, governed entry point for all LLM inference in K9-AIF agent code.
`llm_invoke()` composes the Model Router, LLM Factory, and Inference Layer patterns
into one call — routing, model selection, invocation, and audit trail in a single function.

## Key principle

Agents never call `LLMFactory`, `ModelRouterFactory`, or `OllamaLLM` directly.
All governed LLM inference flows through `llm_invoke()`.

## Chain

```
Agent.execute()
  → llm_invoke(config, InferenceRequest)
    → ModelRouterFactory.get_router(config)
    → K9ModelRouter.route(request) → RouteDecision
    → LLMFactory.get(model_alias) → OllamaLLM
    → OllamaLLM.invoke(prompt) → raw response
    → RoutingStateStore.persist(decision)
    → InferenceResponse
```

## Related patterns

- Model Router Pattern
- Inference Layer Pattern
- Factory Pattern
- Provider Adapter Pattern
