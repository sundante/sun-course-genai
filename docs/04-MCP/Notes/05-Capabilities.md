# MCP Capabilities: All Six Primitives

← **Back to Overview:** [MCP](../INDEX.md)

---

## Overview: The Six Primitives

MCP defines six primitive types that cover every kind of AI-data interaction:

```
Server-side (servers expose TO clients)
├── Tools      → executable functions (model-controlled)
├── Resources  → readable data (app-controlled)
└── Prompts    → reusable templates (user-controlled)

Client-side (clients expose BACK to servers)
├── Sampling   → LLM text generation
├── Elicitation → user input / confirmation
└── Roots      → filesystem access boundaries
```

Each primitive has a discovery mechanism (`list`), an access mechanism (`get`/`call`/`read`), and optional change notifications.

---

## 1. Tools

Tools are the most powerful and consequential primitive. They are executable functions that may have **side effects** — writing data, calling external APIs, modifying system state.

### Capability declaration
```json
{ "capabilities": { "tools": { "listChanged": true } } }
```

### Discovery: tools/list
```json
// Request
{ "jsonrpc": "2.0", "id": 2, "method": "tools/list" }

// Response
{
  "result": {
    "tools": [
      {
        "name": "create_github_issue",
        "title": "Create GitHub Issue",
        "description": "Creates a new issue in a GitHub repository.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "owner": { "type": "string", "description": "Repository owner" },
            "repo":  { "type": "string", "description": "Repository name" },
            "title": { "type": "string", "description": "Issue title" },
            "body":  { "type": "string", "description": "Issue body (markdown)" },
            "labels": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["owner", "repo", "title"]
        },
        "outputSchema": {
          "type": "object",
          "properties": {
            "issue_number": { "type": "integer" },
            "url": { "type": "string" }
          }
        }
      }
    ]
  }
}
```

### Invocation: tools/call
```json
// Request
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "create_github_issue",
    "arguments": {
      "owner": "my-org",
      "repo": "my-app",
      "title": "Button misaligned on mobile",
      "body": "## Steps to reproduce\n1. Open on iOS\n2. Tap settings\n\nExpected: button centered\nActual: button clipped",
      "labels": ["bug", "mobile"]
    }
  }
}

// Success response
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Issue #147 created successfully."
      }
    ],
    "structuredContent": {
      "issue_number": 147,
      "url": "https://github.com/my-org/my-app/issues/147"
    },
    "isError": false
  }
}

// Tool execution error (NOT a protocol error)
{
  "result": {
    "content": [
      { "type": "text", "text": "Error: Repository not found or insufficient permissions." }
    ],
    "isError": true
  }
}
```

### Tool Result Content Types

| Type | Fields | Use Case |
|------|--------|---------|
| `text` | `text: string` | Text output, logs, messages |
| `image` | `data: base64`, `mimeType` | Screenshots, charts, diagrams |
| `audio` | `data: base64`, `mimeType` | Audio output |
| `resource_link` | `uri`, `name`, `mimeType` | Pointer to a resource |
| `resource` (embedded) | full resource object | Inline resource content |

### Tool Annotations

Tools can carry behavioral hints via annotations:

```json
{
  "annotations": {
    "title": "Delete All Records",
    "readOnlyHint": false,
    "destructiveHint": true,
    "idempotentHint": false,
    "openWorldHint": false
  }
}
```

| Annotation | Meaning |
|------------|---------|
| `readOnlyHint: true` | Tool only reads, never writes |
| `destructiveHint: true` | Tool may delete or overwrite data |
| `idempotentHint: true` | Calling multiple times = same result |
| `openWorldHint: true` | Tool interacts with the external world (web, APIs) |

**Warning:** Annotations are advisory — they come from the server and are untrusted unless the server is from a verified source.

---

## 2. Resources

Resources are passive data sources. The application (not the LLM) decides when to include them in context. Reading a resource has no side effects.

### Capability declaration
```json
{
  "capabilities": {
    "resources": {
      "subscribe": true,
      "listChanged": true
    }
  }
}
```

### Discovery: resources/list
```json
// Request (supports pagination via cursor)
{ "jsonrpc": "2.0", "id": 4, "method": "resources/list" }

// Response
{
  "result": {
    "resources": [
      {
        "uri": "file:///project/src/main.py",
        "name": "main.py",
        "title": "Main Application Entry Point",
        "description": "Primary Python application file",
        "mimeType": "text/x-python",
        "size": 4821,
        "annotations": {
          "audience": ["assistant"],
          "priority": 0.9
        }
      },
      {
        "uri": "postgres://schema/users",
        "name": "users_table_schema",
        "mimeType": "application/json"
      }
    ],
    "nextCursor": "eyJwYWdlIjogMn0="
  }
}
```

### Reading: resources/read
```json
// Request
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": { "uri": "file:///project/src/main.py" }
}

// Text response
{
  "result": {
    "contents": [
      {
        "uri": "file:///project/src/main.py",
        "mimeType": "text/x-python",
        "text": "import fastapi\n\napp = fastapi.FastAPI()\n..."
      }
    ]
  }
}

// Binary response (image, PDF, etc.)
{
  "result": {
    "contents": [
      {
        "uri": "file:///project/diagram.png",
        "mimeType": "image/png",
        "blob": "iVBORw0KGgoAAAANSUhEUgAA..."
      }
    ]
  }
}
```

### Resource Templates (Dynamic Resources)

Templates use RFC6570 URI syntax to define parameterized resource patterns:

```json
{
  "result": {
    "resourceTemplates": [
      {
        "uriTemplate": "github://repos/{owner}/{repo}/issues/{issue_number}",
        "name": "GitHub Issue",
        "description": "Content and metadata for a specific GitHub issue",
        "mimeType": "application/json"
      }
    ]
  }
}
```

### Subscriptions

When a server supports `resources.subscribe`, clients can watch specific resources for changes:

```json
// Subscribe
{ "method": "resources/subscribe", "params": { "uri": "file:///project/config.yml" } }

// Server sends when file changes
{ "method": "notifications/resources/updated", "params": { "uri": "file:///project/config.yml" } }

// Unsubscribe
{ "method": "resources/unsubscribe", "params": { "uri": "file:///project/config.yml" } }
```

### Resource Annotations

```json
{
  "annotations": {
    "audience": ["user", "assistant"],
    "priority": 0.8,
    "lastModified": "2024-11-05T17:25:00Z"
  }
}
```

- `audience`: Who the resource is intended for — `"user"` (display in UI), `"assistant"` (include in LLM context)
- `priority`: 0.0–1.0, hint for context prioritization when context window is limited
- `lastModified`: ISO 8601 timestamp for caching decisions

### URI Schemes

| Scheme | Example | Notes |
|--------|---------|-------|
| `file://` | `file:///home/user/project/README.md` | May not be a real filesystem path |
| `https://` | `https://api.github.com/repos/...` | Client can fetch directly |
| `git://` | `git://repo/path/to/file@main` | Version control |
| Custom | `postgres://schema/users` | Server-defined schemes |

---

## 3. Prompts

Prompts are reusable, parameterized templates for LLM interactions. Users invoke them explicitly (like slash commands). They can embed resource content and multi-turn conversation patterns.

### Capability declaration
```json
{ "capabilities": { "prompts": { "listChanged": true } } }
```

### Discovery: prompts/list
```json
// Response
{
  "result": {
    "prompts": [
      {
        "name": "review_pr",
        "title": "Review Pull Request",
        "description": "Generate a thorough code review for a GitHub pull request",
        "arguments": [
          {
            "name": "pr_number",
            "description": "The pull request number to review",
            "required": true
          },
          {
            "name": "focus",
            "description": "Aspect to focus on: security, performance, or readability",
            "required": false
          }
        ]
      }
    ]
  }
}
```

### Getting a Prompt: prompts/get
```json
// Request
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "prompts/get",
  "params": {
    "name": "review_pr",
    "arguments": { "pr_number": "142", "focus": "security" }
  }
}

// Response — the server constructs the full conversation context
{
  "result": {
    "description": "Code review for PR #142 (security focus)",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Please review this pull request with a focus on security vulnerabilities:"
        }
      },
      {
        "role": "user",
        "content": {
          "type": "resource",
          "resource": {
            "uri": "github://repos/my-org/my-app/pulls/142",
            "mimeType": "application/json",
            "text": "{ \"title\": \"Add user authentication\", \"diff\": \"...\" }"
          }
        }
      }
    ]
  }
}
```

Prompt messages can include text, images, audio, or embedded resources — giving the server full control over what context is assembled for the LLM.

---

## 4. Sampling

Sampling lets a **server** request that the **host's LLM** generate text. The server never holds API keys or model-specific code — the host mediates everything.

### Client declares support
```json
{ "capabilities": { "sampling": {} } }
```

### Server sends: sampling/createMessage
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": { "type": "text", "text": "Summarize this code diff:\n\n+def calculate_tax(amount):\n+    return amount * 0.08" }
      }
    ],
    "modelPreferences": {
      "hints": [
        { "name": "claude-3-5-haiku" },
        { "name": "claude" }
      ],
      "costPriority": 0.8,
      "speedPriority": 0.9,
      "intelligencePriority": 0.3
    },
    "systemPrompt": "You are a code review assistant. Be concise.",
    "maxTokens": 200
  }
}
```

### Host responds with LLM output
```json
{
  "result": {
    "role": "assistant",
    "content": {
      "type": "text",
      "text": "Adds a simple 8% tax calculation function. No validation of negative amounts."
    },
    "model": "claude-haiku-4-5",
    "stopReason": "endTurn"
  }
}
```

### Model Preference Priorities

| Priority | Meaning | Example Use |
|----------|---------|------------|
| `costPriority` | Minimize cost | Batch processing, high-volume tasks |
| `speedPriority` | Minimize latency | Real-time interactions |
| `intelligencePriority` | Maximize capability | Complex reasoning, synthesis |

Hints are treated as **substrings** (not exact names) and are advisory — the host makes the final model selection. Multiple hints are ranked in preference order.

---

## 5. Elicitation

Elicitation lets a **server** request structured information or confirmation from the **user** (via the host). It's MCP's built-in human-in-the-loop mechanism.

### Client declares support
```json
{ "capabilities": { "elicitation": {} } }
```

### Server sends: elicitation/create
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "elicitation/create",
  "params": {
    "message": "You are about to delete 50 customer records. Please confirm:",
    "requestedSchema": {
      "type": "object",
      "properties": {
        "records_to_delete": {
          "type": "integer",
          "description": "Confirm number of records to delete",
          "minimum": 1,
          "maximum": 1000
        },
        "backup_confirmed": {
          "type": "boolean",
          "description": "I confirm a backup exists"
        },
        "reason": {
          "type": "string",
          "description": "Reason for deletion",
          "minLength": 10
        }
      },
      "required": ["records_to_delete", "backup_confirmed"]
    }
  }
}
```

### Three possible user responses

**Accept (user filled in the form):**
```json
{
  "result": {
    "action": "accept",
    "content": {
      "records_to_delete": 50,
      "backup_confirmed": true,
      "reason": "GDPR data erasure request from customer #7821"
    }
  }
}
```

**Decline (user said no):**
```json
{ "result": { "action": "decline" } }
```

**Cancel (user dismissed):**
```json
{ "result": { "action": "cancel" } }
```

### Supported Schema Types

| Type | Constraints | Example |
|------|------------|---------|
| `string` | `minLength`, `maxLength`, `format` (email, uri, date, date-time) | Email address |
| `number` / `integer` | `minimum`, `maximum` | Count, percentage |
| `boolean` | `default` | Confirmation checkbox |
| Enum | `enum` (values) + `enumNames` (display) | Dropdown selection |

**Important constraints:** Elicitation schemas must be flat objects of primitive properties only. No nested objects, no arrays of objects — designed to be renderable by any Host UI.

**Security rule:** Servers **MUST NOT** request sensitive information (passwords, credit cards, social security numbers) via Elicitation. The Host should display which server is making the request and allow users to review before submitting.

---

## 6. Roots

Roots let the **client** declare filesystem boundaries that **servers** should respect. They define the workspace scope.

### Client declares support
```json
{ "capabilities": { "roots": { "listChanged": true } } }
```

### Server requests: roots/list
```json
// Request
{ "jsonrpc": "2.0", "id": 9, "method": "roots/list" }

// Response
{
  "result": {
    "roots": [
      {
        "uri": "file:///home/user/projects/my-app",
        "name": "my-app (main project)"
      },
      {
        "uri": "file:///home/user/projects/shared-lib",
        "name": "shared-lib (dependency)"
      }
    ]
  }
}
```

### When roots change: notification
```json
{ "method": "notifications/roots/list_changed" }
```

The server should call `roots/list` again after receiving this notification.

**Security:** Roots are `file://` URIs only. Servers must validate all file paths against declared roots before accessing them — never traverse outside declared boundaries. Path traversal attacks (e.g., `../../../../etc/passwd`) must be validated against the root list.

---

## Pagination

Tools, Resources, and Prompts all support cursor-based pagination for large lists:

```json
// First request (no cursor)
{ "method": "tools/list" }

// Response with more pages
{
  "result": {
    "tools": [...],
    "nextCursor": "eyJwYWdlIjogMn0="
  }
}

// Next page
{
  "method": "tools/list",
  "params": { "cursor": "eyJwYWdlIjogMn0=" }
}
```

---

**Related Topics:**
- [Why MCP Matters →](06-Why-MCP-Matters.md)
- [Architecture Deep-Dive →](07-Architecture-Deep-Dive.md)
- [Getting Started →](08-Getting-Started.md)

---

## Q&A Review Bank

**Q1: What are all six MCP primitives and which side exposes each?** `[Easy]`

A: Server-side (servers expose to clients): Tools (executable functions with potential side effects, model-controlled), Resources (passive data sources, application-controlled), and Prompts (reusable templates, user-controlled). Client-side (clients expose back to servers): Sampling (server requests LLM text generation from the host), Elicitation (server requests structured user input or confirmation), and Roots (client declares filesystem boundaries the server may access). The controller distinction — model, app, or user — determines which party decides when each primitive is used.

---

**Q2: What are tool annotations and why are they untrusted by default?** `[Medium]`

A: Tool annotations are metadata hints attached to tool definitions describing behavior: `readOnlyHint` (no side effects), `destructiveHint` (may delete data), `idempotentHint` (safe to call multiple times), `openWorldHint` (interacts with external systems). They're untrusted by default because they originate from the server — any server can claim `readOnlyHint: true` on a tool that actually deletes records. Hosts and users must verify behavior from trusted server sources rather than relying on self-reported annotations. Treating annotations as verified facts is a security vulnerability.

---

**Q3: What is the difference between `resources.listChanged` and `resources.subscribe`, and when do you need both?** `[Medium]`

A: `resources.listChanged` means the server will send `notifications/resources/list_changed` when the *set of available resources changes* (new file added, resource removed). `resources.subscribe` means clients can call `resources/subscribe` for a specific URI and receive `notifications/resources/updated` whenever that specific resource's *content* changes. You need both for a live coding assistant: `listChanged` to discover when new files appear in the project, and `subscribe` to get real-time updates when a watched file is edited. With only `listChanged` you'd know a file exists but never know it changed; with only `subscribe` you'd never discover new files.

---

**Q4: Elicitation schemas have strict constraints (flat, primitive only). What problem does this solve?** `[Hard]`

A: The constraint that Elicitation schemas must be flat objects of primitive properties (no nested objects, no arrays of objects) ensures every MCP Host — from a desktop GUI to a CLI to a voice interface — can render a confirmation dialog without needing a general-purpose form renderer. A schema with nested objects and arrays would require a complex UI component; a flat schema of strings, numbers, booleans, and enums maps directly to text fields, number inputs, checkboxes, and dropdowns that every UI toolkit provides. This is a deliberate protocol-level tradeoff: some expressive power is sacrificed to guarantee universal renderability across all Host implementations.

---

**Q5: A server uses the Sampling primitive to call `sampling/createMessage` with `intelligencePriority: 1.0` and a hint of `claude-opus`. Can it guarantee that model will be used?** `[Hard]`

A: No — model preferences are advisory, not binding. The Host makes the final model selection based on its own configuration, available models, cost policies, and rate limits. The hints are treated as substring matches, not exact model names, so `"claude-opus"` might match `claude-opus-4-7` or `claude-3-opus-20240229` depending on what the Host has configured. `intelligencePriority: 1.0` signals strong preference for capability over cost/speed, which the Host should weight heavily, but it cannot override the Host's access controls or billing constraints. This design is intentional: servers remain model-agnostic and never hold model credentials.
