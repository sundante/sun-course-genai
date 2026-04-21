# Definition: What Is MCP?

← **Back to Overview:** [MCP](../INDEX.md)

---

## The One-Sentence Definition

**Model Context Protocol (MCP)** is an open standard that enables AI applications to securely connect to external data sources and tools through a uniform, bidirectional protocol — so any compliant AI client can work with any compliant data server without custom integration code.

---

## The USB-C Analogy

Before USB-C, every device had its own proprietary cable. Charging a phone, connecting a monitor, and transferring data all required different connectors — you carried five cables for five devices.

USB-C is a universal connector: one cable works for charging, data transfer, video output, and audio. Device manufacturers build to the USB-C spec once, and their device works with every USB-C peripheral ever made.

**MCP is the USB-C port for AI:**

- **Before MCP:** Every AI app has its own connector format for every data source. 5 apps × 8 sources = 40 custom connectors.
- **With MCP:** Every AI app implements one MCP client. Every data source implements one MCP server. 5+8 = 13 total implementations, 40 working connections.

The universality is the value. A server built for Claude Desktop today automatically works with VS Code, ChatGPT, Cursor, and any future MCP-compatible host — without any changes to the server.

---

## Formal Properties

MCP has five defining properties:

| Property | What It Means |
|----------|--------------|
| **Open standard** | Publicly specified, freely implementable, no vendor lock-in |
| **Bidirectional** | Both client and server can initiate messages |
| **Stateful** | Sessions maintain context across multiple requests |
| **Secure** | Capability negotiation, consent gates, access controls are protocol-native |
| **Model-agnostic** | Works with any LLM — no hardcoded model dependencies |

---

## What MCP Is NOT

It's worth being explicit about scope boundaries:

- **Not an LLM API** — MCP doesn't define how to call a language model; it defines how AI *applications* connect to *external systems*
- **Not a RAG framework** — MCP can power retrieval but is not itself a retrieval system
- **Not an agent framework** — MCP provides tool access; orchestration logic lives above the protocol
- **Not HTTP** — MCP uses HTTP as one of its transports, but the protocol itself is JSON-RPC 2.0 over a transport layer

---

## The Protocol Stack

MCP is organized into two layers:

```
┌─────────────────────────────────────────────┐
│             DATA LAYER                       │
│  JSON-RPC 2.0 message framing               │
│  • Lifecycle management (init/shutdown)      │
│  • Primitives: Tools, Resources, Prompts     │
│  • Capabilities: Sampling, Elicitation       │
│  • Utilities: Progress, Cancellation, Logging│
├─────────────────────────────────────────────┤
│            TRANSPORT LAYER                   │
│  How bytes get from A to B                  │
│  • Stdio (local subprocess)                  │
│  • Streamable HTTP (remote server)           │
│  • Custom transports (implementable)         │
└─────────────────────────────────────────────┘
```

The separation is deliberate: the data layer defines *what* is communicated; the transport layer defines *how* it travels. You can swap transports without changing protocol semantics.

---

## JSON-RPC 2.0 — The Data Layer Foundation

All MCP messages are JSON-RPC 2.0. This is a lightweight remote procedure call protocol with three message types:

### Request
Sent by either side when expecting a response. Has a unique `id`.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_database",
    "arguments": { "query": "active customers" }
  }
}
```

### Response
Sent in reply to a request. Contains either a `result` or an `error`.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{ "type": "text", "text": "Found 42 active customers." }],
    "isError": false
  }
}
```

### Notification
One-way message with no response expected. No `id` field.

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

### Why JSON-RPC (not REST)?

| Concern | REST | JSON-RPC 2.0 |
|---------|------|-------------|
| Bidirectional messaging | Requires webhooks | Native (both sides send requests) |
| Server push | Not natural | Notifications built-in |
| Error structure | HTTP status codes (can be lost in transit) | Structured error objects in payload |
| Session state | Stateless by design | Stateful sessions supported |
| Request correlation | Via URL routing | Via `id` field |

---

## The Two Transports

### Stdio Transport

The server runs as a **subprocess** launched by the client. Communication happens over standard input/output.

```
Client ──stdin──→ Server
Client ←─stdout── Server
               ←─stderr── Server logs (optional)
```

Rules:
- Messages are newline-delimited JSON on a single line — **no embedded newlines** in messages
- Server **MUST NOT** write non-MCP data to stdout (it will break parsing)
- Server **MAY** write UTF-8 logs to stderr for debugging

Best for: Development, desktop applications, local tools.

### Streamable HTTP Transport

The server is an **independent HTTP service**. The client sends requests; the server can stream responses.

```
Client ──HTTP POST──→ Server
Client ←─HTTP resp── Server (single response or SSE stream)
Client ──HTTP GET──→ Server (open SSE stream for server-initiated messages)
```

Key requirements:
- Client **MUST** include `Accept: application/json, text/event-stream` on every request
- Client **MUST** include `MCP-Protocol-Version: <version>` header
- Server **MAY** assign a session ID in `Mcp-Session-Id` header; client **MUST** echo it on all subsequent requests
- For long-running streams: server attaches event `id` fields; client can resume using `Last-Event-ID`

Best for: Remote servers, multi-tenant services, cloud deployments.

---

## Ecosystem Adoption

MCP is supported by a broad and growing set of hosts:

| Host | Type |
|------|------|
| Claude Desktop (Anthropic) | Desktop AI assistant |
| Claude.ai | Web AI assistant |
| VS Code | Code editor |
| Cursor | AI code editor |
| Zed | Code editor |
| ChatGPT (OpenAI) | Web AI assistant |
| MCPJam | MCP playground |

"Build once, integrate everywhere" — a server built for Claude Desktop today works in VS Code and Cursor without modification.

---

**Related Topics:**
- [The Solution →](03-The-Solution.md)
- [Components →](04-Components.md)
- [Architecture Deep-Dive →](07-Architecture-Deep-Dive.md)

---

## Q&A Review Bank

**Q1: Define MCP in one sentence and identify its two communication endpoints.** `[Easy]`

A: MCP is an open standard that enables AI applications (MCP Clients, managed by an MCP Host) to securely connect to external data and capability providers (MCP Servers) through a uniform, bidirectional protocol. The two endpoints are the Client side — the AI application — and the Server side — the program exposing tools, resources, or prompts. The protocol defines how these two sides discover each other's capabilities, negotiate a session, and exchange messages.

---

**Q2: What does "open standard" mean for MCP and why does it matter more than a well-documented proprietary API?** `[Medium]`

A: An open standard is a publicly available specification that any party can implement without licensing fees or vendor permission, unlike proprietary APIs that create dependency on a single vendor's decisions. For MCP, any server built to the spec works immediately with every compliant client — including those built by competitors. A proprietary API must be updated by one team; an open standard benefits from every implementer's improvements. The network effect is compounding: each new MCP server adds value to every existing client, and each new client adds value to every existing server.

---

**Q3: What does JSON-RPC 2.0 give MCP that REST cannot provide natively?** `[Medium]`

A: JSON-RPC 2.0 supports bidirectional messaging (both sides can initiate requests) and server-push notifications — REST is stateless and request/response only, requiring webhooks for server-initiated communication. JSON-RPC error objects travel inside the response payload (not HTTP headers), so they can't be lost or rewritten by proxies. JSON-RPC sessions are stateful, enabling capability negotiation that persists across requests. These properties map naturally to MCP's needs: tool call/response, server capability change notifications, in-flight progress updates, and session-level auth all require what JSON-RPC provides natively.

---

**Q4: When should you choose stdio transport over HTTP/SSE, and what constraint makes this a firm rule?** `[Hard]`

A: Choose stdio when the MCP server should run as a subprocess on the user's machine — desktop apps, local tools, development environments. The firm constraint is that with stdio, a server **MUST NOT** write any non-MCP data to stdout: debug prints, log statements, or any other stdout output will corrupt the newline-delimited JSON stream and break parsing. This means the server must redirect all logs to stderr. HTTP/SSE is required when the server needs independent lifecycle (outlive the client process), serves multiple clients simultaneously, or requires network-level access. The choice is not just architectural preference — it's constrained by deployment topology.

---

**Q5: What does the `Mcp-Session-Id` header do in HTTP transport and what happens if a client ignores it?** `[Hard]`

A: When a server assigns a `Mcp-Session-Id` in its response headers, it's establishing a session context that links subsequent requests to the same initialized session — with all its negotiated capabilities, active subscriptions, and in-flight state. A client that ignores this header will send subsequent requests without the session ID; the server will treat them as new, uninitialized connections and reject them with a 404 or an uninitialized error. Session IDs should be globally unique and cryptographically secure (not guessable) to prevent session hijacking in multi-tenant deployments.
