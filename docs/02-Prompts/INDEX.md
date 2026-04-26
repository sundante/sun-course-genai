# 02 — Prompt Engineering

## What You Will Learn

Prompt engineering is the practice of designing inputs to language models to reliably produce the desired outputs. It is the first lever you pull when working with LLMs — before fine-tuning, before RAG, before agents. It is also the fastest to iterate on: a prompt change takes seconds; retraining takes days.

## Why It Comes After LLMs

You need to understand how LLMs process tokens and generate text (Topic 01) before you can reason about *why* certain prompt structures work. Prompt engineering is applied LLM knowledge — tokenization explains why character-level tasks fail; attention explains why "lost in the middle" happens; instruction tuning explains why zero-shot prompting works at all.

## Why It Comes Before RAG and Agents

RAG pipelines and agents are built on top of prompts. The quality of your retrieval prompts, tool-use prompts, and system prompts directly determines system quality. Strong prompting fundamentals make everything downstream better.

## The Evolution Arc

This section is structured to follow the historical development of the field:

```
2020  Zero-shot / few-shot discovered (GPT-3)
2022  Chain-of-Thought unlocks reasoning (Wei et al.)
2022  ReAct connects models to tools (Yao et al.)
2023  ToT, self-consistency — systematic search over reasoning space
2023  Production concerns: injection, evals, versioning, structured output
2024  DSPy, OPRO — automated prompt optimization
Now   Reasoning models change the prompting paradigm
```

## Chapter Map

| # | File | Topic |
|---|------|-------|
| 1 | [Prompt Basics](Notes/01-Prompt-Basics.md) | Anatomy, system vs user, mental model, tokenization, temperature |
| 2 | [Core Techniques](Notes/02-Core-Techniques.md) | Zero-shot, few-shot, CoT, ReAct, role/persona |
| 3 | [Advanced Techniques](Notes/03-Advanced-Techniques.md) | ToT, self-consistency, chaining, meta-prompting, L2M |
| 4 | [Prompts in Production](Notes/04-Prompt-Engineering-for-Production.md) | Structured output, versioning, injection, evals, context management |
| 5 | [Prompt Optimization & Automation](Notes/05-Prompt-Optimization-and-Automation.md) | APE, OPRO, DSPy, LLM-as-Judge, reasoning models |
| 6 | [Q&A Review Bank](Notes/06-Interview-QA-Bank.md) | 65+ questions, Easy → Staff-level |

## Recommended Path

1. [Prompt Basics](Notes/01-Prompt-Basics.md) — understand what a prompt actually is
2. [Core Techniques](Notes/02-Core-Techniques.md) — learn the patterns used 90% of the time
3. [Advanced Techniques](Notes/03-Advanced-Techniques.md) — extend your toolkit for complex tasks
4. [Prompts in Production](Notes/04-Prompt-Engineering-for-Production.md) — real-world engineering concerns
5. [Prompt Optimization & Automation](Notes/05-Prompt-Optimization-and-Automation.md) — scale beyond manual iteration
6. [Q&A Review Bank](Notes/06-Interview-QA-Bank.md) — consolidated review across all topics
7. [Knowledge Check](../Interview-Questions/02-Prompt-Engineering.md) — concise Q&A for final review

## Navigation

[Previous: 01 — LLM Models](../01-LLM-Models/INDEX.md) | [Next: 03 — RAGs](../03-RAGs/INDEX.md)
