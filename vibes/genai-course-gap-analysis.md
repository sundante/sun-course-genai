# GenAI Course - Gap Analysis & Aspiration

_2026-08-09 - Analysis of the course (`src/content/`) against a personal 16-week GenAI upskilling plan (7 phases: transformer/PyTorch fundamentals, fine-tuning, agentic AI, eval/observability, production engineering, platform breadth, visibility). Kept here as a standing reference, not a course module - part analysis of where the course stands today, part aspiration for what to build next._

## Coverage today

### Well covered
- **Transformer internals** (Phase 0) - strong. `01-LLM-Models` covers attention, KV-cache, positional encoding, decoder-only vs encoder-decoder, sampling in real depth.
- **Agentic patterns** (Phase 2) - the course's strongest area. `05-Agents`, `06-Agentic-AI`, and `04-MCP` cover ReAct, reflection/reflexion, plan-and-execute, hierarchical delegation, tool calling/JSON schema, MCP (full module), LangGraph fundamentals + code labs. 7 runnable architecture-pattern labs, 4 full agentic systems, and 3 healthcare system designs.
- **Eval/observability basics** (Phase 3) - decent. LLM-as-judge, LangSmith/Langfuse concepts appear across Agentic-AI and RAG eval notes, though not yet a dedicated deep module.

### Thin / conceptual only, not hands-on
- LoRA/QLoRA/PEFT/quantization - explained conceptually in `07-Fine-Tuning.mdx` / `08-GPU-and-Hardware.mdx`, no hands-on lab.
- vLLM/serving - a few passing mentions, no real content.
- Security/guardrails (PII, HIPAA) - present inside healthcare system-design docs, not formalized as its own module.

### Essentially absent
- **PyTorch fundamentals** - Dataset/DataLoader, autograd, training loop, checkpointing, mixed precision. Zero dedicated content.
- **HuggingFace ecosystem hands-on** - transformers/datasets/hub libraries.
- **Production engineering** - Docker/Kubernetes for GPU inference, model lifecycle (versioning/canary/rollback), DevSecOps/compliance controls.
- **Platform breadth** - AWS Bedrock, Databricks/Spark/Delta Lake/Unity Catalog, Azure AI Foundry.
- **Diffusion models, GANs, CUDA, DSPy depth** - scattered single-line mentions at most; diffusion/GANs are zero hits.

## Aspiration - next-module shortlist

Ranked by how central each is to a real GenAI engineering track and how absent it is today:

1. **PyTorch fundamentals module** - the biggest structural gap; almost every downstream fine-tuning/serving topic assumes it.
2. **Hands-on LoRA/QLoRA fine-tuning lab** - upgrade `07-Fine-Tuning.mdx`'s conceptual coverage into a code lab, mirroring the existing `06-Agentic-AI/CodeLabs` pattern.
3. **Serving module** - vLLM, quantized inference, batching/latency. Natural pair with #2.
4. **Production engineering module** - Docker/K8s for GPU inference, model lifecycle/canary/rollback. Currently the weakest phase in the whole site.
5. **Platform breadth primer** - Bedrock / Databricks / Azure AI Foundry mapping table. Lower effort, high resume/interview value, matches the site's existing comparison-table pattern used elsewhere.

Diffusion models, GANs, CUDA internals, and deep DSPy coverage are intentionally deprioritized - they're conversational-depth-only "gap-fillers" even in the source upskilling plan, not core engineering skills worth a full module right now.

## Note

This file is a planning reference, not a `src/content/` course module. Turning any shortlist item into real course content (new module + `nav.yml` entry) is a separate follow-up task.
