# Smart Diagnostic Assistant — Orchestrator-Subagent Architecture
## Alternative Design: Version 2

> **Role:** Senior Platform Architect / AI Practice Lead
> **Question:** "A global automotive manufacturer wants to equip their 5,000 factory floor technicians with a Smart Diagnostic Assistant on phone or tablet. When a machine breaks down, the technician should be able to use the app to get step-by-step repair instructions. Design the end-to-end architecture."

---

## How I'd Open This in an Interview (2 min)

"Before I start drawing boxes, let me reframe what's actually hard here. Most candidates treat this as a
RAG problem — retrieve from manuals, generate instructions, done. But there are three constraints that
fundamentally change the architecture.

First, the knowledge needed for one diagnostic comes from three completely different sources that require
three different retrieval strategies: a graph database for machine history, a vector store for technical
manuals, and a structured rule store for safety standards. You can't do those three well with a single
retrieval agent.

Second, safety is non-negotiable. In a factory, a wrong diagnostic instruction doesn't fail gracefully —
it injures someone. That means safety validation has to be a separate, blocking stage, not something
blended into generation.

Third, those three retrieval operations are independent. They don't need each other's results. Running
them sequentially is wasted latency.

So the architecture I want to describe is an Orchestrator-Subagent flow with parallel fan-out:
Input → Data Processing Agent → Orchestrator → [three parallel specialist agents] → Validator → Synthesizer.
Let me walk through each stage."

---

## Why Orchestrator-Subagent Is the Right Pattern

This isn't a reflexive choice. Let me show the decision:

| Alternative Considered | Why It Doesn't Fit |
|------------------------|-------------------|
| **Single monolithic RAG agent** | One retrieval strategy can't serve graph traversal + vector search + structured lookup. You'd end up with one mediocre agent instead of three excellent ones. |
| **Pipeline (sequential)** | The three fetch operations are fully independent. Sequential execution adds ~4–6s with zero benefit. Pipeline is right when step N needs step N-1's output. |
| **Peer-to-peer multi-agent** | No peer coordination needed. The fetch agents don't need to communicate with each other. Unnecessary complexity. |
| **Orchestrator-Subagent + Parallel Fan-out** | ✅ Three independent specialists, run in parallel, results aggregated by a dedicated validator. Clean, explainable, and fast. |

The key property that makes Orchestrator-Subagent right: **the sub-agents are independent**. Legacy
history, OEM manuals, and safety SOPs don't depend on each other. The Orchestrator can dispatch all
three simultaneously and wait for all results.

---

## Clarifying Questions (5 min)

| Question | Why It Matters |
|----------|---------------|
| How many machine models? | Drives knowledge base size and offline pre-generation scope. 300 models × ~50 common failures = 15,000 pre-generated guides. |
| What format are the technical manuals? | PDFs need Document AI ingestion. Structured HTML is simpler. Determines chunking strategy for Vector Search. |
| What safety standards apply? | IEC 62443 for industrial control systems, NFPA 70E for electrical — each requires different validation rules in the SOPs agent. |
| Does your machine registry distinguish new vs. well-documented equipment? | Determines when the Orchestrator should skip the Legacy agent (new machines have no history). |
| What skill tiers do technicians have? | Tier 1–3 system means the Orchestrator must validate authorization before dispatching agents — a failed authorization should stop everything immediately. |
| Is there a CMMS (SAP PM, Maximo)? | If yes, the Synthesizer needs to create a work order as a side effect. Changes output format. |
| What's the WiFi coverage on the factory floor? | If patchy, offline-first is required for 5s SLA. Determines whether pre-generated guides are a nice-to-have or a hard requirement. |
| What languages? | Multilingual output changes both the Synthesizer prompt and the offline cache size. |

**Assumed answers for this design:** 300 machine models, PDF manuals (Document AI ingested), IEC 62443 +
NFPA 70E, SAP PM integration required, ~30% of floor has dead WiFi zones, English + Spanish output.

---

## Scale Reality Check

- **5,000 technicians**, not concurrent — peak load is **~200–300 simultaneous queries** during shift change
- **P99 target: < 5 seconds** — machine downtime costs $10k–$50k/hour, so every second matters
- **~300 machine models**, ~5M total document chunks across all OEM manuals
- **~15,000 pre-generated offline guides** (top-500 failure patterns × 30 machine families) at ~2GB per device

At 200–300 concurrent queries, with 5s P99 budget, this is perfectly achievable with Cloud Run autoscaling
— no exotic infrastructure needed.

---

## Full Architecture

```
Technician Input (voice / QR scan / photo)
        ↓
┌──────────────────────────────────────────────────────────────┐
│  STAGE 1: Data Processing Agent                               │
│                                                               │
│  Voice  ──→ Vertex AI Speech-to-Text ──→ problem description  │
│  Photo  ──→ Gemini Vision API ─────────→ failure symptoms     │
│  QR Code ─→ Equipment Registry lookup ─→ machine context      │
│                                                               │
│  Output: EquipmentContext {                                   │
│    equipment_id, machine_model, location,                     │
│    failure_description, symptom_tags[],                       │
│    technician_id, skill_tier                                  │
│  }                                                            │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│  STAGE 2: Orchestrator                                        │
│                                                               │
│  1. Classifies failure mode (Gemini Flash) + confidence score │
│  2. Authorization check: is tech's skill_tier sufficient?     │
│     → If no: return escalation immediately, skip all agents   │
│  3. Checks LOTO requirement for this failure class            │
│  4. Decides which agents to invoke:                           │
│     ┌─ SOPs & Safety: ALWAYS                                  │
│     ├─ RAG Manual Fetch: ALWAYS                               │
│     └─ Legacy & History: only if machine has repair history   │
│  5. Dispatches in parallel, holds shared state                │
│                                                               │
│  Shared state:                                                │
│  { equipment_id, failure_class, confidence,                   │
│    skill_tier, loto_required, agents_invoked[] }              │
└────────┬──────────────────┬──────────────────┬───────────────┘
         ↓ parallel         ↓ parallel         ↓ parallel
┌────────────────┐  ┌────────────────┐  ┌────────────────────┐
│  STAGE 3A      │  │  STAGE 3B      │  │  STAGE 3C          │
│  Legacy &      │  │  RAG Manual    │  │  SOPs & Safety     │
│  History Fetch │  │  Fetch Agent   │  │  Fetch Agent       │
│                │  │                │  │                    │
│ Spanner Graph: │  │ Vertex AI      │  │ Firestore:         │
│  machine →     │  │ Vector Search: │  │  LOTO procedures   │
│  failure mode  │  │  OEM manuals   │  │  IEC 62443 rules   │
│  → procedure   │  │  repair guides │  │  NFPA 70E reqs     │
│                │  │  parts catalog │  │  escalation limits │
│ BigQuery:      │  │                │  │  skill tier map    │
│  past repairs  │  │ Returns:       │  │                    │
│  MTTR history  │  │  top-k chunks  │  │ Returns:           │
│  tech notes    │  │  + source refs │  │  required safety   │
│                │  │  + confidence  │  │  steps, LOTO Y/N,  │
│ Returns:       │  │                │  │  escalation flags  │
│  similar cases │  │                │  │                    │
│  + outcomes    │  │                │  │                    │
└────────┬───────┘  └────────┬───────┘  └─────────┬──────────┘
         └──────────────┬────┘                     │
                        └───────────────┬───────────┘
                                        ↓ aggregate
┌──────────────────────────────────────────────────────────────┐
│  STAGE 4: Analyser, Validator & Standards Enforcer            │
│                                                               │
│  Conflict resolution (hard precedence order):                 │
│    SOPs & Safety  >  Historical outcomes  >  OEM Manual       │
│                                                               │
│  Validation checks (all blocking):                            │
│  ✓ LOTO completeness: if loto_required=true, Step 1 must be   │
│    lockout — non-negotiable, block synthesis if absent        │
│  ✓ Skill-tier authorization confirmed (second check)          │
│  ✓ IEC 62443 / NFPA 70E compliance                            │
│  ✓ Re-failure rate flag: if >20% of similar past repairs      │
│    failed within 30 days → attach warning, don't suppress     │
│  ✓ Auto-escalation: voltage >480V or confined space entry     │
│    → block synthesis, return escalation to supervisor         │
│                                                               │
│  Output: ValidatedDiagnosticContext {                         │
│    procedure_steps[], safety_steps[], parts_list[],           │
│    estimated_time_minutes, historical_success_rate,           │
│    sources[], escalation_required, warnings[]                 │
│  }                                                            │
└──────────────────────────────┬───────────────────────────────┘
                               ↓ (only if validation passed)
┌──────────────────────────────────────────────────────────────┐
│  STAGE 5: Synthesizer                                         │
│                                                               │
│  Generates (Gemini 1.5 Pro):                                  │
│  - Step-by-step repair procedure (mobile-optimized format)    │
│  - Safety warnings with regulatory citations                  │
│  - Parts list + quantities + SAP inventory status             │
│  - Time estimate from historical MTTR data                    │
│  - Source references (manual section + past repair IDs)       │
│  - Bilingual output (English + Spanish)                       │
│  - Offline-capable package (if technician's device on WiFi)   │
│                                                               │
│  Side effects:                                                │
│  - Creates SAP PM work order                                  │
│  - Logs event to BigQuery (for weekly feedback loop)          │
│  - Triggers parts pre-order if inventory < threshold          │
└──────────────────────────────────────────────────────────────┘
                               ↓
              Technician receives diagnostic guide
              (online: real-time stream / offline: cached)
```

---

## Stage-by-Stage Detail

### Stage 1 — Data Processing Agent

The technician's input is messy and multimodal. This agent's only job is to normalize it into a clean,
structured `EquipmentContext` object that every downstream agent can consume.

**Why a separate agent?** The Orchestrator shouldn't be parsing audio files. Clean separation of concerns
means the Orchestrator always receives a structured object — it never sees raw voice or images.

**Latency target:** < 500ms
- Speech-to-Text: ~200ms for a 10-second voice clip
- Gemini Vision: ~300ms for a single photo

**What happens when input is ambiguous?** If Gemini Vision returns `confidence < 0.6` on the failure
description, the Data Processing Agent asks the technician one clarifying question before producing the
`EquipmentContext`. This adds latency but prevents the Orchestrator from misclassifying based on a blurry
photo.

---

### Stage 2 — Orchestrator

The Orchestrator is the control plane. It makes decisions; the sub-agents do retrieval.

**Failure classification with Gemini Flash:**

```python
classification_prompt = f"""
Equipment: {context.machine_model} ({context.equipment_id})
Problem description: {context.failure_description}
Symptom tags: {context.symptom_tags}

Classify the failure mode from this list: {FAILURE_MODE_TAXONOMY}
Return: { "failure_class": str, "confidence": float, "loto_required": bool }
"""
```

If `confidence < 0.75`, the Orchestrator invokes all three sub-agents (safe default) and flags the
output for tech confirmation. This prevents a low-confidence classification from narrowing retrieval
prematurely.

**Dynamic agent selection:**

```python
agents_to_invoke = ["sops_safety", "rag_manual"]  # always

if equipment_registry.has_repair_history(context.equipment_id):
    agents_to_invoke.append("legacy_history")

# Dispatch in parallel
results = await asyncio.gather(*[
    invoke_agent(agent, context) for agent in agents_to_invoke
])
```

Skipping the Legacy agent for new machines isn't just about latency — an empty Spanner query that returns
"no history found" can confuse the Validator with an empty input. Cleaner to skip it entirely when the
machine is new.

---

### Stage 3A — Legacy & History Fetch Agent

**What it does:** Finds similar past failures on the same machine (or same model family) and retrieves
what procedures were used and what the outcomes were.

**Why Spanner Graph?** The knowledge structure is inherently relational:
`machine → failure_mode → procedure → outcome → technician_notes`. Graph traversal is the natural
retrieval strategy. Vector search would return semantically similar text, not structurally related failure
chains.

**Query pattern:**

```python
# Find similar failures on same model in last 18 months
query = """
GRAPH machine_repair_graph
MATCH (m:Machine {model: $model})
     -[:HAD_FAILURE]-> (f:FailureEvent {class: $failure_class})
     -[:USED_PROCEDURE]-> (p:Procedure)
     -[:PRODUCED_OUTCOME]-> (o:Outcome)
WHERE f.timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 18 MONTH)
RETURN p.steps, o.success, o.mttr_minutes, o.technician_notes
ORDER BY o.timestamp DESC
LIMIT 10
"""
```

**What it returns:** Top-10 most recent similar cases, each with procedure used, success/failure, MTTR,
and technician notes. The Validator will use the success rate to flag if a procedure has a bad track record.

---

### Stage 3B — RAG Manual Fetch Agent

**What it does:** Semantic search over the OEM technical manuals and repair guides for this machine model,
returning the most relevant procedure sections.

**Why Vertex AI Vector Search?** The manuals are unstructured PDFs. Semantic similarity is the right
retrieval strategy — "hydraulic pump cavitation" in the technician's description needs to match
"cavitation in piston pump assemblies" in the manual. Keyword search would fail.

**Retrieval strategy:**

```python
# Hybrid: sparse (BM25) + dense (embedding) retrieval
query_embedding = embed_model.embed(context.failure_description)
results = vector_search.find_neighbors(
    embedding=query_embedding,
    filter=f"machine_model = '{context.machine_model}'",
    num_neighbors=20
)

# Re-rank by confidence + chunk recency (newer manual version wins)
top_chunks = reranker.rerank(results, context.failure_description, top_k=5)
```

**Chunk size:** 512 tokens. Smaller chunks increase precision (fewer irrelevant sentences retrieved).
Overlap of 50 tokens preserves context across chunk boundaries.

**What it returns:** Top-5 chunks with source reference (manual name, section, page) and confidence score.
If the top chunk confidence is < 0.7, the Validator will flag this in the output.

---

### Stage 3C — SOPs & Safety Fetch Agent

**What it does:** Retrieves the relevant safety requirements, LOTO procedures, and regulatory constraints
for this failure class and machine type.

**Why Firestore, not vector search?** Safety rules are structured, not fuzzy. "LOTO required for electrical
failures on 480V systems" is a hard lookup, not a semantic search. Firestore gives consistent, predictable
retrieval. Vector search would introduce non-determinism into safety-critical lookups — unacceptable.

**Lookup pattern:**

```python
# Structured safety rule lookup
safety_rules = firestore.collection("safety_rules").where(
    "applicable_failure_classes", "array_contains", context.failure_class
).where(
    "machine_voltage_class", "==", equipment.voltage_class
).get()

loto_procedure = firestore.collection("loto_procedures").document(
    f"{context.machine_model}_{context.failure_class}"
).get()

skill_tier_requirement = firestore.collection("skill_tier_map").document(
    context.failure_class
).get()
```

**What it returns:** Required safety steps, LOTO procedure (if required), applicable regulatory standards,
escalation thresholds, and minimum skill tier for this repair. This agent never returns "not found" —
if there are no specific safety rules for a failure class, it returns the default safety baseline.

---

### Stage 4 — Analyser, Validator & Standards Enforcer

This is the most important stage. **No procedure reaches the Synthesizer without passing validation.**

**Why a separate stage and not part of the Synthesizer?** In industrial systems, "generate then validate"
is architecturally wrong. An LLM can generate a plausible-sounding procedure that subtly violates a
safety standard. By the time the validator catches it post-generation, you've spent compute and time. And
more importantly: you never want unsafe content to even reach the output pipeline, even briefly.
Validate first. Synthesize only validated context.

**Conflict resolution (strict precedence):**

| Priority | Source | Rationale |
|----------|--------|-----------|
| 1st (highest) | SOPs & Safety Fetch | Regulatory requirements are non-negotiable |
| 2nd | Legacy & History Fetch | Real-world outcomes from the same machine > theory |
| 3rd (lowest) | RAG Manual Fetch | OEM manuals may be outdated or generic |

If the historical agent says "procedure A worked 90% of the time" and the SOPs agent says "procedure A
requires LOTO Step 1 which was missing in past repairs", SOPs win. The Validator will note the discrepancy
in the output and recommend a knowledge base update.

**LLM-as-judge for semantic cross-validation (Gemini Flash):**

Pure rule engines catch known violations. The LLM-as-judge catches semantic contradictions that rules
can't encode — for example, the manual saying "remove power before servicing" while the SOPs agent
notes "this circuit cannot be de-energized during operation due to redundancy requirements." A rule
engine can't catch that. A cross-validation LLM prompt can.

```python
cross_validation_prompt = f"""
You are a safety engineer reviewing a proposed repair procedure.

Manual procedure: {manual_procedure}
Historical outcomes: {historical_context}
Safety requirements: {safety_requirements}

Identify any contradictions or safety gaps. Be specific.
Return: { "contradictions": [str], "safety_gaps": [str], "pass": bool }
"""
```

**Hard blocks (these always stop synthesis):**

- LOTO required but no lockout step present in procedure
- Tech's skill tier below the minimum for this repair class
- Voltage > 480V (requires Level 3 licensed electrician — escalate)
- Confined space entry required (requires permit and standby — escalate)
- SOPs agent returned an error or timed out (safety data unavailable = no synthesis)

---

### Stage 5 — Synthesizer

Only reaches this stage with a `ValidatedDiagnosticContext` that has passed all checks. Clean input,
clean output.

**Prompt structure:**

```python
synthesis_prompt = f"""
You are generating a step-by-step diagnostic and repair guide for a factory technician.

Equipment: {validated.machine_model} — {validated.failure_class}
Technician skill tier: {validated.skill_tier}

SAFETY REQUIREMENTS (non-negotiable, must appear first):
{validated.safety_steps}

PROCEDURE (from validated sources):
{validated.procedure_steps}

HISTORICAL CONTEXT:
Success rate for this procedure: {validated.historical_success_rate}%
Average completion time: {validated.estimated_time_minutes} min
Technician notes from past repairs: {validated.tech_notes_summary}

PARTS REQUIRED:
{validated.parts_list}

SOURCES:
{validated.sources}

Generate a mobile-formatted guide. Use numbered steps. Safety warnings in ALL CAPS.
Include time estimate. Include parts list. Include source references at the bottom.
Output in English, then repeat in Spanish.
"""
```

**Side effects (all async, non-blocking):**

- SAP PM work order creation (fire-and-forget, doesn't delay guide delivery)
- BigQuery diagnostic event log (for weekly feedback analysis)
- Parts pre-order trigger if inventory < 2 units (Pub/Sub message to procurement system)

---

## GCP Services Map

| Agent / Stage | Service | Why |
|---|---|---|
| Data Processing Agent | Vertex AI Speech-to-Text | Industry-leading accuracy for noisy factory environments |
| Data Processing Agent | Gemini Vision API | Multimodal failure symptom extraction |
| Data Processing Agent | Firestore (equipment registry) | Fast key-value lookup for machine context by QR code |
| Orchestrator | Gemini Flash (classification) | Fast, cheap — failure classification is a classification task, not generation |
| Orchestrator | Vertex AI ADK or LangGraph on Cloud Run | Agent framework for state management + parallel dispatch |
| Legacy & History Fetch | Cloud Spanner | Graph-capable, strongly consistent, globally distributed |
| Legacy & History Fetch | BigQuery | Analytical queries on repair history at scale |
| RAG Manual Fetch | Vertex AI Vector Search | Managed ANN search over 5M document chunks |
| RAG Manual Fetch | Cloud Storage | Stores document chunks + original PDFs |
| SOPs & Safety Fetch | Firestore | Structured safety rules with real-time consistency |
| Analyser / Validator | Cloud Run (rule engine) | Deterministic safety checks, not LLM |
| Analyser / Validator | Gemini Flash (LLM-as-judge) | Semantic contradiction detection |
| Synthesizer | Gemini 1.5 Pro | Full procedure generation, long-context window |
| Synthesizer | SAP PM API | Work order creation |
| Synthesizer | BigQuery (event log) | Feedback loop data |
| Offline delivery | Cloud Storage + Cloud CDN | Pre-generated guide cache delivery |
| Offline delivery | Firebase offline sync | Device-local caching for dead-WiFi zones |
| Observability | Cloud Trace | Distributed tracing across all 5 stages |
| Observability | Cloud Monitoring | Latency, error rate, per-agent SLOs |
| Knowledge ingestion | Document AI | PDF → structured chunks for Vector Search |
| Knowledge ingestion | Dataflow | Batch ingestion pipeline for manual updates |

---

## Latency Budget Breakdown

| Stage | Target | Why Achievable |
|-------|--------|----------------|
| Data Processing Agent | ~500ms | Speech-to-Text + Vision in parallel |
| Orchestrator (classification) | ~400ms | Gemini Flash, simple classification |
| Orchestrator (dispatch overhead) | ~100ms | Async dispatch, minimal compute |
| Parallel sub-agents (slowest of 3) | ~1.5s | Vector Search + graph query both under 1.5s at this scale |
| Analyser / Validator | ~500ms | Rule checks are fast; LLM-as-judge adds ~300ms |
| Synthesizer | ~1.5s | Gemini 1.5 Pro for ~500-token output |
| **Total P99** | **< 5s** | All stages sequential except fan-out |

The parallel fan-out in Stage 3 is the key latency win. Sequential execution of three agents would cost
~4–5s for Stage 3 alone, blowing the budget. In parallel, Stage 3 costs only as long as the slowest
individual agent.

---

## Interviewer Probes — Strong Answers

| Probe | Strong Answer |
|-------|--------------|
| "How does the Orchestrator decide which agents to call?" | Classification result + machine registry check. SOPs and RAG always. Legacy only if machine has repair history. If confidence < 0.75, invoke all three regardless. |
| "What's the conflict resolution protocol?" | Strict precedence: SOPs > History > Manual. Documented, not emergent. Validator applies it deterministically, not via LLM judgment. |
| "What happens if the SOPs agent is down?" | Hard block. Safety data is required before synthesis. The system returns an escalation message, not a degraded answer. |
| "What happens if the Legacy agent returns nothing?" | Synthesizer generates from manual + SOPs only. Output notes "no historical data available for this failure pattern." Valid degraded mode. |
| "Why not one big RAG agent over all three knowledge sources?" | Each source requires a different retrieval strategy. Spanner needs graph traversal. Manuals need semantic vector search. SOPs need structured lookup. One agent doing all three poorly is worse than three agents each doing one thing well. |
| "How do you prevent the Orchestrator from misclassifying and sending techs down the wrong path?" | Confidence threshold (< 0.75 = invoke all agents + flag). Post-repair feedback loop surfaces systematic misclassifications within one week. And the Validator catches procedure mismatches even when classification is off. |
| "What's the state schema the Orchestrator holds?" | `{ equipment_id, machine_model, failure_class, confidence, skill_tier, loto_required, agents_invoked[], agent_results{}, timestamp }` — each agent writes to `agent_results` independently. |
| "Why is the Validator a separate stage and not part of the Synthesizer?" | Safety enforcement must happen before generation. "Generate then validate" is a safety anti-pattern in industrial settings. Validation also needs to see all three agent outputs simultaneously — the Synthesizer's scope is too narrow. |
| "How does this handle a brand-new machine that just arrived on the floor?" | Equipment registry shows no history. Orchestrator skips Legacy agent. RAG Manual Fetch retrieves from newly ingested OEM manuals. SOPs apply defaults for the machine class. Synthesizer generates from manuals + SOPs with explicit note that no historical data exists. |

---

## Trade-offs

| Trade-off | Decision Made | Reasoning |
|-----------|--------------|-----------|
| Orchestrator-Subagent vs. single agent | Orchestrator-Subagent | Three different retrieval strategies require three specialized agents |
| Parallel fan-out vs. sequential | Parallel | Agents are fully independent; sequential would add ~4s for no benefit |
| Dynamic agent selection vs. always invoke all three | Dynamic | New machines have no history; invoking Legacy and getting empty results wastes latency and confuses Validator |
| Validate before synthesize vs. validate after | Before | Industrial safety anti-pattern to generate first; validate before synthesis is non-negotiable |
| LLM-as-judge vs. pure rule engine in Validator | Hybrid | Rules for known violations; LLM for semantic contradictions between sources |
| Offline capability via pre-generation | Pre-generate top-500 failure patterns per machine family | 5s P99 is impossible if WiFi required; factory floors have dead zones |
| Gemini Flash for classification vs. Pro | Flash | Classification is a classification task — Pro capability not needed; Flash is 10× cheaper and faster |
| Spanner Graph vs. Neo4j | Spanner | GCP-native, managed, ACID transactions, globally consistent; Neo4j would require separate management |

---

## Failure Scenarios

| Failure | Impact | Mitigation |
|---------|--------|-----------|
| Legacy Fetch agent times out | No historical context | Synthesizer generates from manual + SOPs with "no historical data" note — valid degraded mode |
| RAG Manual Fetch returns confidence < 0.7 | Weak procedural basis | Validator attaches explicit low-confidence warning; Synthesizer adds supervisor review flag |
| SOPs agent unavailable | Safety validation impossible | **Hard block** — return escalation to supervisor, do not attempt synthesis |
| Orchestrator misclassifies failure (confidence < 0.75) | Wrong agents invoked | Invoke all three agents regardless + require tech to confirm failure description before displaying output |
| Validator finds conflicting safety data (unresolvable) | Synthesis blocked | Return escalation with conflict details — supervisor must manually resolve, system logs for knowledge base update |
| Gemini 1.5 Pro (Synthesizer) slow or degraded | Latency exceeds 5s | Pre-generated offline guide served from cache (covers ~85% of common failures) |
| SAP PM API fails | Work order not created | Synthesizer completes — work order failure logged to BigQuery for async retry. Guide delivery is not blocked by SAP. |

---

## What's Different from Version 1

| Aspect | Version 1 (Monolithic Agent) | Version 2 (Orchestrator-Subagent) |
|--------|------------------------------|----------------------------------|
| Architecture pattern | Single Diagnostic Agent with hybrid RAG | Orchestrator + 3 specialist sub-agents + Validator |
| Retrieval | One agent mixes graph + vector + structured lookup | Each agent uses the optimal strategy for its knowledge type |
| Safety enforcement | Safety gates within the Diagnostic Agent | Dedicated Validator stage — hard block before generation |
| Parallelism | Sequential retrieval steps | True parallel fan-out across all three knowledge agents |
| Agent selection | Fixed: always retrieve everything | Dynamic: skip Legacy for new machines, confidence-gated |
| Conflict resolution | Implicit in single agent | Explicit precedence: SOPs > History > Manual |
| Failure graceful degradation | Partial | Explicit: each agent failure has a defined degraded mode |
| Interview signal | Competent | Advanced — demonstrates Orchestrator-Subagent judgment |

Both versions produce the same end result. Version 2 is more complex to implement but is significantly
more explainable, more reliable, and more defensible in a senior ML system design interview.

---

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| End-to-end P99 latency | < 5 seconds | Cloud Trace, sampled per request |
| Diagnostic accuracy (validated post-repair) | ≥ 92% | Weekly BigQuery analysis of repair outcomes |
| First-time fix rate | ≥ 75% | SAP PM re-open rate within 7 days |
| LOTO compliance rate | 100% | Validator hard-block ensures this at the system level |
| Validator block rate (conflicting safety data) | < 2% | High rate indicates knowledge base gaps needing curation |
| Sub-agent parallel execution overhead | < 100ms vs. slowest single agent | Cloud Trace parallel span comparison |
| Offline cache hit rate | ≥ 85% | Firebase analytics — cache hit vs. miss per request |
| SOPs agent availability | ≥ 99.9% | Firestore SLA + Cloud Monitoring alerts |

---

## Pre-Deployment Checklist

- [ ] Knowledge base loaded: all 300 machine model manuals ingested via Document AI + Dataflow
- [ ] Spanner Graph schema validated: machine → failure → procedure → outcome paths correct
- [ ] Safety rules loaded: IEC 62443 + NFPA 70E rules in Firestore, reviewed by safety engineer
- [ ] Skill tier map complete: all failure classes mapped to required tier levels
- [ ] LOTO procedures loaded for all 300 models
- [ ] Orchestrator classification tested on 100+ historical failure descriptions (≥90% accuracy required)
- [ ] Validator tested against 50 synthetic conflicting-source scenarios
- [ ] Offline cache pre-generated for top-500 failure patterns
- [ ] SAP PM API integration tested in staging environment
- [ ] Cloud Trace configured with per-agent span labels
- [ ] Escalation paths tested: supervisor notification working end-to-end
- [ ] P99 latency load test at 300 concurrent requests passing < 5s target
