# MCP Components: Host, Client, Server

← **Back to Overview:** [MCP](../INDEX.md)

---

## The Three Roles

Every MCP interaction involves exactly three roles. Understanding the boundary between them is the key to designing correct MCP systems.

```
┌──────────────────────────────────┐
│           MCP HOST               │
│  (e.g., Claude Desktop, VS Code) │
│                                  │
│  ┌──────────┐  ┌──────────┐     │
│  │ Client 1 │  │ Client 2 │ ... │
│  └────┬─────┘  └────┬─────┘     │
└───────┼─────────────┼────────────┘
        │             │
        ▼             ▼
 ┌──────────┐  ┌──────────┐
 │ Server A │  │ Server B │
 │ (GitHub) │  │(Postgres)│
 └──────────┘  └──────────┘
```

---

## MCP Host

The Host is the **user-facing application** that houses the AI model and manages the overall session. Examples: Claude Desktop, Claude.ai, VS Code with an AI extension, Cursor.

**Responsibilities:**

- Creates and supervises one or more Client instances
- Manages capability declarations for all clients
- Routes Sampling requests from servers to the underlying LLM
- Surfaces Elicitation requests from servers to the user
- Enforces security policies (which servers are trusted, which capabilities are granted)
- Maintains the session lifecycle

**Critical insight:** The Host is the security boundary. It controls what each server can access, mediates all server interactions with the LLM and the user, and decides which capabilities to declare during initialization. A server cannot bypass the Host to reach the LLM or the user directly.

---

## MCP Client

The Client is a **protocol component** created by the Host to manage a dedicated connection to one specific Server.

**One Client = One Server connection.**

**Responsibilities:**

- Maintains a stateful JSON-RPC session with one Server
- Sends initialization handshake and declares capabilities
- Sends requests (tool calls, resource reads, prompt gets) and receives responses
- Listens for server notifications and triggers appropriate refreshes
- Handles transport-level concerns (reconnect, session ID, progress tokens)

**Why separate from the Host?**

The Host manages N simultaneous Client connections. Separating Host from Client lets the Host fan out across multiple servers without multiplexing logic: each Client handles its own connection lifecycle independently. The Host can add or drop connections at runtime without disrupting others.

---

## MCP Server

The Server is an **independent program** that exposes capabilities for a specific data source or service.

**Responsibilities:**

- Implements the MCP server-side protocol (responds to `initialize`, `tools/list`, `tools/call`, etc.)
- Exposes its capabilities: tools, resources, prompts
- May use client-side primitives if the Host declared support (Sampling, Elicitation)
- Sends notifications when its capabilities change

**What the Server does NOT know:**

- Which AI model the Host is running
- Which other Servers the Host is connected to
- The Host's internal application state
- The user's identity (unless the server implements its own auth)

Servers are designed as **pluggable, independent components**. A GitHub MCP server written today should work with any MCP Host, current or future.

---

## Capability Declarations

During initialization, both sides declare their capabilities. This is the contract for the session.

### Server capability declaration examples:

```json
{
  "capabilities": {
    "tools": {
      "listChanged": true
    },
    "resources": {
      "subscribe": true,
      "listChanged": true
    },
    "prompts": {
      "listChanged": true
    },
    "logging": {}
  }
}
```

- `tools.listChanged`: Server will send `notifications/tools/list_changed` when its tool list changes
- `resources.subscribe`: Server supports per-resource subscriptions (client can watch individual resources for changes)
- `resources.listChanged`: Server will notify when the list of available resources changes
- `logging`: Server can send log messages to the Host

### Client capability declaration examples:

```json
{
  "capabilities": {
    "sampling": {},
    "elicitation": {},
    "roots": {
      "listChanged": true
    }
  }
}
```

- `sampling`: Host can handle `sampling/createMessage` requests from the server
- `elicitation`: Host can surface `elicitation/create` requests to the user
- `roots.listChanged`: Client will send `notifications/roots/list_changed` when workspace changes

**If a capability is not declared, it MUST NOT be used.** A server that sends a Sampling request when the client didn't declare `sampling` support receives a protocol error.

---

## The Initialization Handshake

Every MCP session starts with a three-step handshake:

### Step 1: Initialize Request (Client → Server)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "sampling": {},
      "roots": { "listChanged": true }
    },
    "clientInfo": {
      "name": "ClaudeDesktop",
      "version": "1.2.0"
    }
  }
}
```

### Step 2: Initialize Response (Server → Client)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": { "listChanged": true },
      "resources": { "subscribe": true }
    },
    "serverInfo": {
      "name": "github-mcp-server",
      "version": "0.4.1"
    }
  }
}
```

### Step 3: Initialized Notification (Client → Server)

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

After this three-step exchange, the session is **active**. The client now knows:
- The server's protocol version
- Which server capabilities to use
- The server's name and version (for display and audit logging)

If the server rejects the protocol version, it sends a JSON-RPC error in Step 2 and the connection fails before any data exchange.

---

## Session Lifecycle States

```
CONNECTING
    ↓ (initialize request sent)
INITIALIZING
    ↓ (initialize response received + initialized notification sent)
ACTIVE ←──────────────────────────────────────────────────┐
    │  (tool calls, resource reads, notifications, etc.)   │
    │                                                       │
    ↓ (either side closes transport)                        │
TERMINATED                                                  │
                                                            │
    [Reconnect if desired] ─────────────────────────────────┘
```

There is no "pause" state — a dropped connection means full re-initialization on reconnect. In-flight requests at disconnection are lost.

---

## The Ecosystem Components

Beyond Host/Client/Server, the MCP ecosystem has three supporting components:

### 1. Protocol Specification

The official spec defines every message format, error code, capability flag, and behavioral requirement. Available at [modelcontextprotocol.io](https://modelcontextprotocol.io) and versioned (e.g., `2025-03-26`).

### 2. Official SDKs

SDKs translate the spec into idiomatic libraries:

| Language | SDK | Best For |
|----------|-----|---------|
| Python | `mcp` | Data science, ML pipelines, data tools |
| TypeScript | `@modelcontextprotocol/sdk` | Web services, Node.js tools |
| Go | `mcp-go` | Performance-critical, cloud services |
| Java/Kotlin | Community SDKs | Enterprise, Android |
| C# | Community SDKs | .NET ecosystem |

SDKs handle the JSON-RPC framing, capability negotiation, and message routing automatically — you write business logic, not protocol code.

### 3. Community Server Repository

The [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) GitHub repository contains ready-to-use server implementations for common systems: filesystem, Git, GitHub, Slack, PostgreSQL, SQLite, Google Drive, Brave Search, and many more.

---

**Related Topics:**
- [Definition →](02-Definition.md)
- [Capabilities →](05-Capabilities.md)
- [Architecture Deep-Dive →](07-Architecture-Deep-Dive.md)

---

## Q&A Review Bank

**Q1: Describe the Host, Client, and Server roles in one sentence each.** `[Easy]`

A: The Host is the user-facing AI application that manages all client connections, enforces security policies, and mediates interactions between servers and the LLM/user. Each Client maintains a dedicated stateful JSON-RPC connection to exactly one Server and handles the protocol mechanics for that connection. The Server is an independent program that exposes tools, resources, and prompts for a specific data source — it has no knowledge of the Host's application logic or other Server connections.

---

**Q2: Why does MCP separate Host from Client rather than merging them?** `[Medium]`

A: A Host typically manages simultaneous connections to multiple Servers. By separating Host from Client, the architecture allows one Host to fan out across N independent Client connections — each managing its own stateful session lifecycle, capability set, and message flow without coupling to other connections. If merged, the Host would need to multiplex all inbound and outbound messages across all servers, making the code complex and making it harder to add or drop connections at runtime. The separation also makes it possible for different Client implementations to serve different Server types without changing Host code.

---

**Q3: What happens during the initialized notification (step 3 of the handshake) and what would break if it were skipped?** `[Medium]`

A: The `notifications/initialized` notification signals to the Server that the Client has received and accepted the initialize response and is ready to begin normal operations. If skipped, the Server would be in an ambiguous state — it responded to `initialize` but doesn't know if the Client processed it successfully. Well-implemented servers will not send capabilities-dependent messages (like `notifications/tools/list_changed`) until they receive `initialized`. A missing `initialized` notification can cause servers to either hang waiting or proceed immediately, both of which can cause subtle ordering bugs where tool list notifications arrive before the client has set up its listener.

---

**Q4: What capability flags does a server need to declare to support real-time resource change notifications?** `[Hard]`

A: Two distinct flags cover different notification types. `resources.listChanged: true` means the server will send `notifications/resources/list_changed` when the *set* of available resources changes (a new file appears, a database table is dropped). `resources.subscribe: true` means clients can call `resources/subscribe` with a specific resource URI, and the server will send `notifications/resources/updated` with that URI whenever that specific resource's *content* changes. A client that supports persistent context (e.g., an IDE watching a file) needs both: `listChanged` to discover new/removed resources, and `subscribe` to get live updates on resources it's actively using.

---

**Q5: A server sends `sampling/createMessage` but the client never declared the `sampling` capability. What should happen and what does this reveal about the security model?** `[Hard]`

A: The Client should return a JSON-RPC error with code `-32601` (Method Not Found) or a similar "unsupported capability" error, because the server is attempting to use a feature the client never agreed to support. This scenario reveals the security model's core mechanism: capability declarations during initialization are a binding contract, not advisory documentation. A server that attempts to use undeclared capabilities is either misconfigured (a bug) or malicious (attempting to use a capability it wasn't granted). The Host is responsible for detecting this pattern and potentially terminating the connection if a server repeatedly attempts unauthorized capability use.
