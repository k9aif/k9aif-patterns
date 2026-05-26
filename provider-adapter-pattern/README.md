# Provider Adapter Pattern

This pattern describes an architectural approach for supporting multiple LLM providers — or any pluggable backend — without coupling the factory, agents, or orchestration logic to any specific vendor.

The design applies the ABB/SBB separation used throughout K9-AIF: the framework provides a stable contract and registry mechanism, and concrete provider implementations are registered as extensions without modifying the framework.

---

## Pattern Intent

Define a stable adapter contract for provider-specific construction so that:

- new providers can be added by extending one class and registering it
- the factory remains provider-agnostic — it resolves and delegates, never constructs directly
- agents, squads, orchestrators, and the model router require no changes when the provider changes
- API keys and infrastructure details never appear in framework code

---

## Context and Forces

Agentic systems must support multiple LLM providers: local models for development, cloud APIs for production, enterprise platforms for regulated environments. Provider requirements change as the AI industry evolves.

Forces in tension:

- **Extensibility** — new providers must be addable without modifying shared infrastructure
- **Stability** — existing agents and orchestration logic must not be affected by provider changes
- **Security** — API keys and secrets must not be hardcoded in config or framework code
- **Simplicity** — switching provider should require only a config change, not a code change

---

## Structure

```
LLMFactory
  → ProviderAdapterRegistry    (resolves adapter by backend name)
  → BaseProviderAdapter        (ABB — abstract contract)
  → Concrete ProviderAdapter   (SBB — one per provider)
  → BaseLLM
```

### Architecture Diagram

![Provider Adapter Class Diagram](k9-aif-inteference-llm-provider-class-diagram.png)

---

## Architectural Components

### Architecture Building Blocks (ABB)

**`BaseLLM`**
Abstract inference contract. Defines `generate(prompt: str) -> str`. All provider-specific LLM classes extend this.

**`BaseProviderAdapter`**
Abstract adapter contract. Two methods:
- `provider_name: str` — registry key, enforced as abstract property by ABC
- `create_llm(model_name, factory_cfg, extra_kwargs) -> BaseLLM` — constructs and returns the LLM instance

**`ProviderAdapterRegistry`**
Central registry mapping backend names to adapter classes. Bootstraps OOB defaults lazily. Exposes `register(name, adapter_cls)` for custom extensions — no framework modification required.

**`LLMFactory`**
Provider-agnostic factory. Reads `backend:` from config, resolves the adapter from the registry, calls `create_llm()`. Caches instances by alias.

---

### Solution Building Blocks (SBB)

**`OllamaProviderAdapter`** — creates `OllamaLLM` from `base_url` and model config. Default local backend.

**`OpenAIProviderAdapter`** — creates `OpenAILLM` for any OpenAI-compatible endpoint. Covers OpenAI API and Grok/xAI via `base_url`. Resolves API key from environment variable (`api_key_env:`) — never from raw config values.

**Custom adapters** — any team can extend `BaseProviderAdapter`, implement two methods, and register with `ProviderAdapterRegistry.register()`. The factory uses it immediately.

---

## Runtime Polymorphism

The factory dispatch is three lines:

```python
backend = (fcfg.get("backend") or fcfg.get("provider") or "ollama").lower()
adapter  = ProviderAdapterRegistry.resolve(backend)
inst     = adapter.create_llm(model_name, fcfg, extra_kwargs)
```

The client — agents, squads, orchestrators — interacts only with the stable `llm_invoke` interface:

```python
resp = llm_invoke(self.config, InferenceRequest(prompt=..., task_type=...))
```

The provider in use is determined entirely by config. No agent code changes when the backend changes.

---

## Extending with a New Provider

```python
from k9_aif_abb.k9_core.inference.base_provider_adapter import BaseProviderAdapter
from k9_aif_abb.k9_core.inference.provider_registry import ProviderAdapterRegistry


class WatsonxProviderAdapter(BaseProviderAdapter):

    @property
    def provider_name(self) -> str:
        return "watsonx"

    def create_llm(self, model_name, factory_cfg, extra_kwargs) -> BaseLLM:
        api_key = os.environ.get(factory_cfg.get("api_key_env", "WATSONX_API_KEY"), "")
        return WatsonxLLM(api_key=api_key, model=model_name, **extra_kwargs)


ProviderAdapterRegistry.register("watsonx", WatsonxProviderAdapter)
```

Then in `config.yaml`:

```yaml
inference:
  llm_factory:
    backend: watsonx
    api_key_env: WATSONX_API_KEY
    models:
      general:
        model: "ibm/granite-3-8b-instruct"
```

`LLMFactory`, agents, squads, orchestrators, and the model router are unchanged.

---

## Configuration-Driven Provider Selection

| Provider | `backend` | Key config |
|---|---|---|
| Ollama (local) | `ollama` | `base_url` |
| OpenAI | `openai` | `api_key_env: OPENAI_API_KEY` |
| Grok / xAI | `openai-compatible` | `base_url`, `api_key_env: GROK_API_KEY` |
| Any OAI-compatible | `openai-compatible` | `base_url`, `api_key_env` |
| Custom SBB | your key | `register()` + `backend:` in config |

---

## Design Principles

- **ABB defines the contract** — `BaseProviderAdapter` and `ProviderAdapterRegistry` are framework-level ABBs. They are stable and never modified when new providers are added.
- **SBB provides the realization** — each provider adapter is an SBB. It lives outside the core framework and can be contributed independently.
- **Nothing is hardwired** — no provider name, no API key pattern, no SDK import appears in `LLMFactory`. The factory is decoupled from every concrete provider.
- **Secrets stay in the environment** — `api_key_env:` resolves keys from environment variables at runtime. Config files are safe to commit.

---

## Reference Implementation

Provider adapters are implemented in the K9-AIF Framework:

- `k9_aif_abb/k9_core/inference/base_provider_adapter.py`
- `k9_aif_abb/k9_core/inference/provider_registry.py`
- `k9_aif_abb/k9_core/inference/ollama_provider_adapter.py`
- `k9_aif_abb/k9_core/inference/openai_provider_adapter.py`
- `k9_aif_abb/k9_factories/llm_factory.py`

➡️ [github.com/k9aif/k9-aif-framework](https://github.com/k9aif/k9-aif-framework)
