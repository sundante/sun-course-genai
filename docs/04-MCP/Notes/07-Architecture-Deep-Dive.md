Based on the [Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture) from the Model Context Protocol documentation, I've organized these notes into a structured format. 

You can copy the content below and save it as an `.md` file (e.g., `MCP_Architecture_Notes.md`) for your personal study.

---

# 📝 Learning Notes: MCP Architecture

## 🌟 Overview
The **Model Context Protocol (MCP)** is a standardized protocol designed to help AI applications (Hosts) exchange context with various data sources and services (Servers). It focuses strictly on the **context exchange**, not on how the LLM actually uses that data.

---

## 🏗️ Core Participants
The ecosystem consists of three main roles:
* **MCP Host**: The "brain" or AI application (e.g., Claude Desktop, VS Code). It manages multiple clients.
* **MCP Client**: A bridge created by the Host to maintain a dedicated connection to a specific server.
* **MCP Server**: The "provider." A program that exposes tools, resources, or prompts to the client. Can be **Local** (via STDIO) or **Remote** (via HTTP).

---

## ⚡ The Two-Layer System

### 1. Data Layer (The "What")
Uses **JSON-RPC 2.0** to define how messages are structured.
* **Lifecycle Management**: Handles the "handshake" (initialization), capability negotiation, and shutdown.
* **Primitives**: The actual "stuff" being shared (Tools, Resources, Prompts).
* **Utilities**: Features like real-time notifications and progress tracking.

### 2. Transport Layer (The "How")
Handles the actual physical/network connection.
* **Stdio Transport**: Used for local processes. Very fast with zero network overhead.
* **Streamable HTTP Transport**: Used for remote servers. Uses HTTP POST and Server-Sent Events (SSE).

---

## 🛠️ The Core Primitives (Server Side)
These are the primary ways a server provides value:
* **Tools**: Executable functions the AI can call (e.g., "fetch_weather" or "query_db").
* **Resources**: Passive data sources the AI can read (e.g., a file's content or a database schema).
* **Prompts**: Pre-defined templates to help structure the LLM's behavior or input.

### Client-Side Primitives
Servers can also ask the *Client* to do things:
* **Sampling**: The server asks the Host's LLM to generate text (model-agnostic).
* **Elicitation**: The server asks the user for more info or confirmation.
* **Logging**: The server sends logs to the Host for debugging.

---

## 🔄 Lifecycle: The Initialization Handshake
Before doing anything, the Client and Server must agree on rules:
1.  **Initialize Request**: Client sends its protocol version and what it can do (capabilities).
2.  **Initialize Response**: Server sends its version, info, and its own capabilities (e.g., "I support tools").
3.  **Initialized Notification**: Client confirms it's ready to start operations.

---

## 🔔 Real-Time Updates (Notifications)
MCP is **stateful**. If a server's tool list changes (e.g., a plugin is disabled), it doesn't wait for the client to ask.
* The server sends a `notifications/tools/list_changed`.
* The client then triggers a new `tools/list` request to refresh its registry.
* **Benefit**: No polling needed; the AI always has the latest capabilities.

---

## 💡 Key Takeaways for Developers
* **Model Independence**: Using the "Sampling" primitive allows servers to get LLM help without being tied to a specific SDK (like OpenAI or Anthropic).
* **Discovery**: The `list` methods allow for dynamic environments where tools and resources can change on the fly.
* **Standardization**: Whether a server is a local Python script or a remote API, the JSON-RPC messages look exactly the same.

---
*Source: [Model Context Protocol - Architecture](https://modelcontextprotocol.io/docs/learn/architecture)*

---

## Q&A Review Bank

**Q1: Walk through the MCP initialization handshake in order.** `[Easy]`

A: Step 1 — the Client sends an `initialize` request with its protocol version and capability set. Step 2 — the Server responds with its protocol version, server info (name, version), and its own capabilities. Step 3 — the Client sends an `initialized` notification confirming the session is ready. After this three-step exchange both sides know exactly which features the other supports, and the session is active. If the Client and Server cannot agree on a protocol version, the Server rejects the initialize request with a structured error and the connection fails before any data is exchanged.

---

**Q2: Compare stdio and HTTP/SSE transport — when do you choose each?** `[Medium]`

A: Stdio: the MCP server runs as a local subprocess; communication via stdin/stdout with zero network overhead; process lifetime is tied to the client; no auth infrastructure needed. Best for development, desktop integrations, and local-machine tools. HTTP/SSE: the server is an independently deployed HTTP service; client sends JSON-RPC via HTTP POST; server sends events to client via Server-Sent Events. Best for remote deployments, multi-client shared servers, cloud integrations, and servers requiring independent lifecycle and scaling. Rule of thumb: choose stdio when the server should die with the client process; choose HTTP/SSE when the server must outlive or be shared across clients.

---

**Q3: What is the Sampling primitive's full request flow and why does it make servers model-agnostic?** `[Medium]`

A: When a Server needs LLM-generated text, it sends a `sampling/createMessage` request to the Client, which forwards it to the Host, which routes it to the underlying LLM. The LLM generates a response that travels back: LLM → Host → Client → Server. The Server never knows which model was used — it specifies preferences (speed vs. quality, context budget) but the Host chooses the actual model. This means the same MCP server works with Claude, GPT-4, or any future model without modification, because the "intelligence layer" is permanently abstracted behind the Host boundary.

---

**Q4: How does MCP push capability updates without polling, and what breaks if a client ignores `notifications/tools/list_changed`?** `[Hard]`

A: MCP is stateful — when a server's capabilities change (a plugin loads, permissions are granted, a tool is removed), it immediately sends `notifications/tools/list_changed` to the client. The client responds with a `tools/list` request to fetch the updated manifest. Without this, the client retains a stale tool list: the LLM may attempt to call tools that no longer exist (receiving runtime errors), or miss newly available tools that would have improved its response. In agentic systems mid-task, a stale tool list can cause plan failure if a required tool was removed or a needed tool only became available after the plan was formed.

---

**Q5: How does JSON-RPC 2.0's error model differ from HTTP status codes, and why does MCP use it?** `[Hard]`

A: JSON-RPC 2.0 errors are structured objects with three fields: `code` (integer in a defined range), `message` (human-readable string), and optional `data` (machine-readable detail). Unlike HTTP where errors live in the transport layer (status codes) and can be intercepted, rewritten, or lost in proxies, JSON-RPC errors travel inside the response payload and always reach the application layer intact. For MCP, this matters because tool execution errors — "file not found", "permission denied", "rate limited", "invalid query" — need structured representation that the LLM can reason about. A raw HTTP 500 gives the LLM no actionable information; a JSON-RPC error with code and data gives it enough context to retry, replan, or escalate.

---

**Q6: How does MCP's design limit what a compromised MCP server can do?** `[Hard]`

A: MCP has several defense layers: (1) capability negotiation — the Host only enables features it explicitly declared; a server cannot use Sampling if the Host didn't claim it. (2) The Host mediates all Sampling and Elicitation — a server cannot directly call the LLM or the user; every such request flows through the Host, which can inspect and reject it. (3) Tool and Resource declarations are advisory — the Host can choose not to surface specific tools to the LLM even if the server offers them. (4) Each Client connection is isolated — a compromised server cannot read other Clients' state or messages. The remaining attack vector is tool description prompt injection: a malicious server can craft descriptions that manipulate LLM behavior, which is why Hosts should treat server-provided content as untrusted input and apply sanitization before including it in the context window.