# The Solution: How MCP Works

← **Back to Overview:** [MCP](../INDEX.md)

---

## The Core Idea

MCP solves the M×N integration problem by introducing a **shared protocol layer** between AI applications and data sources.

```
BEFORE MCP                          WITH MCP
──────────────────────              ──────────────────────────────────
App A ──custom──→ Source 1          App A ──MCP client──┐
App A ──custom──→ Source 2                               ├──→ Source 1 (MCP server)
App B ──custom──→ Source 1          App B ──MCP client──┤
App B ──custom──→ Source 2                               └──→ Source 2 (MCP server)

M×N = 4 connectors                 M+N = 4 implementations, unlimited connections
```

Any client connects to any server. The protocol defines the contract both sides agree to.

---

## What the Protocol Defines

MCP specifies six **primitive types** — the building blocks of all AI-data interaction. Three are exposed *by servers*, three are exposed *by clients*.

### Server-Side Primitives (what servers offer)

| Primitive | Who Controls | What It Is |
|-----------|-------------|-----------|
| **Tools** | Model-controlled | Executable functions the LLM can invoke |
| **Resources** | App-controlled | Passive data the application surfaces |
| **Prompts** | User-controlled | Reusable templates users explicitly select |

### Client-Side Primitives (what clients offer back)

| Primitive | Direction | What It Is |
|-----------|-----------|-----------|
| **Sampling** | Server → Host LLM | Server requests LLM text generation |
| **Elicitation** | Server → User | Server requests structured user input |
| **Roots** | Client → Server | Client exposes filesystem boundaries |

The *controller* distinction matters: Tools are invoked autonomously by the LLM; Resources are included in context by the application; Prompts are triggered by explicit user action.

---

## Server-Side Primitives in Detail

### Tools — Model-Controlled Actions

Tools are functions the LLM *decides* to call. They have side effects and require explicit invocation intent.

```
Example tools:
  search_web(query: string) → results
  query_database(sql: string) → rows
  send_email(to: string, subject: string, body: string) → confirmation
  create_issue(title: string, body: string, labels: list) → issue_id
```

Tools answer: *"What can the AI do?"*

### Resources — Application-Controlled Context

Resources are data the **application** decides to include in the LLM's context — not the model, not the user. They're passive: reading them has no side effects.

```
Example resources:
  file:///home/user/project/README.md   → file content
  postgres://schema/users_table         → table schema
  github://repos/my-org/my-repo         → repo metadata
```

Resources answer: *"What context does the AI have?"*

### Prompts — User-Controlled Templates

Prompts are parameterized templates users explicitly invoke (like slash commands). They shape the LLM's interaction pattern for a specific task.

```
Example prompts:
  /summarize-pr(pr_number: int)
  /write-test(function_name: string, language: string)
  /analyze-log(log_file: string, error_type: string)
```

Prompts answer: *"How does the user invoke a structured workflow?"*

---

## Client-Side Primitives in Detail

### Sampling — LLM Access for Servers

Servers can request the Host's LLM to generate text. This makes servers **model-agnostic** — the server specifies preferences, the Host chooses the model.

```
Server → Client: "Please generate a summary of this document"
Client → LLM: routes to whatever model the Host is running
LLM → Client → Server: generated text
```

The server never knows which model was used. It works identically with Claude, GPT-4, or any local model.

### Elicitation — Structured User Input

Servers can pause and request structured information from the user via the Host. The user can accept (with data), decline, or cancel.

```
Server → Client: "Before deleting 50 records, confirm:
                  { records_to_delete: int, confirm_backup: bool }"
User   → Client: accept { records_to_delete: 50, confirm_backup: true }
Client → Server: approved, proceed
```

### Roots — Filesystem Boundaries

Clients expose `file://` URIs representing the directories the server is allowed to access. This scopes server access to declared workspace roots.

```
Client declares: file:///home/user/projects/my-app
Server knows: only files under this path are in scope
```

---

## The Security Model

MCP's solution is not just about connectivity — it bakes security into the protocol:

### Consent at Every Layer

```
User consent    → which servers can the Host connect to?
App consent     → which capabilities does the Host declare?
Elicitation     → does the user approve this specific server action?
Tool call       → does the user see and approve this tool invocation?
```

### Principle of Least Disclosure

- Resources return only what the server chooses to expose
- Tool results contain only what's needed — not raw database rows
- Roots limit filesystem access to declared boundaries
- Capability negotiation limits what a server can even attempt

### The Trust Hierarchy

```
Most trusted    User (highest authority)
                ↓
                Host (mediates all server interactions)
                ↓
                Client (executes protocol mechanics)
                ↓
Least trusted   Server (untrusted third-party code)
```

Servers are treated as untrusted third parties. Every capability they use must be explicitly granted by the Host.

---

## The M×N Reduction in Practice

With MCP in place:

- **1 MCP client implementation** connects to all existing and future servers
- **1 MCP server implementation** works with all existing and future hosts
- **No coordination required** between client developers and server developers
- **Model upgrades** don't require server changes (Sampling keeps servers model-agnostic)
- **New data sources** become available to all hosts simultaneously

The math: 100 AI applications + 500 data sources = **600 implementations, 50,000 working connections**.

Without MCP: 50,000 custom integrations — maintained, versioned, and debugged separately.

---

## What MCP Does Not Do

MCP is a connectivity protocol, not an execution engine:

| What MCP provides | What you still build |
|-------------------|---------------------|
| How tools are described and called | What the tools actually do |
| How resources are accessed | What data the resources contain |
| How the LLM requests generation | Which model to use and the prompting strategy |
| A consent framework | The application's specific authorization policies |
| A transport standard | The server's business logic |

---

**Related Topics:**
- [The Problem →](01-The-Problem.md)
- [Capabilities →](05-Capabilities.md)
- [Why It Matters →](06-Why-MCP-Matters.md)

---

## Q&A Review Bank

**Q1: What are the three server-side primitives and what controls each one?** `[Easy]`

A: Tools are model-controlled — the LLM autonomously decides when to invoke them based on task context. Resources are application-controlled — the host application decides which data to include in the LLM's context. Prompts are user-controlled — the user explicitly triggers them like slash commands. This three-way split is deliberate: it assigns clear authority to the right actor for each type of interaction, preventing the LLM from autonomously reading passive data (a Resource concern), or the application from automatically executing side-effecting operations (a Tool concern).

---

**Q2: What is the Roots primitive and how does it limit server access?** `[Medium]`

A: Roots are `file://` URIs declared by the client that define the filesystem boundaries the server is permitted to access — typically the user's active project directories or workspaces. The server queries `roots/list` to discover which paths are in scope, and should restrict all file operations to paths under those roots. The client receives `notifications/roots/list_changed` when the workspace changes. This prevents a server from accessing files outside the user's intended scope — a server for a project at `/home/user/projects/app` cannot read `/home/user/.ssh/` unless that path is explicitly declared as a root.

---

**Q3: Explain the MCP trust hierarchy and why Servers are at the bottom.** `[Medium]`

A: The trust hierarchy flows: User (highest) → Host → Client → Server (lowest). Servers are treated as untrusted third parties because they are arbitrary code, potentially authored by anyone and distributed through the open-source ecosystem. A server cannot use any capability the Host didn't explicitly declare during initialization; all server-initiated interactions with the user (Elicitation) and the LLM (Sampling) must pass through the Host, which can inspect and reject them. This design ensures that even a compromised or malicious server is constrained by what the Host permits — it cannot directly access the LLM, the user, or capabilities beyond its declared scope.

---

**Q4: How does the Sampling primitive achieve model-agnosticism for MCP servers?** `[Hard]`

A: When a server needs LLM-generated text, it sends a `sampling/createMessage` request specifying messages and preferences (costPriority, speedPriority, intelligencePriority, and optional model name hints) — but never a specific model API endpoint or API key. The Host intercepts this request, selects the actual model based on its own configuration and the server's preferences, executes the generation, and returns the result to the server. The server never knows which model was used and never holds credentials. When the Host switches from Claude to GPT-4, every MCP server immediately runs against the new model without any server-side changes.

---

**Q5: What is the difference between a Tool error and a protocol error in MCP, and why does the distinction matter?** `[Hard]`

A: A protocol error occurs when something goes wrong at the communication level — unknown method name, malformed JSON, server failure, timeout — and is returned as a JSON-RPC error object (with negative error codes like `-32602`). A Tool execution error is when the tool ran successfully from a protocol perspective but the business logic failed (e.g., "file not found", "permission denied", "query returned no results") — this is returned as a normal result with `isError: true` in the response body. The distinction matters because the LLM should treat protocol errors as communication failures (retry or escalate) but treat tool execution errors as informative results it can reason about — "the file wasn't found, so I should try a different path."
