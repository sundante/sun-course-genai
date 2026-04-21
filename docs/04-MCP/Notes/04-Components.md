# 🔧 Three Major Components of MCP

[← Back to Index](../INDEX.md)

## Component 1: MCP Specifications and SDKs

**Link:** [GitHub - MCP Specifications](https://github.com/modelcontextprotocol)

- Comprehensive protocol specifications
- Official Software Development Kits
- Language bindings and implementations
- Best practices and standards documentation

### Details
*Add your notes about specifications and SDKs here...*

---

## Component 2: MCP Open Source Repository

**Link:** [GitHub - MCP Servers](https://github.com/modelcontextprotocol/servers)

- Collection of ready-to-use MCP server implementations
- Reference implementations for various data sources
- Community-contributed servers
- Examples and templates for building new servers

### Details
*Add your notes about open source repositories here...*

---

## Component 3: MCP Support for Desktop LLM Apps

- Integration with desktop LLM applications
- Claude integration support
- Local LLM compatibility
- Easy connection to local data sources and tools

### Details
*Add your notes about desktop LLM app support here...*

---

## Ecosystem Overview

These three components work together to create a complete ecosystem:

```
Specifications & SDKs
        ↓
    (Define how)
        ↓
Open Source Servers + Desktop Apps
        ↓
    (Connect to)
        ↓
Data Sources & AI Tools
```

---

## Detailed Exploration

*Add your detailed notes here as you explore each component in depth...*

---

**Related Topics:**
- [Definition →](02-Definition.md)
- [Capabilities →](05-Capabilities.md)
- [Getting Started →](08-Getting-Started.md)

---

## Q&A Review Bank

**Q1: Describe the distinct roles of MCP Host, MCP Client, and MCP Server.** `[Easy]`

A: The Host is the user-facing application (e.g., Claude Desktop, VS Code) that houses the AI model, manages the overall session, and creates/supervises Client instances. Each Client maintains a dedicated, stateful connection to one MCP Server and handles the JSON-RPC message exchange for that connection. The Server is an independent program that exposes capabilities (tools, resources, prompts) for a specific data source or service — it knows nothing about the Host's application logic and communicates only through the MCP protocol.

---

**Q2: Why does MCP separate the Host from the Client instead of merging them?** `[Medium]`

A: A single Host typically needs connections to multiple Servers simultaneously — a file server, a calendar server, and a database server all active at once. By separating Host from Client, MCP allows one Host to fan out across N independent Client connections, each managing its own stateful session to a different Server. If merged, the Host would need to multiplex and demultiplex all messages itself, introducing coupling and complexity. The separation also means the Host can add or drop Server connections at runtime without disrupting active sessions on other Servers.

---

**Q3: What role do SDKs play in MCP adoption and why do they matter more than just the specification?** `[Medium]`

A: The specification defines the full protocol: message formats, primitive types, transport requirements, lifecycle, error codes, and capability flags — it's the authoritative contract. SDKs (available in Python, TypeScript, Go, and others) translate that spec into idiomatic, ready-to-use libraries, so developers write application logic rather than raw JSON-RPC. SDK adoption is a key adoption driver because it lowers the barrier from "implement a complex stateful protocol" to "call three functions." Most production MCP servers are built on official SDKs, not from-scratch implementations — the SDK quality directly determines how many servers get built and maintained.

---

**Q4: When would you build a custom MCP server versus using one from the open-source repository?** `[Hard]`

A: Use an existing community server for well-known systems (GitHub, Slack, Google Drive, Postgres) — they handle auth, pagination, and edge cases you'd re-solve. Build custom when: (1) the data source is proprietary or internal with no existing MCP server; (2) the existing server doesn't expose the specific tools or resource shapes your use case requires; (3) you need custom security policies, rate limiting, or data transformation that can't be bolted onto a generic server; or (4) you need to compose multiple APIs into a single coherent server with a unified data model. Custom servers are also appropriate when you need fine-grained control over what fields are surfaced to the LLM — minimizing context waste and reducing prompt injection attack surface.

---

**Q5: How should a Host maintain security isolation between multiple simultaneous Client-Server connections?** `[Hard]`

A: Each Client connection should operate in its own sandbox — the Host must not share authentication tokens, session state, or tool results between different Server connections unless explicitly designed to do so. The MCP spec treats each Server as an untrusted third party: capability negotiation defines exactly what a server can request, Elicitation gates are surfaced to the user rather than auto-approved, and per-server permission models are established at setup time. In practice this means separate credential stores per Server, audit logging at each Client boundary so unexpected capability requests are visible, and process isolation for local stdio servers to prevent one compromised server from reading another server's I/O.
