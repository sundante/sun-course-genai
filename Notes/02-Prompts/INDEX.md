# 02 — Prompt Engineering

## What You Will Learn

Prompt engineering is the practice of designing inputs to language models to reliably produce the desired outputs. It is the first lever you pull when working with LLMs — before fine-tuning, before RAG, before agents.

## Why It Comes After LLMs

You need to understand how LLMs process tokens and generate text (Topic 01) before you can reason about *why* certain prompt structures work. Prompt engineering is applied LLM knowledge.

## Why It Comes Before RAG and Agents

RAG pipelines and agents are built on top of prompts. The quality of your retrieval prompts, tool-use prompts, and system prompts directly determines system quality. Strong prompting fundamentals make everything downstream better.

## Chapter Map

| # | File | Topic |
|---|------|-------|
| 1 | [Prompt Basics](Notes/01-Prompt-Basics.md) | Anatomy, system vs user, mental model |
| 2 | [Core Techniques](Notes/02-Core-Techniques.md) | Zero-shot, few-shot, CoT, ReAct |
| 3 | [Advanced Techniques](Notes/03-Advanced-Techniques.md) | ToT, self-consistency, meta-prompting |
| 4 | [Prompts in Production](Notes/04-Prompt-Engineering-for-Production.md) | Templates, versioning, injection, evals |

## Recommended Path

1. [Prompt Basics](Notes/01-Prompt-Basics.md) — understand what a prompt actually is
2. [Core Techniques](Notes/02-Core-Techniques.md) — learn the patterns used 90% of the time
3. [Advanced Techniques](Notes/03-Advanced-Techniques.md) — extend your toolkit
4. [Prompts in Production](Notes/04-Prompt-Engineering-for-Production.md) — real-world considerations
5. [Interview Q&A](../Interview-Questions/02-Prompt-Engineering.md) — consolidate and test

## Navigation

[Previous: 01 — LLM Models](../01-LLM-Models/INDEX.md) | [Next: 03 — RAGs](../03-RAGs/INDEX.md)
