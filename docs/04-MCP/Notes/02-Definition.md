# 📖 Definition (MCP)

[← Back to Index](../INDEX.md)

## What is MCP?

**Model Context Protocol (MCP)** is an open standard that enables developers to build secure, two-way connections between their data sources and AI-powered tools.

## Architecture Overview

The architecture is straightforward:

- **Server-side:** Developers can expose their data through **MCP servers**
- **Client-side:** Developers can build AI applications (**MCP clients**) that connect to these servers
- **Two-way communication:** Secure, standardized data exchange between systems

## Visual Representation

![Model Context Protocol Diagram](./mcp-img-assets/mcp-simple-diagram.avif)

## Key Definition Points

- MCP is an **open-source standard** for connecting AI applications to external systems
- It enables **secure, two-way connections**
- It works between **data sources** and **AI-powered tools**
- Built on a **standardized protocol** for consistency across implementations

---

## Detailed Exploration

*Add your detailed notes here as you learn more about MCP's architecture and design principles...*

---

**Related Topics:**
- [The Solution →](03-The-Solution.md)
- [Components →](04-Components.md)
- [Getting Started →](08-Getting-Started.md)

---

## Q&A Review Bank

**Q1: Define MCP and identify its two communication endpoints.** `[Easy]`

A: MCP (Model Context Protocol) is an open standard that enables secure, bidirectional communication between AI applications and external data or capability providers. The two endpoints are the Client side — the AI application, managed by a Host — and the Server side — the program that exposes tools, resources, or prompts for a specific data source or service. The protocol defines how these two sides discover each other's capabilities, negotiate a session, and exchange messages.

---

**Q2: What does "open standard" mean for MCP adoption, and why does it matter more than a proprietary protocol?** `[Medium]`

A: An open standard is a publicly available specification that any party can implement without licensing fees or vendor lock-in. For MCP, this means a server built by any company works immediately with every compliant MCP client — including those built by competitors. The network effect is the key driver: each new MCP server adds value to every existing client, and each new client adds value to every existing server. A proprietary protocol owned by one vendor creates fragmentation; an open standard creates a shared infrastructure where every participant benefits from every other participant's investment.

---

**Q3: What transport protocols does MCP support and when is each appropriate?** `[Medium]`

A: MCP supports two transports: Stdio (standard input/output) and Streamable HTTP. Stdio is used when the MCP server runs as a local subprocess on the same machine — communication happens via stdin/stdout with zero network overhead, making it ideal for development, desktop integrations, and local tools. Streamable HTTP uses HTTP POST for client-to-server messages and Server-Sent Events (SSE) for server-to-client streaming; it's appropriate for remotely deployed servers, multi-tenant environments, and servers that need independent scaling or shared access across many clients.

---

**Q4: Why does MCP use JSON-RPC 2.0 rather than REST as its data-layer protocol?** `[Hard]`

A: JSON-RPC 2.0 is bidirectional and session-oriented — unlike REST, which is stateless and request/response only. MCP sessions require both sides to initiate messages: servers send notifications and progress updates; clients send requests and receive streaming events. REST cannot naturally express this without webhooks, which introduce their own complexity. JSON-RPC also provides structured error objects (code, message, data) with standardized error codes, deterministic request-response correlation via IDs, and clean separation between protocol-level errors and application-level errors — all of which map well to tool invocation and capability notification patterns.

---

**Q5: What is capability negotiation and what happens if client and server declare incompatible versions?** `[Hard]`

A: During the initialization handshake the client sends its supported protocol version and capability set; the server responds with its own version and capabilities. The session proceeds using only the features both sides declared support for — a server won't offer Sampling if the client didn't claim it. If the client requests a protocol version the server doesn't recognize, the server rejects the initialize request and the connection fails with an error. This design ensures older clients aren't exposed to features they can't handle, and newer servers can negotiate down to older protocol versions for backward compatibility — without either side silently misinterpreting messages.
