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