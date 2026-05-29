"""Generate individual pattern pages for patterns.k9x.ai"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

NAV_LINKS = """
    <a href="https://k9x.ai">Home</a>
    <a href="https://pydocs.k9x.ai/starthere/">Docs</a>
    <a href="https://blog.k9x.ai">Blog</a>
    <a href="https://graph.k9x.ai" target="_blank" rel="noopener">Graph Explorer</a>
    <a href="https://github.com/k9aif/k9aif-patterns" target="_blank" rel="noopener">GitHub</a>
"""

PATTERNS = [
    {"id": "agent-squad-pattern",           "cat": "Execution",              "cat_slug": "execution"},
    {"id": "validation-loop-pattern",        "cat": "Execution",              "cat_slug": "execution"},
    {"id": "critic-actor-pattern",           "cat": "Execution",              "cat_slug": "execution"},
    {"id": "model-router-pattern",           "cat": "Inference",              "cat_slug": "inference"},
    {"id": "inference-pattern",              "cat": "Inference",              "cat_slug": "inference"},
    {"id": "provider-adapter-pattern",       "cat": "Inference · Integration","cat_slug": "inference"},
    {"id": "factory-pattern",               "cat": "Governance",             "cat_slug": "governance"},
    {"id": "runtime-agent-loader-pattern",  "cat": "Governance",             "cat_slug": "governance"},
    {"id": "external-connector-pattern",    "cat": "Integration",            "cat_slug": "integration"},
]

PATTERN_DATA = {
    "agent-squad-pattern": {
        "title": "Agent Squad Pattern",
        "intent": "Organize multiple agents into a coordinated execution unit called a Squad, enabling structured collaboration, shared context, governance enforcement, and scalable orchestration.",
        "image": None,
        "motivation": """Multi-agent systems fail when agents operate in isolation without shared state or governance. As systems grow, informal coordination collapses — agents produce incompatible outputs, governance becomes inconsistent, and debugging is impossible.

The Squad pattern introduces a formal coordination layer between orchestrators and individual agents. A Squad defines a sequential execution flow, maintains a shared context that grows progressively richer as each agent contributes, and enforces governance at the squad boundary.""",
        "structure": [
            "Orchestrator loads and invokes a Squad by ID",
            "Squad defines a sequential flow of named agents",
            "Each agent executes and writes its result to a named key in the shared context",
            "The next agent receives the enriched context as input",
            "Governance is enforced before and after each step",
        ],
        "key_concepts": ["BaseSquad", "SquadLoader", "flow steps", "result_key", "context enrichment", "AgentRegistry"],
        "used_in": ["BaseSquad", "SquadLoader", "EOC — ClaimsProcessingSquad", "EOC — FraudDetectionSquad", "EOC — ComplianceSquad", "DoW — 6 DoDAF stage squads"],
        "github": "agent-squad-pattern",
    },
    "validation-loop-pattern": {
        "title": "Validation Loop Pattern",
        "intent": "Enable an agent to iteratively test a hypothesis, observe the result, and decide whether to continue — repeating until confidence is sufficient, a definitive result is reached, or the iteration cap is hit.",
        "image": "validation-loop-pattern/k9x-framework-validation-loop-pattern.png",
        "motivation": """Some problems cannot be solved in a single pass. Fraud signal correlation, compliance gap analysis, and document confidence scoring all require iterative convergence — the agent must test something, observe the outcome, and decide whether to try again.

Standard one-shot agents cannot model this. The Validation Loop Pattern gives agents a structured skeleton for problems where the answer must be earned through iteration rather than computed in a single step.""",
        "structure": [
            "generate_hypothesis() — form the next thing to test based on prior steps",
            "run_validation() — invoke a tool, rule engine, LLM, or external system",
            "evaluate_observation() — interpret the raw result and return a confidence dict",
            "should_continue() — return CONTINUE, FINALIZE, ESCALATE, or FAIL",
            "Record the step and repeat, or terminate",
            "finalize() / escalate() / fail() — produce the final output",
        ],
        "key_concepts": ["BaseValidationLoopAgent", "K9ValidationLoopAgent", "ValidationLoopContext", "ValidationDisposition", "confidence_threshold", "max_iterations"],
        "used_in": ["BaseValidationLoopAgent", "K9ValidationLoopAgent", "FraudDetectionAgent (EOC)", "DocumentExtractorAgent (EOC)"],
        "github": "validation-loop-pattern",
    },
    "critic-actor-pattern": {
        "title": "Critic-Actor Pattern",
        "intent": "An Actor produces a draft output; a Critic evaluates it and provides structured feedback; the Actor refines — repeating until the Critic accepts the output or a round cap triggers escalation.",
        "image": None,
        "motivation": """Many agent tasks require quality refinement, not just validation. Contract drafting, report writing, policy review, and code generation benefit from structured critique cycles rather than single-pass generation.

The Critic-Actor Pattern separates generation from evaluation, creating a feedback loop that converges on acceptable quality. Unlike the Validation Loop (which tests correctness), the Critic-Actor pattern improves quality through structured critique.""",
        "structure": [
            "generate() — Actor produces the first draft",
            "critique() — Critic evaluates the draft and returns structured feedback",
            "refine() — Actor revises the draft based on the critique",
            "should_accept() — Critic decides whether the refined output is acceptable",
            "Repeat or finalize / escalate",
        ],
        "key_concepts": ["BaseCriticActorAgent", "K9CriticActorAgent", "generate()", "critique()", "refine()", "should_accept()", "finalize()"],
        "used_in": ["BaseCriticActorAgent", "K9CriticActorAgent", "contract drafting agents", "report writing agents", "policy review agents"],
        "github": "critic-actor-pattern",
    },
    "model-router-pattern": {
        "title": "Model Router Pattern",
        "intent": "Dynamically select the most appropriate model for a given task based on task type, complexity, cost, latency, and policy constraints — fully decoupled from agent code.",
        "image": None,
        "motivation": """Agents that hardcode model choices cannot adapt to cost constraints, latency requirements, or governance policies. As model providers and capabilities evolve, every agent would require modification.

The Model Router Pattern introduces a routing layer between agents and model providers. Routing decisions are governed, scored, persisted, and auditable. Agents simply declare what they need — the router decides which model serves that need.""",
        "structure": [
            "Agent calls llm_invoke(config, InferenceRequest)",
            "InferenceRequest carries: prompt, task_type, sensitivity, latency_budget, cost_profile",
            "ModelRouter scores all catalog models against the request signals",
            "Best-scoring model is selected",
            "Routing decision (model, scores, latency) persisted to state store",
            "LLM response returned to agent",
        ],
        "key_concepts": ["BaseModelRouter", "K9ModelRouter", "InferenceRequest", "RouteDecision", "routing state store", "weighted scoring: +3 task_type, +2 sensitivity, +2 latency, +2 cost"],
        "used_in": ["BaseModelRouter", "K9ModelRouter", "ModelRouterFactory", "llm_invoke()", "routing_state_store (SQLite / PostgreSQL)", "all K9-AIF agents"],
        "github": "model-router-pattern",
    },
    "inference-pattern": {
        "title": "Inference Layer Pattern",
        "intent": "Build a provider-independent inference layer by separating ABB contracts from SBB implementations — swap Ollama, IBM Watsonx, or OpenAI via config with no code changes.",
        "image": "inference-pattern/inference_layer_small.png",
        "motivation": """Agents that import LLM clients directly become provider-locked. Switching from Ollama to Watsonx requires modifying every agent. The inference layer pattern ensures the framework controls which provider is used, not the agent.

ABB contracts define what the inference layer must provide. SBB implementations deliver it for each provider. The factory resolves the right implementation from config at runtime.""",
        "structure": [
            "BaseLLM ABB defines the inference contract",
            "OllamaLLM, WatsonxLLM, MockLLM are SBB implementations",
            "ProviderAdapterRegistry maps provider name to adapter class",
            "LLMFactory.bootstrap(config) initialises the correct provider",
            "LLMFactory.get(alias) returns a cached instance",
            "Agents call llm_invoke() — never touch LLMFactory directly",
        ],
        "key_concepts": ["BaseLLM", "LLMFactory", "OllamaLLM", "InferenceRequest", "InferenceResponse", "ProviderAdapterRegistry", "MockLLM"],
        "used_in": ["LLMFactory", "OllamaLLM", "InferenceRequest", "InferenceResponse", "ProviderAdapterRegistry", "MockLLM (testing)"],
        "github": "inference-pattern",
    },
    "provider-adapter-pattern": {
        "title": "Provider Adapter Pattern",
        "intent": "Support multiple pluggable backends — LLM providers, secret managers, caches, LLM bridges — without coupling factories or agents to any specific vendor. ABB contract + SBB adapters + Factory.",
        "image": "provider-adapter-pattern/k9-aif-inteference-llm-provider-class-diagram.png",
        "motivation": """Enterprise systems must change providers without code changes. Secret management moves from env vars to Vault. Caching moves from in-memory to Redis. LLM providers change. None of these should require touching agent or orchestrator code.

The Provider Adapter Pattern applies ABB/SBB separation to every infrastructure concern: define a stable contract, register concrete implementations, let a factory select the right one from config.""",
        "structure": [
            "BaseXxx ABB defines the contract (e.g. BaseSecretManager, BaseCache)",
            "XxxAdapter SBBs implement the contract for each provider",
            "XxxFactory._registry maps provider name to adapter class",
            "XxxFactory.create(config) reads config key, returns correct adapter",
            "Zero-config default — always works without explicit config",
            "Credentials NEVER in config.yaml — always from environment",
        ],
        "key_concepts": ["BaseSecretManager", "BaseCache", "EnvSecretAdapter", "VaultSecretAdapter", "InMemoryAdapter", "RedisAdapter", "SecretManagerFactory", "CacheFactory", "K9XLiteLLMBridgeAdapter"],
        "used_in": ["SecretManagerFactory", "CacheFactory", "EnvSecretAdapter", "VaultSecretAdapter", "AwsSecretAdapter", "IbmSecretAdapter", "InMemoryAdapter", "RedisAdapter", "K9XLiteLLMBridgeAdapter"],
        "github": "provider-adapter-pattern",
    },
    "factory-pattern": {
        "title": "Factory Pattern",
        "intent": "Centralise component instantiation through static factories. Never instantiate agents, routers, orchestrators, or LLMs directly in application code.",
        "image": "factory-pattern/factory_class_diagram.png",
        "motivation": """Direct instantiation scatters construction logic, prevents governance, and couples application code to concrete implementations. When construction requires config, caching, thread-safety, and lifecycle management, doing it inline becomes unmanageable.

K9-AIF factories are static — they cannot be instantiated. They maintain a thread-safe registry and return cached instances. All major components are provisioned exclusively through factories.""",
        "structure": [
            "Static factory class with _registry: Dict[str, Type]",
            "bootstrap(config) — initialises the factory once per runtime",
            "register(name, cls) — adds a class to the registry",
            "get(name) — returns a cached instance, raises if unknown",
            "create(config) — config-driven selection, zero-config default",
            "Thread-safe via threading.Lock",
        ],
        "key_concepts": ["AgentRegistry", "OrchestratorRegistry", "RouterFactory", "LLMFactory", "ModelRouterFactory", "SecretManagerFactory", "CacheFactory", "singleton caching", "bootstrap pattern"],
        "used_in": ["AgentRegistry", "OrchestratorRegistry", "RouterFactory", "LLMFactory", "ModelRouterFactory", "SecretManagerFactory", "CacheFactory", "PersistenceFactory"],
        "github": "factory-pattern",
    },
    "runtime-agent-loader-pattern": {
        "title": "Runtime Agent Loader Pattern",
        "intent": "Load and wire agents, squads, and orchestrators from declarative YAML configuration at runtime — change orchestration structure without changing or redeploying application code.",
        "image": "runtime-agent-loader-pattern/loader.png",
        "motivation": """Hardcoded orchestration logic cannot be modified without deployment. Adding an agent to a squad, changing the execution flow, or swapping an orchestrator should not require code changes.

Configuration-driven loading separates what the system does from how it is assembled. The YAML is the architecture definition. The loader wires it at startup.""",
        "structure": [
            "squads.yaml defines: squad ID, agents list, flow steps with result_key",
            "AgentRegistry.register(name, factory_fn) maps name to construction lambda",
            "SquadLoader.load_one(yaml_path, squad_id) reads YAML, resolves agents from registry",
            "AgentLoader.merge_with_global(agent_name, config) merges agent YAML with global config",
            "Orchestrator calls _load_squad() — never references agent classes directly",
        ],
        "key_concepts": ["SquadLoader", "AgentLoader", "AgentRegistry", "squads.yaml", "flow steps", "result_key", "merge_with_global()", "_load_squad()"],
        "used_in": ["SquadLoader", "AgentLoader", "_load_squad()", "k9_generator.sh", "all EOC squads", "all DoW squads", "k9-aif-intake"],
        "github": "runtime-agent-loader-pattern",
    },
    "external-connector-pattern": {
        "title": "External Connector Pattern",
        "intent": "Access external systems through a standardised connector layer with governance enforced at the integration boundary — APIs, databases, MCP tool servers, messaging systems.",
        "image": "external-connector-pattern/governed-connector-pattern.png",
        "motivation": """Agents that call external systems directly bypass governance, create hidden dependencies, and cannot be tested in isolation. Every external call is a governance boundary — it must be verified, logged, and policy-checked before execution.

The connector layer enforces policy at the boundary, abstracts the protocol, and makes external dependencies explicit and testable.""",
        "structure": [
            "BaseMCPAgent provides the governed agent contract for tool-using agents",
            "MCPHttpConnector handles HTTP/HTTPS MCP tool servers",
            "MCPStdioConnector handles stdio-based MCP tool servers",
            "Connector type is config-driven — swap without changing agent code",
            "Governance hooks fire before and after every external call",
        ],
        "key_concepts": ["MCPHttpConnector", "MCPStdioConnector", "BaseMCPAgent", "MCPClientAgent", "MCP tool server protocol", "governance boundary"],
        "used_in": ["MCPHttpConnector", "MCPStdioConnector", "BaseMCPAgent", "MCPClientAgent", "DocumentExtractorAgent (EOC)", "Docling OCR MCP server"],
        "github": "external-connector-pattern",
    },
}

CSS = """
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
    :root{
      --bg:#f7f4ef;--bg-card:#fff;--bg-tint:#f0ece4;
      --border:#ddd8cf;--border-l:#e8e3da;
      --ink:#1a1a1a;--ink-2:#3a3a3a;--ink-3:#666056;--muted:#9a9288;
      --blue:#1C69D4;--blue-bg:rgba(28,105,212,0.06);
      --gold:#7a5c1e;--gold-bg:rgba(122,92,30,0.07);
      --code-fg:#1C69D4;--code-bg:rgba(28,105,212,0.06);
    }
    html{scroll-behavior:smooth;}
    body{background:var(--bg);color:var(--ink-2);font-family:'Inter',Arial,system-ui,sans-serif;font-size:15px;line-height:1.75;-webkit-font-smoothing:antialiased;}

    /* Side overlay */
    .side-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:900;opacity:0;transition:opacity .3s ease;}
    .side-overlay.active{display:block;opacity:1;}

    /* Side panel */
    .side-panel{position:fixed;top:0;left:0;width:260px;height:100vh;background:#070f18;border-right:1px solid rgba(0,230,255,0.15);z-index:1000;transform:translateX(-100%);transition:transform .3s cubic-bezier(.4,0,.2,1);display:flex;flex-direction:column;overflow-y:auto;}
    .side-panel.open{transform:translateX(0);}
    .side-panel-header{display:flex;align-items:center;justify-content:space-between;padding:16px 18px 14px;border-bottom:1px solid rgba(0,230,255,0.10);}
    .side-panel-logo{color:#d4af37;font-size:15px;font-weight:700;}
    .side-close{background:none;border:none;color:#6f8a96;font-size:18px;cursor:pointer;padding:4px 8px;}
    .side-close:hover{color:#00E6FF;}
    .side-nav{list-style:none;padding:8px 0 16px;flex:1;}
    .side-back{display:block;padding:10px 18px;color:#00E6FF;font-size:13px;font-weight:600;border-bottom:1px solid rgba(0,230,255,0.08);margin-bottom:8px;}
    .side-back:hover{background:rgba(0,230,255,0.05);}
    .side-cat{display:block;padding:6px 18px 2px;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#4d6880;}
    .side-link{display:block;padding:9px 18px 9px 24px;color:#8aa0ae;font-size:13px;border-left:2px solid transparent;transition:color .18s,background .18s,border-color .18s;}
    .side-link:hover{color:#00E6FF;background:rgba(0,230,255,0.04);border-left-color:rgba(0,230,255,0.3);}
    .side-link.active{color:#00E6FF;border-left-color:#00E6FF;}

    /* Nav */
    .site-nav{background:#0f1720;border-bottom:1px solid rgba(0,230,255,0.08);}
    .nav-inner{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;padding:0 32px;flex-wrap:wrap;}
    .nav-left{display:flex;align-items:center;gap:0;}
    .hamburger{display:flex;flex-direction:column;gap:4px;background:none;border:1px solid rgba(0,230,255,0.18);border-radius:6px;cursor:pointer;padding:7px 9px;margin-right:16px;transition:border-color .2s,background .2s;}
    .hamburger:hover{border-color:rgba(0,230,255,0.45);background:rgba(0,230,255,0.05);}
    .hamburger span{display:block;width:18px;height:2px;background:#8aa0ae;border-radius:2px;}
    .hamburger:hover span{background:#00E6FF;}
    .nav-brand{font-size:1rem;font-weight:700;color:#e8edf0;text-decoration:none;letter-spacing:0.04em;padding:14px 0;}
    .nav-brand span{color:#00E6FF;}
    .nav-links{display:flex;}
    .nav-links a{display:inline-block;padding:13px 22px;color:#6f8a96;text-decoration:none;font-size:0.88rem;border-left:1px solid rgba(0,230,255,0.08);transition:color .2s,background .2s;}
    .nav-links a:last-child{border-right:1px solid rgba(0,230,255,0.08);}
    .nav-links a:hover{color:#00E6FF;background:rgba(0,230,255,0.05);}

    /* Page */
    .page{max-width:1100px;margin:0 auto;padding:0 32px;}

    /* Article */
    .article-header{max-width:760px;padding:60px 0 44px;border-bottom:1px solid var(--border);margin-bottom:44px;}
    .article-kicker{font-size:0.68rem;font-weight:600;letter-spacing:0.24em;text-transform:uppercase;color:var(--blue);margin-bottom:18px;}
    .article-title{font-size:clamp(24px,3.5vw,38px);font-weight:800;color:var(--ink);letter-spacing:-0.4px;line-height:1.15;margin-bottom:14px;}
    .article-intent{font-size:1rem;color:var(--ink-3);max-width:680px;line-height:1.7;}

    .article-body{max-width:760px;}
    .article-body h2{font-size:1.1rem;font-weight:700;color:var(--ink);margin:36px 0 12px;letter-spacing:-0.2px;}
    .article-body p{color:var(--ink-3);margin-bottom:14px;line-height:1.75;}
    .article-body ul{list-style:none;padding:0;margin:0 0 16px;}
    .article-body ul li{padding:6px 0 6px 20px;position:relative;color:var(--ink-3);font-size:14px;border-bottom:1px solid var(--border-l);}
    .article-body ul li::before{content:"→";position:absolute;left:0;color:var(--blue);}
    .article-body ul li:last-child{border-bottom:none;}

    /* Image */
    .pattern-image{margin:28px 0;border:1px solid var(--border);border-radius:10px;overflow:hidden;background:var(--bg-card);}
    .pattern-image img{width:100%;display:block;}
    .pattern-image figcaption{padding:8px 14px;font-size:12px;color:var(--muted);border-top:1px solid var(--border-l);font-style:italic;}

    /* Tags */
    .usage-tags{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px;}
    .usage-tag{font-size:0.76rem;font-weight:500;color:var(--code-fg);background:var(--code-bg);border:1px solid rgba(28,105,212,0.14);border-radius:5px;padding:3px 9px;font-family:'Courier New',monospace;}

    /* GitHub link */
    .github-link{display:inline-flex;align-items:center;gap:8px;margin-top:32px;padding:12px 20px;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;color:var(--ink-2);font-size:13px;font-weight:600;transition:border-color .2s,box-shadow .2s;}
    .github-link:hover{border-color:#c8c0b4;box-shadow:0 2px 10px rgba(0,0,0,0.06);}

    /* Back link */
    .back-link{display:inline-block;margin:0 0 32px;font-size:13px;font-weight:600;color:var(--blue);}
    .back-link:hover{text-decoration:underline;}
    .bottom-back{margin:48px 0 0;padding-top:32px;border-top:1px solid var(--border);}

    /* Footer */
    footer{background:#0f1720;border-top:1px solid rgba(0,230,255,0.08);padding:40px 32px;margin-top:64px;}
    .footer-inner{max-width:1100px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:20px;}
    .footer-brand{font-weight:700;color:#e8edf0;font-size:0.95rem;}
    .footer-brand span{color:#00E6FF;}
    .footer-links{display:flex;gap:20px;flex-wrap:wrap;}
    .footer-links a{font-size:0.82rem;color:#6f8a96;text-decoration:none;transition:color .2s;}
    .footer-links a:hover{color:#00E6FF;}
    .footer-copy{max-width:1100px;margin:16px auto 0;padding-top:14px;border-top:1px solid rgba(0,230,255,0.08);font-size:0.72rem;color:#4d6270;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;}

    @media(max-width:700px){.page{padding:0 20px;}.nav-inner{padding:0 16px;}.nav-links a{padding:13px 14px;font-size:0.8rem;}footer{padding:32px 20px;}.article-header{padding:40px 0 32px;}}
"""

JS = """
  var hamburger=document.getElementById('hamburger');
  var sidePanel=document.getElementById('side-panel');
  var sideClose=document.getElementById('side-close');
  var overlay=document.getElementById('side-overlay');
  function open(){sidePanel.classList.add('open');overlay.classList.add('active');document.body.style.overflow='hidden';}
  function close(){sidePanel.classList.remove('open');overlay.classList.remove('active');document.body.style.overflow='';}
  if(hamburger)hamburger.addEventListener('click',open);
  if(sideClose)sideClose.addEventListener('click',close);
  if(overlay)overlay.addEventListener('click',close);
  document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
  document.querySelectorAll('a[href^="#"]').forEach(function(a){a.addEventListener('click',function(e){var t=document.querySelector(this.getAttribute('href'));if(t){e.preventDefault();t.scrollIntoView({behavior:'smooth'});close();}});});
"""

SIDE_PANEL_CATS = [
    ("EXECUTION", ["agent-squad-pattern", "validation-loop-pattern", "critic-actor-pattern"]),
    ("INFERENCE", ["model-router-pattern", "inference-pattern", "provider-adapter-pattern"]),
    ("GOVERNANCE", ["factory-pattern", "runtime-agent-loader-pattern"]),
    ("INTEGRATION", ["external-connector-pattern"]),
]

PATTERN_TITLES = {p["id"]: PATTERN_DATA[p["id"]]["title"] for p in PATTERNS}
PATTERN_FILES = {p["id"]: p["id"] + ".html" for p in PATTERNS}


def make_side_panel(current_id):
    items = ['<div class="side-overlay" id="side-overlay"></div>']
    items.append('<nav class="side-panel" id="side-panel">')
    items.append('<div class="side-panel-header"><span class="side-panel-logo">K9-AIF Patterns</span><button class="side-close" id="side-close">&#x2715;</button></div>')
    items.append('<ul class="side-nav">')
    items.append('<li><a href="index.html" class="side-back">&#x2190; All Patterns</a></li>')
    for cat_name, pattern_ids in SIDE_PANEL_CATS:
        items.append(f'<li><span class="side-cat">{cat_name}</span></li>')
        for pid in pattern_ids:
            active = ' active' if pid == current_id else ''
            title = PATTERN_TITLES[pid]
            href = PATTERN_FILES[pid]
            items.append(f'<li><a href="{href}" class="side-link{active}">{title}</a></li>')
    items.append('</ul></nav>')
    return '\n'.join(items)


def make_page(pattern_id):
    p = PATTERN_DATA[pattern_id]
    meta = next(m for m in PATTERNS if m["id"] == pattern_id)
    title = p["title"]
    kicker = meta["cat"] + " Pattern"
    intent = p["intent"]
    image_html = ""
    if p["image"]:
        image_html = f'''<figure class="pattern-image">
      <img src="{p["image"]}" alt="{title} diagram" loading="lazy">
      <figcaption>{title} — structural diagram</figcaption>
    </figure>'''

    structure_items = "\n".join(f"<li>{s}</li>" for s in p["structure"])
    concept_tags = "\n".join(f'<span class="usage-tag">{c}</span>' for c in p["key_concepts"])
    used_tags = "\n".join(f'<span class="usage-tag">{u}</span>' for u in p["used_in"])
    side_panel = make_side_panel(pattern_id)
    github_url = f"https://github.com/k9aif/k9aif-patterns/tree/main/k9aif-patterns/{p['github']}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} &#8212; K9-AIF Patterns</title>
  <meta name="description" content="{intent}">
  <meta name="author" content="Ravi Natarajan">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>

{side_panel}

<nav class="site-nav">
  <div class="nav-inner">
    <div class="nav-left">
      <button class="hamburger" id="hamburger" aria-label="Open menu"><span></span><span></span><span></span></button>
      <a href="https://k9x.ai" class="nav-brand">K9X<span>.ai</span></a>
    </div>
    <div class="nav-links">
      <a href="https://k9x.ai">Home</a>
      <a href="https://pydocs.k9x.ai/starthere/">Docs</a>
      <a href="https://blog.k9x.ai">Blog</a>
      <a href="https://graph.k9x.ai" target="_blank" rel="noopener">Graph Explorer</a>
      <a href="https://github.com/k9aif/k9aif-patterns" target="_blank" rel="noopener">GitHub</a>
    </div>
  </div>
</nav>

<div class="page">

  <header class="article-header">
    <div class="article-kicker">{kicker}</div>
    <h1 class="article-title">{title}</h1>
    <p class="article-intent">{intent}</p>
  </header>

  <div class="article-body">

    <a href="index.html" class="back-link">&#x2190; All Patterns</a>

    {image_html}

    <h2>Motivation</h2>
    <p>{p["motivation"].replace(chr(10)+chr(10), "</p><p>")}</p>

    <h2>Structure</h2>
    <ul>
      {structure_items}
    </ul>

    <h2>Key Concepts</h2>
    <div class="usage-tags">
      {concept_tags}
    </div>

    <h2>Used in K9-AIF</h2>
    <div class="usage-tags">
      {used_tags}
    </div>

    <div class="bottom-back">
      <a href="{github_url}" class="github-link" target="_blank" rel="noopener">
        View implementation on GitHub &#x2197;
      </a>
    </div>

  </div>

</div>

<footer>
  <div class="footer-inner">
    <div class="footer-brand">K9X<span>.ai</span></div>
    <div class="footer-links">
      <a href="https://k9x.ai">k9x.ai</a>
      <a href="index.html">Pattern Catalog</a>
      <a href="https://github.com/k9aif/k9-aif-framework" target="_blank" rel="noopener">Framework</a>
      <a href="https://github.com/k9aif/k9aif-patterns" target="_blank" rel="noopener">GitHub</a>
    </div>
  </div>
  <div class="footer-copy">
    <span>&#169; 2026 K9X.ai &#183; Ravi Natarajan &#183; Apache 2.0</span>
    <span>Architecture patterns for governed agentic AI systems.</span>
  </div>
</footer>

<script>
{JS}
</script>
</body>
</html>"""


if __name__ == "__main__":
    for p in PATTERNS:
        pid = p["id"]
        filename = os.path.join(BASE, pid + ".html")
        content = make_page(pid)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Written: {pid}.html")

    # Update index.html card links
    index_path = os.path.join(BASE, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        idx = f.read()

    import re
    for pid in PATTERN_DATA:
        gh_url = f"https://github.com/k9aif/k9aif-patterns/tree/main/k9aif-patterns/{pid}"
        local_url = f"{pid}.html"
        idx = idx.replace(
            f'href="{gh_url}" class="card-link"',
            f'href="{local_url}" class="card-link"'
        )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(idx)
    print("  Updated: index.html (card links now point to local pages)")
    print(f"\nDone. {len(PATTERN_DATA)} pages generated.")
