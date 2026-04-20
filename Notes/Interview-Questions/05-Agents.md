# Interview Q&A — Agents

## Conceptual Questions

**Q: What is an AI Agent?**
An AI Agent is a system that uses a Large Language Model (LLM) as its "brain" to perceive its environment, reason through complex goals, and execute actions autonomously using external tools to achieve a specific outcome. Unlike a chatbot (single input → single output), an agent pursues a goal over multiple steps — it acts, receives feedback, and adapts rather than just generating one response.

**Q: What are the key features of AI Agents?**
- **Autonomy**: Act independently without constant human intervention
- **Goal-Oriented**: Driven by objectives, aiming to maximize success based on defined metrics
- **Perception & Observation**: Gather information from the environment to understand context
- **Reasoning & Rationality**: Analyze data, identify patterns, and make informed decisions
- **Planning**: Develop strategic plans to achieve goals
- **Acting & Proactivity**: Take initiative and execute actions based on decisions, anticipating events rather than just reacting
- **Adaptability**: Adjust strategies and learn in response to new circumstances
- **Collaboration**: Work effectively with humans or other AI agents through communication and coordination

**Q: What is the agent loop (Perceive → Reason → Act)?**
Perceive: receive input — user message, tool result, or environmental state. Reason: use the LLM to decide what to do next (which tool to call, or whether to respond). Act: execute the chosen action — call a tool, run code, search the web, etc. The loop repeats until a stopping condition is met (task complete, max steps reached, confidence threshold).

**Q: What is tool use / function calling?**
Function calling allows the LLM to request the execution of a predefined function by outputting structured JSON (function name + arguments) instead of text. The application executes the function and returns the result to the LLM. This turns the LLM from a text generator into something that can interact with the world: search APIs, databases, code interpreters, external services.

**Q: What is the difference between tool use and MCP?**
Tool use (function calling) is a mechanism — the LLM outputs a function signature, your application calls it. Each integration is custom. MCP is a *protocol* that standardizes how tools and data sources are exposed to LLMs — a universal interface so any MCP server can work with any MCP-compatible host. MCP is the scalable, ecosystem-level answer to the N×M integration problem.

---

## Framework-Specific Questions

**Q: What is the ReAct pattern?**
Reasoning + Acting interleaved. The agent generates a Thought (internal reasoning about what to do), then an Action (tool call), then receives an Observation (tool result), then reasons again. This cycle continues until a Final Answer is reached. Compared to pure CoT, ReAct has access to real-world information via tools, making it far more capable for information-retrieval and multi-step tasks.

**Q: When would you choose LangGraph over LangChain?**
Use LangGraph when: (1) your agent needs cycles — revisiting earlier steps, retrying, looping; (2) you need persistent, checkpointed state across a long conversation; (3) you want explicit control over agent flow with branching logic; (4) you're building multi-agent systems with defined coordination. LangChain is sufficient for linear pipelines. LangGraph is built on top of LangChain — it's an extension, not a replacement.

**Q: What is CrewAI's role-based model and when is it useful?**
In CrewAI, each agent has a defined Role, Goal, and Backstory — this primes the LLM to behave like a specific persona (researcher, writer, critic). Agents are assigned Tasks and can delegate to each other. This model shines when a problem naturally decomposes into distinct professional roles. It's more intuitive to design than explicit graph-based flows but offers less low-level control.

---

## Architecture and Design Questions

**Q: How do agents maintain state and memory?**
Four types: (1) In-context — information in the current prompt window (short-lived). (2) External storage — key-value stores, databases, vector stores (persistent). (3) Episodic memory — past conversation summaries retrieved at the start of new sessions. (4) Semantic memory — a knowledge base the agent can query. Most production systems combine all four.

**Q: What are the main failure modes of LLM agents?**
(1) Tool call loops — agent keeps calling the same tool without progress. (2) Hallucinated tool arguments — LLM generates invalid parameters. (3) Context overflow — accumulated observations exceed the context window. (4) Overconfident stopping — agent decides it's done before the task is complete. (5) Cascading errors — early tool call failure derails the entire plan. Mitigation: max-step limits, result validation, structured error handling, human-in-the-loop checkpoints.

**Q: What is a multi-agent system and when do you need one?**
Multiple specialized agents collaborating on a task — an orchestrator decomposes the task and delegates to subagents (researcher, coder, reviewer). Needed when: (1) parallelism — subtasks can run concurrently; (2) specialization — different parts require different personas or tools; (3) context management — each subagent handles its own context window. The cost is coordination overhead and harder debugging.
