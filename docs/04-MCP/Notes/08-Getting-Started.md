# Getting Started with MCP

← **Back to Overview:** [MCP](../INDEX.md)

---

## Prerequisites

Before building MCP servers, you need:

- **Python 3.10+** or **Node.js 18+** (TypeScript)
- Familiarity with async programming in your chosen language
- A working installation of Claude Desktop (for testing) or access to another MCP Host
- Basic understanding of JSON and REST APIs

---

## Learning Path

### Phase 1: Foundation (Week 1)
- [ ] [The Problem](01-The-Problem.md) — understand what MCP solves
- [ ] [Definition](02-Definition.md) — what MCP is and how it works
- [ ] [The Solution](03-The-Solution.md) — primitives overview
- [ ] [Components](04-Components.md) — Host/Client/Server roles

### Phase 2: Deep Dive (Week 2)
- [ ] [Capabilities](05-Capabilities.md) — all 6 primitives in detail
- [ ] [Architecture Deep-Dive](07-Architecture-Deep-Dive.md) — transport, JSON-RPC, security
- [ ] Read through the official Python SDK source code

### Phase 3: Build (Weeks 3-4)
- [ ] Build a minimal tool-only server (below)
- [ ] Add a Resource to your server
- [ ] Add a Prompt to your server
- [ ] Test with Claude Desktop or MCP Inspector

### Phase 4: Production (Week 5+)
- [ ] Add authentication (HTTP server)
- [ ] Add input validation and error handling
- [ ] Add logging and observability
- [ ] Deploy as HTTP server with proper security

---

## Installation

### Python SDK
```bash
pip install mcp
# or with uv (recommended):
uv add mcp
```

### TypeScript SDK
```bash
npm install @modelcontextprotocol/sdk
# or:
yarn add @modelcontextprotocol/sdk
```

---

## Building Your First Server (Python)

### Minimal tool-only server

```python
# server.py
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Create the server
app = Server("my-first-server")

# Register a tool
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="add_numbers",
            description="Adds two numbers together and returns the result.",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        )
    ]

# Handle tool calls
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "add_numbers":
        result = arguments["a"] + arguments["b"]
        return [types.TextContent(type="text", text=f"Result: {result}")]
    raise ValueError(f"Unknown tool: {name}")

# Start the server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python server.py
```

### Add a Resource

```python
@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="file:///app/status",
            name="Application Status",
            description="Current application health and metrics",
            mimeType="application/json",
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "file:///app/status":
        import json
        return json.dumps({"status": "healthy", "uptime_seconds": 3600, "version": "1.0.0"})
    raise ValueError(f"Unknown resource: {uri}")
```

### Add a Prompt

```python
@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="analyze_number",
            description="Analyzes a number and provides interesting facts about it",
            arguments=[
                types.PromptArgument(
                    name="number",
                    description="The number to analyze",
                    required=True,
                )
            ],
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    if name == "analyze_number":
        number = arguments.get("number", "0")
        return types.GetPromptResult(
            description=f"Analysis prompt for {number}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Analyze the number {number}. Is it prime? What are its factors? Any interesting mathematical properties?",
                    ),
                )
            ],
        )
    raise ValueError(f"Unknown prompt: {name}")
```

---

## Building Your First Server (TypeScript)

```typescript
// server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-first-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "add_numbers",
      description: "Adds two numbers together.",
      inputSchema: {
        type: "object",
        properties: {
          a: { type: "number", description: "First number" },
          b: { type: "number", description: "Second number" },
        },
        required: ["a", "b"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "add_numbers") {
    const { a, b } = request.params.arguments as { a: number; b: number };
    return {
      content: [{ type: "text", text: `Result: ${a + b}` }],
      isError: false,
    };
  }
  throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
});

// Start
const transport = new StdioServerTransport();
await server.connect(transport);
```

```bash
npx ts-node server.ts
```

---

## Connecting to Claude Desktop

Add your server to Claude Desktop's configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-first-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

For TypeScript:
```json
{
  "mcpServers": {
    "my-ts-server": {
      "command": "node",
      "args": ["/absolute/path/to/dist/server.js"]
    }
  }
}
```

Restart Claude Desktop and look for the 🔌 icon in the chat interface — it indicates active MCP connections.

---

## Testing with MCP Inspector

MCP Inspector is the official debugging tool — it lets you interactively test your server without a full Host.

```bash
npx @modelcontextprotocol/inspector python /path/to/server.py
```

Opens a web UI at `http://localhost:6274` where you can:
- View the initialization handshake
- Browse discovered tools, resources, prompts
- Invoke tools and see raw JSON-RPC messages
- Monitor notifications in real-time
- Test error handling

**Invaluable for debugging:** Always test with Inspector before connecting to Claude Desktop.

---

## Adding Error Handling

### Tool execution errors (use `isError`)
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_database":
        try:
            result = await db.execute(arguments["sql"])
            return [types.TextContent(type="text", text=str(result))]
        except PermissionError as e:
            # Tool ran, but execution failed — use isError
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Permission denied: {e}")],
                isError=True,
            )
        except ValueError as e:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Invalid query: {e}")],
                isError=True,
            )
```

### Protocol errors (raise exceptions)
```python
    # This tool name doesn't exist — raise a protocol error
    raise ValueError(f"Unknown tool: {name}")
    # SDK converts this to a JSON-RPC error response
```

---

## Adding Input Validation

Always validate tool inputs before executing business logic:

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "send_email":
        # Validate required fields
        if "to" not in arguments:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="Missing required field: 'to'")],
                isError=True,
            )
        
        # Validate format
        if not "@" in arguments["to"]:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="Invalid email format")],
                isError=True,
            )
        
        # Validate length
        if len(arguments.get("body", "")) > 10000:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="Email body exceeds 10,000 character limit")],
                isError=True,
            )
        
        # Execute
        ...
```

---

## Common Debugging Issues

### Issue 1: Server doesn't appear in Claude Desktop

**Symptom:** No 🔌 icon or server not listed in Claude Desktop.

**Checks:**
1. Is the path in `claude_desktop_config.json` absolute and correct?
2. Does `python server.py` work when run manually in the terminal?
3. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log` (macOS)
4. Is the server writing to stdout? (Any print statement breaks the stream)

### Issue 2: Tools not appearing

**Symptom:** Server connects but Claude can't see tools.

**Checks:**
1. Did you declare `"tools": {}` in your capabilities during initialization?
2. Does `tools/list` return a valid response? Test with MCP Inspector.
3. Are tool `inputSchema` objects valid JSON Schema?

### Issue 3: Tool calls fail silently

**Symptom:** Tool is invoked but returns no result or crashes.

**Checks:**
1. Are you returning `[types.TextContent(...)]` or `types.CallToolResult(...)`?
2. Wrap your handler in try/except and return `isError: true` with the error message
3. Check stderr output — SDK errors appear there

### Issue 4: Stdio transport broken by print statements

**Symptom:** Server crashes immediately or produces garbled output.

**Fix:**
```python
import sys

# Wrong — breaks stdio transport:
print("Server starting...")

# Correct — goes to stderr, not stdout:
print("Server starting...", file=sys.stderr)
```

### Issue 5: HTTP server returns 404 after reconnect

**Symptom:** Works initially, fails after a network interruption.

**Fix:** Check that your client is sending the `Mcp-Session-Id` header on reconnect. The session ID from the initial `initialize` response must be echoed on all subsequent requests.

---

## Project Ideas

### Beginner
- **File summarizer:** Resource reads local files; Tool invokes Sampling to summarize
- **Calculator:** Tools for arithmetic, algebra, and unit conversion
- **Todo list:** In-memory CRUD tools (`add_todo`, `list_todos`, `complete_todo`)

### Intermediate
- **Database explorer:** Resources expose table schemas; Tools execute validated queries
- **Git assistant:** Tools for `git log`, `git diff`, `git blame`; Resources expose repo structure
- **API proxy:** Wraps a REST API (weather, news, etc.) as MCP tools with caching

### Advanced
- **Multi-source search:** Fan-out tool that searches GitHub, Slack, and Confluence simultaneously
- **Code review server:** Uses Sampling to analyze diffs; Elicitation for reviewer confirmation
- **Audit-logged enterprise server:** Full auth, per-tool RBAC, structured audit logging to a SIEM

---

**Related Topics:**
- [Q&A Review Bank →](09-QA-Review-Bank.md)
- [Definition →](02-Definition.md)
- [Components →](04-Components.md)
- [Capabilities →](05-Capabilities.md)

---

## Progress Tracking

| Phase | Topic | Status |
|-------|-------|--------|
| Foundation | Problem & Definition | ⬜ |
| Foundation | Solution & Components | ⬜ |
| Foundation | Capabilities | ⬜ |
| Deep Dive | Architecture | ⬜ |
| Build | First Tool Server | ⬜ |
| Build | Add Resource | ⬜ |
| Build | Add Prompt | ⬜ |
| Build | Test with Inspector | ⬜ |
| Production | Auth + Security | ⬜ |
| Production | Logging + Monitoring | ⬜ |

---

## Q&A Review Bank

**Q1: What are the key steps to build a minimal working MCP server in Python?** `[Easy]`

A: (1) Install the MCP SDK (`pip install mcp`). (2) Create a `Server` instance with a name. (3) Register a `list_tools()` handler that returns tool definitions with name, description, and inputSchema. (4) Register a `call_tool()` handler that executes the logic and returns `TextContent` results. (5) Run the server with `stdio_server()` for local development. The SDK handles all JSON-RPC framing, capability negotiation, and lifecycle management — you only write the tool definitions and handler functions.

---

**Q2: What is MCP Inspector and when should you use it?** `[Medium]`

A: MCP Inspector is the official debugging tool that lets you interactively test an MCP server without a full Host application. Run `npx @modelcontextprotocol/inspector python server.py` and it opens a web UI showing the initialization handshake, discovered tools/resources/prompts, raw JSON-RPC messages, and real-time notifications. Use it before connecting to Claude Desktop to verify your server's tool definitions are correct, error handling works, and input schemas validate properly. It's the fastest way to catch schema mismatches and malformed responses that would be opaque errors inside Claude Desktop.

---

**Q3: What is the single most common mistake that breaks stdio MCP servers?** `[Medium]`

A: Writing to stdout from application code (e.g., `print("Server starting...")` in Python). The stdio transport is newline-delimited JSON — every byte on stdout is expected to be a JSON-RPC message. A stray `print` statement corrupts the stream, causing the client's JSON parser to fail on the first message, which appears as "server crashed immediately" with no useful error. The fix is to always redirect debug output to stderr: `print("debug message", file=sys.stderr)`. This is the first thing to check when a server fails to appear in Claude Desktop.

---

**Q4: How should you handle a tool execution failure vs. an unexpected exception in a tool handler?** `[Hard]`

A: Tool execution failures (expected business logic failures: file not found, permission denied, invalid query result) should return a `CallToolResult` with `isError=True` and a descriptive error message in the content — this is information the LLM can reason about and potentially recover from. Unexpected exceptions (unhandled errors, assertion failures, crashes) should be caught at the outermost handler level and also returned as `isError=True` with a sanitized message — never let raw exception tracebacks reach the LLM (they may contain file paths, internal state, or PII). Protocol-level failures (unknown tool name, malformed request) should raise exceptions that the SDK converts to JSON-RPC error responses. Three levels, three handling strategies.

---

**Q5: How would you build a production-grade MCP server for an enterprise database with multi-tenant access control?** `[Hard]`

A: Deploy as an HTTP server (not stdio) so multiple clients can share connection pools. Implement OAuth 2.0 on the HTTP layer for authentication — validate tokens on every request, not just at session init. In each tool handler, extract the authenticated user identity from the session context and apply row-level access control before executing queries (use Postgres's `SET LOCAL role` or equivalent to run queries as the authenticated user, not a shared service account). Validate all SQL inputs against a strict allowlist of operations (no DDL, bounded result sets). Add per-session rate limiting to prevent query floods. Implement structured audit logging: every tool invocation, user identity, query parameters, row count returned, and execution duration — sent both to application logs and to the MCP Logging primitive for Host-side visibility. Return only the fields the LLM needs in results, not full raw rows.
