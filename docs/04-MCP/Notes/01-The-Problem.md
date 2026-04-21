# The Problem MCP Solves

← **Back to Overview:** [MCP](../INDEX.md)

---

## The AI Integration Crisis

AI models are powerful in isolation, but isolated is exactly the problem. A language model sitting behind a chat interface can only work with what you paste into the prompt. To do anything *real* — check your calendar, query a database, read a file, call an API — the model needs access to external systems.

Every team building AI applications faces the same wall: **how do you connect the model to the data it needs?**

The answer before MCP was: you build a custom connector. Every time, for every source, for every application.

---

## The M×N Explosion

Imagine you have **M = 5** AI applications:

| App | Purpose |
|-----|---------|
| Claude Desktop | General assistant |
| VS Code AI | Code completion |
| Internal chatbot | Employee Q&A |
| Support agent | Customer service |
| Analytics copilot | Data analysis |

And **N = 6** data sources:

| Source | Type |
|--------|------|
| GitHub | Code & issues |
| Slack | Messages & channels |
| PostgreSQL | Business data |
| Google Drive | Documents |
| Jira | Project tracking |
| Salesforce | CRM |

Without a standard protocol, each of the **5 × 6 = 30** pairs needs its own custom integration:

```
Claude Desktop ──→ GitHub connector (custom)
Claude Desktop ──→ Slack connector (custom)
Claude Desktop ──→ Postgres connector (custom)
VS Code AI     ──→ GitHub connector (custom, different)
VS Code AI     ──→ Slack connector (custom, different)
...
```

Every integration is built from scratch. Every team reinvents the same auth handling, pagination, error recovery, and data transformation. When GitHub changes their API, **every** GitHub connector breaks separately. When a new data source appears, every application has to build its own connector.

This is the **M×N integration problem** — and it scales catastrophically.

---

## What Partial Solutions Failed to Solve

### REST APIs

REST APIs standardize the *transport* (HTTP) and the *data format* (JSON) but not the *semantic contract*. Every API has:

- Different authentication schemes (OAuth2, API keys, JWT, basic auth)
- Different pagination patterns (cursor, offset, page number)
- Different error formats and status code conventions
- Different rate limiting mechanisms
- Different SDK requirements per language

Building a "Postgres integration" for Claude Desktop is completely different work from building a "Postgres integration" for VS Code AI — even though they're both reading the same database.

### LLM Function Calling

Function calling was a breakthrough — it let models output structured JSON to signal intent to call a function. But it introduced its own fragmentation:

| Provider | Schema Format |
|----------|--------------|
| OpenAI | `functions` array with JSON Schema parameters |
| Anthropic | `tools` array with `input_schema` |
| Google | `function_declarations` in `tools` |
| Mistral | OpenAI-compatible (different edge cases) |

A tool written for OpenAI's function calling format requires adaptation for Anthropic's tool_use format. A team building 10 tools has to maintain 4 different schema definitions per tool — one per provider.

Function calling also has **no concept of:**

- Data discovery (how does the model learn what tools exist at runtime?)
- Passive data access (reading a file shouldn't require a "tool call" with side-effect semantics)
- Server-to-model communication (the server can't ask the model a question)
- Standard consent mechanics (who approves the call?)
- Cross-session portability (tools defined for one app can't be used by another)

### Plugin Systems

Early plugin systems (OpenAI Plugins, etc.) were vendor-specific: a plugin built for one AI platform didn't work with any other. They recreated the M×N problem at the platform level — if 4 AI vendors each had proprietary plugin formats, every tool developer had to build and maintain 4 separate plugin implementations.

---

## The Root Causes

The integration crisis has three root causes:

### 1. No Shared Semantic Contract

Every integration defines its own conventions for what a "tool call" means, what a "data source" looks like, and how errors are reported. Without a common contract, integrations cannot be reused across applications or model providers.

### 2. No Separation of Concerns

Before MCP, the AI application was responsible for knowing about every data source it might use. Adding a new source required modifying the application. This couples the application's logic to its integrations in a way that makes both harder to change.

### 3. Model-Specific Coupling

Tools, prompts, and context retrieval patterns written for one LLM provider cannot be used with another. Organizations that switch or multi-home across providers must rebuild all their integrations.

---

## The Concrete Cost

A 10-person AI team maintaining 5 AI products connected to 8 data sources:

- **Without MCP:** 40 custom connectors, each maintained independently
- **When a source changes its API:** Up to 5 emergency patches
- **When switching LLM providers:** Rewrite all function calling schemas
- **When adding a new product:** Build 8 new connectors

This is the status quo MCP was built to end.

---

## Key Takeaway

The fundamental problem is not that connecting AI to data is technically hard — it's that without a standard protocol, every connection must be built from scratch, coupling applications to sources, sources to models, and models to vendors. MCP addresses all three couplings simultaneously with one shared protocol.

---

**Related Topics:**
- [The Solution →](03-The-Solution.md)
- [Why MCP Matters →](06-Why-MCP-Matters.md)

---

## Q&A Review Bank

**Q1: What specific inefficiency does the "M×N integration problem" describe?** `[Easy]`

A: When M AI applications each need to connect to N data sources, every pair requires a custom implementation — producing M×N unique connectors with no reuse across pairs. Each new application must re-implement adapters others have already built, and each new data source must be adapted separately for every existing application. This creates exponentially growing maintenance burden, duplicated engineering effort, and a fragile web of integrations that break independently whenever either side changes.

---

**Q2: Why didn't LLM function calling solve the integration problem?** `[Medium]`

A: Function calling standardized the invocation contract (how the LLM signals intent to call a function) but remained model-specific — OpenAI's function schema, Anthropic's tool_use format, and Google's function_declarations are all different, requiring separate implementations per provider. It also provided no standard for data discovery (how does the model learn what tools exist at runtime?), passive data reads (reading a schema shouldn't have side-effect semantics), cross-session portability, or consent mechanics. MCP addresses all of these as protocol-level concerns that transcend any single model provider.

---

**Q3: What are the three root causes of the AI integration crisis?** `[Medium]`

A: First, no shared semantic contract — every integration defines its own conventions for tool calls, data sources, and error reporting, making integrations non-reusable across applications. Second, no separation of concerns — AI applications were coupled to their data sources, so adding a new source required modifying the application itself. Third, model-specific coupling — tools and prompt patterns written for one LLM provider couldn't be used with another, locking teams into a single vendor or forcing them to maintain multiple versions of the same integration.

---

**Q4: Why did vendor-specific plugin systems fail to solve the integration problem?** `[Hard]`

A: Proprietary plugin systems recreated the M×N problem at the platform level: a plugin built for OpenAI Plugins didn't work with Anthropic, Claude Desktop, or any other host. If four AI vendors each maintain their own plugin format, tool developers must build and maintain four separate plugin implementations for the same capability — the number of integrations required didn't shrink, it just moved from the application layer to the plugin layer. An open, vendor-neutral protocol is the only architecture that collapses M×N without creating a new fragmentation elsewhere.

---

**Q5: How does the pre-MCP integration landscape compare to the early web before HTTP standardization?** `[Hard]`

A: Early networked applications each implemented proprietary data exchange formats, requiring custom parsers for every pair of systems that needed to communicate. HTTP and REST standardized web data exchange, creating the modern API economy — any HTTP client works with any HTTP server ever built. MCP is making the same bet for AI-data integration: the API economy created enormous value by collapsing M×N proprietary protocols into M+N HTTP implementations, and MCP's open-standard approach aims to produce the same compounding return for the AI integration layer.
