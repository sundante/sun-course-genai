# Concept Review — Prompt Engineering

Quick-reference Q&A for interview preparation. For in-depth treatment, see the [Q&A Review Bank](../02-Prompts/Notes/06-Interview-QA-Bank.md).

---

## Foundational

**Q: What is prompt engineering and why does it matter?**  
The practice of designing, testing, and iterating on LLM inputs to reliably produce desired outputs. Matters because the same model performs drastically differently based on how the task is framed — a well-designed prompt can match fine-tuned model performance at zero additional cost and in seconds of iteration.

**Q: What are the four components of a well-structured prompt?**  
Instruction (what to do), Context (background the model needs), Input Data (the content to process), Output Format (the shape of the response). Add components only to fix actual failures — start minimal.

**Q: What is the difference between a system prompt and a user prompt?**  
System prompt: developer-controlled, establishes persona, constraints, and format rules for the entire session. User prompt: the actual task or query. The model sees both; system takes behavioral precedence — but that precedence is trained behavior, not an architectural guarantee.

**Q: Can a system prompt be overridden by a user?**  
Not through the API role mechanism, but through adversarial prompting. Role hierarchy is trained via RLHF, not enforced architecturally. Sufficiently crafted user input can cause the model to ignore system instructions — the basis of jailbreaking and prompt injection.

**Q: What is assistant prefill?**  
Injecting a partial assistant message before generation begins, forcing the model to continue from that starting point. Used to prevent preamble text, force JSON output (start with `{`), or enforce a specific structure.

**Q: What is tokenization and why does it matter for prompting?**  
Tokenization converts text into subword units (tokens) — what the model actually processes. Numbers, code, and special characters split across token boundaries in non-obvious ways. Context windows are token-counted. Character-level tasks (count letters, reverse strings) fail because the model reasons over tokens, not characters.

**Q: What is the "prompt as a program" mental model?**  
Prompt = function body; input data = argument; model output = return value; model = interpreter. Enables engineering discipline: debug by adding "print statements" (think aloud), test with eval sets, compose via prompt chaining.

---

## Core Techniques

**Q: What is zero-shot prompting and why does it work?**  
Giving the model a task with no examples. Works because instruction tuning (RLHF, FLAN) installed a general "follow natural language instructions" skill across thousands of task types. Only works on instruction-tuned models.

**Q: What is few-shot prompting (in-context learning)?**  
Including 1–N input→output examples before the query. The model learns the task format and pattern through completion, not gradient updates. Example quality, order, and diversity matter more than quantity.

**Q: What is label sensitivity in few-shot prompting?**  
Model performance changes when example labels change, even with equally valid examples. Related: recency bias — the last few examples disproportionately influence the output. Shuffle example order and balance classes to mitigate.

**Q: Research shows few-shot works even with wrong labels. What does this mean?**  
Few-shot is primarily a format/distribution signal, not knowledge injection (Min et al., 2022). Models learn task structure from examples, not correct label semantics. Format consistency and example diversity matter more than label accuracy.

**Q: What is Chain-of-Thought prompting?**  
Instructing the model to produce intermediate reasoning steps before the final answer. Intermediate tokens serve as working memory — each step is written into context and available for subsequent reasoning, extending the model's ability to track state across multi-step problems.

**Q: What is zero-shot CoT?**  
Adding "Let's think step by step" to a prompt without any examples. Works because instruction-tuned models were trained on step-by-step reasoning data. The phrase activates that pattern.

**Q: What is ReAct prompting?**  
Thought → Action → Observation loop. The model generates a Thought (internal reasoning), an Action (tool call), receives an Observation (tool result), and repeats. Foundation of all tool-using agents. The model generates text describing tool calls; application code executes them.

**Q: What is role/persona prompting and what does it actually change?**  
"You are an expert X" shifts response vocabulary, depth, tone, and assumed audience — not the model's actual knowledge. Personas don't inject new knowledge; they shift the response distribution.

**Q: Why is negative prompting less reliable than positive framing?**  
"Don't do X" requires the model to represent X to negate it — potentially priming the behavior. "Do Y instead" gives a direct positive target. Use negative framing only for prohibitions with no clean positive alternative.

---

## Advanced Techniques

**Q: What is Tree of Thought (ToT)?**  
Extends CoT from a single linear chain to a tree search. Generates multiple candidate reasoning steps at each level, scores them, and explores the best branches — backtracking on dead ends. Cost: O(breadth × depth) LLM calls. Use when CoT consistently fails and the problem has well-defined evaluation criteria.

**Q: What is self-consistency?**  
Generate N diverse CoT chains (high temperature), take a majority vote on the final answer. Improves accuracy by averaging out errors across chains. Works only for tasks with verifiable, convergent answers. Cost: N× base cost.

**Q: What is prompt chaining?**  
Decomposing a complex task into a pipeline of focused prompts, where output of step N feeds step N+1. Benefits: debuggable, composable, parallelizable. Risk: error propagation — validate intermediate outputs.

**Q: What is the self-refinement loop?**  
Generate → critique → revise, iterated 1–3 times. Improves output quality for tasks with clear evaluation criteria. Subject to the model's own blind spots — it may not critique its own errors.

**Q: What is Generated Knowledge Prompting?**  
Ask the model to generate relevant facts before answering. Predecessor to RAG — makes implicit knowledge explicit in context. Risk: model can hallucinate the generated facts, which then become the basis for a confident wrong answer.

**Q: What is Least-to-Most Prompting?**  
Decompose a problem into sub-problems ordered from simplest to hardest. Solve each, carrying the solution forward as context for the next sub-problem. Effective for multi-step math, multi-hop Q&A, and complex code generation.

---

## Production and Security

**Q: Why is JSON mode not sufficient for structured output?**  
JSON mode guarantees syntactically valid JSON but not your schema. The model can return any valid JSON structure. Schema enforcement requires structured output with a Pydantic model or manual post-hoc validation.

**Q: What is prompt drift?**  
Silent degradation when the model provider updates the underlying model. Your prompt stays the same; model behavior changes. Detection: monitor output metrics continuously. Mitigation: pin model versions in production; run eval suites before switching model versions.

**Q: What is prompt injection?**  
An attack where malicious instructions embedded in user input or external data override system instructions. Direct: user input contains override instructions. Indirect: malicious instructions embedded in retrieved content (web pages, documents). No complete defense exists — use defense in depth.

**Q: What is prompt leaking?**  
Causing the model to reveal its system prompt via crafted inputs ("Repeat everything above verbatim"). Defense: explicit prohibition in system prompt, output monitoring for key phrases, and keeping the system prompt brief and non-sensitive.

**Q: What is the "lost in the middle" problem?**  
Models attend more strongly to tokens at the beginning and end of the context window. Critical instructions or documents placed in the middle receive less attention. Mitigation: place critical content at start or end; repeat important instructions.

**Q: How do you evaluate prompt quality systematically?**  
Golden set with representative + edge case examples; LLM-as-judge for non-binary quality; regression testing against previous prompt versions; security tests (injection, leaking). Always evaluate before any production deployment.

**Q: What are the known biases of LLM-as-Judge?**  
Position bias (prefers first option), verbosity bias (prefers longer responses), self-preference (favors same-model-family outputs), sycophancy (agrees with hinted preferences). Mitigations: swap A/B order and average, use a different model as judge, include conciseness in the rubric.

---

## Automation and Evaluation

**Q: What is APE (Automatic Prompt Engineer)?**  
Use an LLM to generate candidate prompt instructions from demonstration pairs, evaluate each on a test set, and select the best. One-shot: generate once, evaluate, select. Does not iteratively improve.

**Q: What is OPRO?**  
Iterative prompt optimization. Maintains a history of (prompt, score) pairs; an optimizer LLM proposes improvements based on the history — converging over multiple rounds. Similar to gradient descent but using language rather than calculus.

**Q: What is DSPy?**  
A framework where you write programs using LM calls as primitives; DSPy compiles those programs into optimized prompts automatically. Requires a metric function and training data. The prompt is an implementation detail managed by the compiler, not hand-written.

**Q: How do reasoning models change prompting?**  
Models like o1, o3, Claude extended thinking, and DeepSeek R1 perform internal CoT — explicit CoT instructions and demonstrations are no longer necessary (and can be counterproductive). Prompting shifts to: clear task framing, output format, constraints, and context quality. Prompt engineering evolves rather than disappears.

**Q: What is LLM-as-Judge?**  
Using a strong LLM to evaluate outputs at scale for tasks where "correct" is not binary. Modes: criteria-based (score against a rubric), pairwise (which is better?), reference-based (compare to gold answer). Reliable for relative comparisons; less reliable for absolute scores.

---

## Tricky / Edge Cases

**Q: Why does adding "Let's think step by step" work even with no examples?**  
Instruction-tuned models were trained on step-by-step reasoning data. The trigger phrase activates that pattern without needing examples. The intermediate tokens serve as working memory for multi-step problems.

**Q: A model correctly identifies the answer in its reasoning but gives the wrong final answer. What happened?**  
The model may have reached the correct intermediate conclusion but then "overrode" it with a more probable completion — the final answer token prediction was pulled toward a different pattern in the training distribution. Fix: use answer extraction prompts ("Based on your reasoning above, the final answer is:") or few-shot examples showing correct answer extraction.

**Q: Why might an adversarial user provide a very long input to a RAG-augmented chatbot?**  
To push the system prompt and retrieved context into the "middle" of the context window, reducing the model's attention to them. A very long user-supplied document can effectively bury safety instructions and retrieved context, potentially making the model more susceptible to injection or hallucination. Mitigation: enforce input length limits; always place system instructions at the top of the context.

**Q: What does it mean for a prompt to "overfit" to a test set?**  
The prompt was optimized (manually or automatically) to perform well on specific test examples but fails on novel inputs from the production distribution. Signs: very high eval accuracy but significant production accuracy drop; the prompt contains very specific references to patterns in the test set. Prevention: use a held-out test set that is not accessible during prompt development, and monitor production accuracy independently.

**Q: Is prompt engineering still relevant with reasoning models?**  
Yes — it evolves. Reasoning models don't need CoT instructions, but still require: clear task framing (what counts as success), output format specification, context quality, evaluation, security, and cost optimization. The "tell the model how to think" part shrinks; the "define what you want and measure if you got it" part remains and may grow.
