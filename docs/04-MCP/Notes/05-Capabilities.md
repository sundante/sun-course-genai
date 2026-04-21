# ✨ What can MCP Enable?

[← Back to Index](../INDEX.md)

## Use Cases & Applications

### 1. Personalized AI Assistants
**Agents can access your Google Calendar and Notion**, acting as a more personalized AI assistant.

- Real-time schedule awareness
- Task and note integration
- Proactive suggestions based on context
- Cross-platform data synchronization

#### Details
*Add your notes about personalized assistants here...*

---

### 2. Web App Generation from Design
**Claude Code can generate an entire web app using a Figma design.**

- Visual design to code conversion
- Automated UI/UX implementation
- Design-aware code generation
- Reduced development time

#### Details
*Add your notes about design-to-code here...*

---

### 3. Enterprise Data Chatbots
**Enterprise chatbots can connect to multiple databases** across an organization, empowering users to analyze data using chat.

- Multi-database queries
- Natural language data analysis
- Cross-system insights
- User-friendly data access

#### Details
*Add your notes about enterprise applications here...*

---

### 4. Advanced Design & Manufacturing
**MCP can be used for any AI application** that can create 3D designs on Blender and print them out using a 3D printer.

- AI-assisted design creation
- CAD integration
- 3D printing automation
- Manufacturing workflow optimization

#### Details
*Add your notes about design & manufacturing here...*

---

## Other Potential Applications

### Brainstorm & Expand
*Add other capabilities you discover as you learn more:*

- 
- 
- 

---

## Common Patterns

1. **Data Access:** Connecting to various data sources
2. **Automation:** AI-driven task automation
3. **Integration:** Bridging multiple systems
4. **Intelligence:** Adding AI capabilities to existing tools

---

## Detailed Exploration

*Add your detailed analysis of capabilities and use cases here...*

---

**Related Topics:**
- [Why MCP Matters →](06-Why-MCP-Matters.md)
- [Components →](04-Components.md)
- [Getting Started →](08-Getting-Started.md)

---

## Q&A Review Bank

**Q1: Name all three server-side primitives and all three client-side primitives in MCP.** `[Easy]`

A: Server-side primitives (what servers expose): Tools (executable functions with side effects), Resources (readable data sources identified by URI), and Prompts (reusable, parameterized templates). Client-side primitives (what clients/hosts expose back to servers): Sampling (server asks the host's LLM to generate text), Elicitation (server requests user input or confirmation), and Logging (server sends debug/info logs to the host for observability). The client-side primitives are less commonly discussed but are architecturally significant — they allow servers to leverage the host's capabilities rather than being purely passive responders.

---

**Q2: What is the difference between a Tool and a Resource? When does the distinction matter most?** `[Medium]`

A: A Tool is an executable function with input parameters that performs an action and returns a result — it may have side effects such as writing files, calling external APIs, or modifying database records. A Resource is a passive data source identified by a URI that the client can read without triggering logic — equivalent to a side-effect-free read. The distinction matters most for trust and authorization: LLMs can freely read Resources during planning without user approval, but Tool invocations represent irreversible agent actions that should be visible and potentially gated. A Host might display all Tool calls to users while reading Resources silently in the background.

---

**Q3: What is the Sampling primitive and why is it architecturally significant?** `[Medium]`

A: Sampling allows a Server to ask the Host's LLM to generate text as part of the server's own logic — for example, a document-summarizer MCP server can invoke the LLM to produce the summary rather than calling an external model API. Architecturally, this makes MCP servers model-agnostic: the server specifies generation preferences (speed vs. quality, context budget) but doesn't hardcode a specific LLM; the Host chooses the actual model and routes the request. The same MCP server therefore works unmodified with Claude, GPT-4, or any future model — the "intelligence" stays in the Host layer and the server remains a pure capability provider.

---

**Q4: Design an MCP server for a product inventory system — what would you expose as Tools vs. Resources?** `[Hard]`

A: Resources (read-only, no approval needed): current inventory counts per SKU, product catalog schema, category hierarchy, supplier list, price history — safe for the LLM to read freely during planning. Tools (executable, may have side effects, require intent): `reserve_stock(sku, quantity)`, `create_purchase_order(supplier_id, items)`, `update_price(sku, new_price)`, `cancel_reservation(reservation_id)` — these modify state and should be LLM-invoked actions with user visibility. The key principle: anything the LLM should "see" without acting → Resource; anything that changes the world → Tool. Misclassifying a write operation as a Resource removes the authorization gate and creates a silent side-effect path.

---

**Q5: A server sends `notifications/tools/list_changed`. What must a well-implemented Host do, and what breaks if it doesn't?** `[Hard]`

A: The Host must immediately send a `tools/list` request to the server to fetch the updated tool manifest, then refresh the tool registry for that Client connection. If the Host ignores the notification, the LLM operates on a stale tool list — it may attempt to call tools that no longer exist (causing runtime errors), or miss newly available tools that would have improved the response. For agentic systems mid-task, the Host must also decide whether to re-plan with the new tool set or complete the current plan. In production, tool list changes should be logged as audit events since unexpected capability shifts can indicate a compromised, updated, or misconfigured server.
