// Hand-written subtitle + description per module, keyed by slug. Shared by the home page
// tiles (CurriculumTiles.tsx - a module with no entry here gets no tile) and the course map
// (courseMap.ts - the subtitle is the landmark's name). No fs imports: client components use it.
// Numbers, order, tracks and counts are not here: they come from nav.yml
// (via getNavigationTree / getCourseStats) so they cannot drift out of date.

export interface ModuleMeta {
  subtitle: string;
  description: string;
}

export const MODULE_META: Record<string, ModuleMeta> = {
  "llm-models":             { subtitle: "The Engine",       description: "How large language models work - tokens, the transformer, attention, model families, and the ways they fail." },
  "prog-langs":             { subtitle: "The Toolkit",      description: "Python and systems engineering for AI - uv and asyncio, LLM API design, Git workflows, Linux and the GPU box - then PyTorch: tensors, autograd, the training loop, checkpointing and mixed precision." },
  "math-for-ml":            { subtitle: "The Language",     description: "The math LLM work actually uses - linear algebra for attention and LoRA, probability and information theory for losses and sampling, calculus and optimizers, and statistics for honest evals." },
  "pretraining":            { subtitle: "The Forge",        description: "How base models are built - data pipelines, scaling laws, distributed training, and the GPU memory budget." },
  "post-training":          { subtitle: "The Finishing",    description: "From base model to assistant - SFT, preference tuning, RLHF, GRPO and reasoning, LoRA and QLoRA." },
  "fine-tuning-lab":        { subtitle: "The Specialist",   description: "Hands-on LoRA/QLoRA fine-tuning - the HuggingFace ecosystem, instruction data, training runs, and a real base-vs-tuned benchmark." },
  "evaluation":             { subtitle: "The Yardstick",    description: "Measuring models honestly - benchmarks, contamination, LLM-as-judge, and building your own evaluation harness." },
  "serving-and-inference":  { subtitle: "The Delivery",     description: "Serving models fast and cheaply - KV cache, vLLM, quantized inference, batching, streaming, and deployment." },
  "production-engineering": { subtitle: "The Operations",   description: "Docker, Kubernetes and Helm for GPU inference, model lifecycle and rollout, and security & compliance controls." },
  "platform-breadth":       { subtitle: "The Landscape",    description: "AWS Bedrock, Google Cloud's agent platform (formerly Vertex AI), Microsoft Foundry, and Databricks - a working map across the major cloud AI stacks." },
  "prompt-engineering":     { subtitle: "The Interface",    description: "Talking to models well - prompting techniques, prompting mechanics, production prompt systems, and optimization." },
  "rag":                    { subtitle: "The Memory",       description: "Retrieval-Augmented Generation - giving LLMs access to your own knowledge and keeping answers grounded." },
  "agents":                 { subtitle: "The Actors",       description: "What agents are and how they work - the agent loop, tool use, memory, and planning." },
  "mcp":                    { subtitle: "The Protocol",     description: "Model Context Protocol and A2A - connecting agents to tools, data and each other, with authorization and security." },
  "agentic-ai":             { subtitle: "The Blueprints",   description: "Workflow and single-agent patterns, multi-agent architectures and engineering - and the evidence on when each helps." },
  "agent-frameworks":       { subtitle: "The Workshop",     description: "LangGraph, OpenAI Agents SDK, Claude Agent SDK, Google ADK, CrewAI, Microsoft Agent Framework and PydanticAI - one agent built in each." },
  "production-agents":      { subtitle: "The Systems",      description: "Shipping agents - architecture, security, durable execution, cost, evaluation and benchmarks, observability, and system designs." },
  "agent-engineering":      { subtitle: "The Architecture", description: "Designing the system around the model - harnesses, loops and graphs, context, coding and computer-use agents, skills, verifiers and specs." },
  "solutions-architecture": { subtitle: "The Bridge",       description: "Turning a customer problem into a system people will fund and use - discovery, qualification and ROI, architecture docs and ADRs, communicating to every audience, and PoC to production." },
  "capstones":              { subtitle: "The Proof",        description: "Three end-to-end projects with rubrics - train and post-train a model, serve it against an SLO, and ship a production agent." },
};
