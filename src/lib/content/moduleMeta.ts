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
  "python-and-systems":     { subtitle: "The Toolkit",      description: "Python and systems engineering for AI - uv and asyncio, LLM API design, Git workflows for ML, and Linux and the GPU box." },
  "math-for-ml":            { subtitle: "The Language",     description: "The math LLM work actually uses - linear algebra for attention and LoRA, probability and information theory for losses and sampling, calculus and optimizers, and statistics for honest evals." },
  "foundation-models":      { subtitle: "The Engine",       description: "The foundation every other module builds on - tokens, the transformer, attention, model families, and the ways large language models predictably fail." },
  "evaluation":             { subtitle: "The Yardstick",    description: "Measuring models honestly - benchmarks, contamination, LLM-as-judge, safety red-teaming, and building your own evaluation harness." },
  "prompt-engineering":     { subtitle: "The Interface",    description: "Talking to models well - prompting techniques, structured outputs, context engineering, caching and cost, production prompt systems, and optimization." },
  "pytorch":                { subtitle: "The Workbench",    description: "PyTorch from tensors and autograd to the training loop, checkpointing and mixed precision, GPU memory debugging - ending with a GPT built from scratch." },
  "pretraining":            { subtitle: "The Forge",        description: "How base models are built - data curation, scaling laws and stable training, then the compute side: GPU memory, distributed training, accelerators and CUDA profiling." },
  "post-training":          { subtitle: "The Finishing",    description: "From base model to assistant - SFT, preference tuning, RL and reasoning - then hands-on LoRA/QLoRA fine-tuning with the Hugging Face stack, TRL, and a real base-vs-tuned benchmark." },
  "agent-fundamentals":     { subtitle: "The Actors",       description: "What agents are and how they work - agents vs workflows, the anatomy of an agent, the agent loop, where agents pay off, and a first evaluation with pass^k." },
  "agent-building-blocks":  { subtitle: "The Parts",        description: "The parts every agent is assembled from - tool use and function calling, memory from working context to long-term stores, and planning and reasoning." },
  "mcp-and-a2a":            { subtitle: "The Protocol",     description: "Model Context Protocol and A2A - connecting agents to tools, data and each other, with authorization and security." },
  "agentic-workflows":      { subtitle: "The Blueprints",   description: "Agentic workflow patterns, single-agent patterns, multi-agent architectures and engineering - and the evidence on when each helps." },
  "rag":                    { subtitle: "The Memory",       description: "Retrieval-Augmented Generation - giving LLMs access to your own knowledge, from the core pipeline through advanced patterns to enterprise RAG in production." },
  "agent-frameworks":       { subtitle: "The Workshop",     description: "LangGraph, OpenAI Agents SDK, Claude Agent SDK, Google ADK, CrewAI, Microsoft Agent Framework and PydanticAI - one agent built in each." },
  "production-agents":      { subtitle: "The Systems",      description: "Shipping agents - architecture, security, durable execution, cost, evaluation and benchmarks, observability, and case studies." },
  "inference-and-serving":  { subtitle: "The Delivery",     description: "Serving models fast and cheaply - KV cache, vLLM, quantized inference, batching, streaming, and deployment." },
  "production-engineering": { subtitle: "The Operations",   description: "Docker, Kubernetes and Helm for GPU inference, cloud networking, IAM and infrastructure as code, then model rollout, observability and SLOs, and security & compliance." },
  "cloud-platforms":        { subtitle: "The Landscape",    description: "AWS Bedrock, Google Cloud's agent platform (formerly Vertex AI), Microsoft Foundry, and Databricks - a working map across the major cloud AI stacks." },
  "agent-engineering":      { subtitle: "The Architecture", description: "Designing the system around the model - harnesses, loops and graphs, context, skills and memory, coding and computer-use agents, specs, verifiers and agent RL." },
  "solutions-architecture": { subtitle: "The Bridge",       description: "Turning a customer problem into a system people will fund and use - discovery, qualification and ROI, architecture docs and ADRs, communicating to every audience, and PoC to production." },
  "capstones":              { subtitle: "The Proof",        description: "Three end-to-end projects with rubrics - train and post-train a model, serve it against an SLO, and ship a production agent." },
};
