# Interview Q&A — MCP (Model Context Protocol)

## Conceptual Questions

**Q: What exactly is the Model Context Protocol?**
MCP is an open standard (originally from Anthropic) that defines a universal interface between LLM applications (hosts) and external data/tool providers (servers). Think of it as "USB-C for AI integrations" — instead of every AI application building custom connectors for every tool, both sides implement MCP once and interoperate. The protocol covers tool invocation, resource access, prompts, and sampling.

**Q: What problem does MCP solve?**
The N×M integration problem. Without MCP, connecting N AI applications to M data sources requires N×M custom integrations. With MCP, each data source builds one MCP server, each AI application builds one MCP host client — reducing to N+M integrations. It also standardizes the interface so servers built for one LLM host work with any other.

**Q: How is MCP different from function calling?**
Function calling is a model-level mechanism — the LLM outputs a structured JSON call, your application executes it. It's one-directional and requires you to write custom integration logic for every tool. MCP is a full bidirectional protocol with: defined message formats, capability negotiation, resource streaming, built-in lifecycle management, and a server ecosystem. MCP uses function calling internally but adds the protocol layer on top.

**Q: Who implements MCP servers vs hosts?**
Servers: developers who own data sources or tools (e.g., a company exposing its database, a SaaS product exposing its API). Servers are published once and reused. Hosts: LLM application developers (e.g., Claude Desktop, IDEs, custom chat UIs). Hosts discover and connect to servers. End users benefit without needing to understand the protocol.

---

## Architecture Questions

**Q: What are the three main MCP primitives?**
(1) **Tools**: functions the LLM can invoke — e.g., run a database query, call an API. (2) **Resources**: data sources the server exposes for the LLM to read — e.g., file contents, database records. Resources are URI-addressable. (3) **Prompts**: reusable prompt templates the server can provide — e.g., a standard code review prompt. Together these cover actions, data, and guidance.

**Q: How does the MCP client-server architecture work?**
The host application runs an MCP client. When the user makes a request that needs external data or tools, the LLM decides which MCP server to contact. The client sends JSON-RPC messages to the server (over stdio, HTTP, or WebSocket). The server processes the request and returns results. The LLM incorporates the results into its response. The host manages the lifecycle of server connections.

**Q: What transport protocols does MCP use?**
MCP uses JSON-RPC 2.0 as the message format over three transport options: (1) stdio — for local servers running as child processes; (2) HTTP with SSE (Server-Sent Events) — for remote servers; (3) WebSocket — for bidirectional streaming. The transport is abstracted from the application logic.

---

## Implementation Questions

**Q: What are the steps to build an MCP server?**
(1) Choose SDK (official SDKs for Python, TypeScript). (2) Define your tools: name, description, input schema (JSON Schema). (3) Implement tool handlers — the actual logic that executes when the tool is called. (4) Define resources (optional): URIs, MIME types, and read handlers. (5) Register server and start transport. (6) Test with MCP Inspector or a compatible host.

**Q: What security considerations apply to MCP?**
(1) Authentication — MCP servers should require credentials (API keys, OAuth tokens) passed by the host. (2) Authorization — servers should enforce least-privilege. (3) Input validation — tool arguments come from an LLM; validate them before executing. (4) Prompt injection via resources — malicious content in a returned resource could attempt to override LLM instructions. (5) Scope control — define which tools are available to which hosts/users.

**Q: Can MCP be used with models other than Claude?**
Yes. MCP is model-agnostic — it's a protocol between applications and data sources, not between a specific LLM and tools. Any LLM application that implements the MCP host interface can connect to any MCP server. This model-agnosticism is a key design goal.

---

## Scenario Questions

**Q: How would you design an MCP server for an enterprise database?**
Define tools for each operation: `query_database(sql)`, `list_tables()`, `describe_table(name)`. Implement authorization: only allow read operations for AI use, require a service account, enforce row-level security. Add resources: expose schema documentation as readable resources. Add rate limiting and connection pooling. Consider a query allow-list to prevent dangerous operations.

**Q: When would you choose MCP over direct function calling?**
Choose MCP when: (1) you want tools reusable across multiple AI applications; (2) you're building a tool/data ecosystem others will use; (3) you want standardized capability discovery and lifecycle management. Choose direct function calling for: simple app-specific tools that won't be shared, or when the MCP protocol overhead isn't justified.
