# Agentic System: Insurance Claims Processor

**Problem Statement:** Design an agentic system that helps an insurance company process claims against their homeowner's policy more quickly.

---

## Clarifying Questions (asked before designing)

The problem is intentionally vague. These questions must be answered before committing to a design:

| Question | Why It Matters |
|---|---|
| What evidence does the claimant submit? (photos, videos, police reports, written descriptions?) | Determines whether we need vision, audio transcription, or document parsing capabilities |
| Which legacy systems must the agent interface with? (Claims Management System, CRM, policy DB?) | Defines the integration surface — tools the agents need to call |
| Has an insurance assessor already visited the site? | If yes, we have a structured assessment report; if no, the agent must infer damage from raw evidence alone |
| What is the claim value threshold for auto-approval vs. mandatory human review? | Sets the HITL escalation policy |
| What data is available on past claims? (for fraud detection and cost benchmarking) | Determines viability of RAG-based retrieval vs. fine-tuning |

---

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLAIMANT INTERFACE                             │
│         Web Portal / Mobile App / Phone (IVR + Transcription)        │
│                                                                       │
│   Submits: photos · videos · police report · written description     │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    SECURITY & INGESTION LAYER                         │
│                                                                       │
│   • PII Redaction: strip names, addresses, policy numbers from       │
│     evidence before passing to LLMs                                  │
│   • Prompt Injection Guard: sanitize free-text fields                │
│   • Fraudulent Imagery Detection: EXIF metadata check,              │
│     reverse image search for stock/recycled photos                   │
│   • Evidence stored in secure object store (encrypted at rest)       │
└──────────────────────────────┬───────────────────────────────────────┘
                               │  Sanitised claim package
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       ORCHESTRATOR AGENT                              │
│                                                                       │
│   Model: Multi-modal Foundation Model (e.g., Gemini / Claude)        │
│   Pattern: Plan → Dispatch → Reflect → Synthesize                    │
│                                                                       │
│   • Creates claim context window (shared state for all sub-agents)   │
│   • Dispatches to specialist sub-agents in parallel                  │
│   • Detects conflicts between sub-agent findings (see below)         │
│   • Applies escalation rules → routes to HITL or auto-decision       │
│   • Interfaces with legacy CMS and CRM via tool calls                │
└──────┬─────────────────┬──────────────────────┬───────────────────┬──┘
       │                 │                      │                   │
       ▼                 ▼                      ▼                   ▼
┌────────────┐   ┌────────────────┐   ┌─────────────────┐  ┌─────────────────┐
│  DAMAGE    │   │    POLICY      │   │  COST ESTIMATOR │  │  LEGACY SYSTEM  │
│  ANALYST   │   │   AUDITOR      │   │    (sub-task     │  │   CONNECTOR     │
│            │   │                │   │  of Synthesizer) │  │                 │
│ • Ingests  │   │ • Pulls active │   │ • Looks up       │  │ • Reads/writes  │
│   photos,  │   │   policy at    │   │   repair cost    │  │   Claims Mgmt   │
│   videos,  │   │   date of loss │   │   benchmarks     │  │   System (CMS)  │
│   reports  │   │ • Checks       │   │   from RAG DB    │  │ • Reads CRM for │
│ • Uses     │   │   coverage     │   │ • Applies        │  │   claimant      │
│   vision   │   │   limits,      │   │   ACV or RCV     │  │   history       │
│   model to │   │   deductibles, │   │   per policy     │  │ • Updates claim │
│   classify │   │   exclusions   │   │ • Produces       │  │   status in CMS │
│   damage:  │   │ • Flags gaps   │   │   itemised cost  │  │                 │
│   water /  │   │   in coverage  │   │   estimate       │  │                 │
│   fire /   │   │ • Returns      │   │ • Proposes       │  │                 │
│   impact   │   │   structured   │   │   settlement     │  │                 │
│ • Assesses │   │   policy       │   │   offer draft    │  │                 │
│   severity │   │   summary      │   │   for adjuster   │  │                 │
│   (minor / │   │                │   │                  │  │                 │
│   moderate │   │                │   │                  │  │                 │
│   /major)  │   │                │   │                  │  │                 │
└─────┬──────┘   └───────┬────────┘   └────────┬─────────┘  └────────┬────────┘
      │                  │                     │                     │
      └──────────────────┴──────────────┬──────┘                     │
                                        │                            │
                                        ▼                            │
┌──────────────────────────────────────────────────────────────────────────────┐
│                          SYNTHESIZER AGENT                                    │
│                                                                               │
│   Combines: damage classification + severity + policy coverage +             │
│             cost estimate + claimant history from CRM                        │
│                                                                               │
│   Outputs a structured recommendation with fraud risk score:                 │
│                                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  RECOMMENDATION  │  CONDITIONS                                       │   │
│   ├─────────────────────────────────────────────────────────────────────┤   │
│   │  ✅ Approve Claim │  Damage confirmed · Covered · Fraud risk: LOW    │   │
│   │  ℹ️ Request Info  │  Evidence incomplete · Policy gap unclear        │   │
│   │  🔍 Dispatch      │  High severity · Fraud risk: MED/HIGH · Complex  │   │
│   │     Human         │  conflict between evidence and claimed damage    │   │
│   │     Assessor      │                                                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│   CONFLICT RESOLUTION LOGIC (built into Synthesizer):                        │
│   • Photo shows MINOR damage + text claims MAJOR → flag discrepancy,         │
│     downgrade recommendation, escalate to human adjuster                     │
│   • Date on EXIF metadata ≠ claimed date of loss → fraud flag raised        │
│   • Cost estimate far exceeds regional benchmark → soft flag + justification │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ✅ Auto-Approve       ℹ️ Request Info    🔍 Escalate to
    (HITL light-touch)    Claimant notified   Human Adjuster
    Adjuster sees         via portal;         Full package:
    summary + can         claim paused        damage report +
    override within                           policy summary +
    48hrs                                     settlement offer
                                              draft + fraud score
           │                   │                   │
           └───────────────────┴───────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │        NOTIFICATION AGENT       │
              │                                │
              │  • Updates CMS claim status    │
              │  • Emails / SMS claimant       │
              │  • Triggers payment if approved│
              │  • Refers approved contractors │
              └────────────────────────────────┘
```

---

## Agent Breakdown

### 1. Orchestrator Agent
**Model:** Multi-modal foundation model (e.g., Gemini 1.5 Pro or Claude) — chosen over separate NLP + Vision silos because a single model maintains coherent reasoning across text and image evidence without context loss between handoffs.

| Responsibility | Details |
|---|---|
| Context management | Creates and maintains the shared claim context window across all sub-agents |
| Parallel dispatch | Runs Damage Analyst + Policy Auditor + Legacy Connector simultaneously |
| Conflict detection | Compares sub-agent outputs for discrepancies before passing to Synthesizer |
| Escalation logic | Routes outcome to auto-approve, request-info, or human adjuster paths |
| Legacy integration | Tool calls to CMS (update claim status) and CRM (read claimant history) |

### 2. Damage Analyst
**Model:** Multi-modal foundation model (same model as Orchestrator — no separate vision silo)
**Tools:** Vision analysis, weather event API, EXIF metadata extractor

- Ingests all unstructured evidence: photos, videos, police reports, written descriptions
- Classifies damage **type**: water / fire / impact / theft / wind
- Classifies damage **severity**: minor / moderate / major / total loss
- Corroborates date and cause against weather records
- Flags if imagery metadata (EXIF timestamps, GPS) conflicts with the claim narrative

### 3. Policy Auditor
**Model:** LLM with RAG over policy documents
**Tools:** Policy DB API, coverage rules engine

- Pulls the claimant's active policy at the exact date of loss
- Checks which perils are covered, deductibles, sub-limits (jewelry, electronics), exclusions
- Returns a structured policy summary the Synthesizer can reason over
- Does **not** make a coverage decision — it surfaces facts for the Synthesizer

### 4. Cost Estimator (sub-task within Synthesizer flow)
**Tools:** RAG over repair cost database (Xactimate / regional benchmarks), depreciation tables

- Retrieves comparable repair costs from a RAG database — avoids hallucinated cost estimates
- Applies ACV (Actual Cash Value) or RCV (Replacement Cost Value) per policy terms
- Produces an itemised cost estimate
- Drafts a preliminary settlement offer amount for the human adjuster to review

### 5. Synthesizer Agent
**Model:** LLM reasoning over structured inputs from all other agents

Combines: damage type + severity + policy coverage + cost estimate + claimant history from CRM

Outputs one of three structured recommendations with a **fraud risk score (Low / Medium / High)**:

| Recommendation | Trigger Conditions |
|---|---|
| **Approve Claim** | Damage confirmed · Covered by policy · Cost reasonable · Fraud risk: Low |
| **Request More Information** | Evidence incomplete · Policy gap ambiguous · Claimant hasn't responded |
| **Dispatch Human Assessor** | High severity · Fraud risk Medium/High · Evidence-claim conflict detected |

**Conflict Resolution Logic** built into the Synthesizer:
- Photo evidence shows **minor** damage but claimant text describes **major** loss → flag discrepancy, downgrade recommendation, require adjuster sign-off
- EXIF date on photos does not match claimed date of loss → raise fraud flag
- Cost estimate significantly exceeds regional benchmark → soft flag with justification required

### 6. Legacy System Connector
**Tools:** CMS API, CRM API

- Reads full claimant history from CRM (prior claims, disputes, payment history)
- Writes claim status updates back to the Claims Management System at each lifecycle transition
- Decouples agent logic from legacy system specifics — all agents interact through this connector

### 7. Notification Agent
**Tools:** Email API, SMS gateway, customer portal CMS, contractor referral DB

- Sends status updates at each lifecycle transition
- Delivers decision letter and settlement offer to claimant
- Triggers payment processing for approved claims
- Provides list of approved contractors for repairs

---

## Model Selection: Build vs. Buy

| Decision | Choice | Rationale |
|---|---|---|
| NLP + Vision | **Single multi-modal model** (Gemini / Claude) | Avoids context loss between separate NLP and vision silos; one model reasons coherently across text and image |
| Build vs. fine-tune | **General-purpose model + RAG** | Start with a capable foundation model retrieving from a policy and cost database; fine-tune only once evidence shows generalisation failures at scale |
| RAG for cost data | **RAG over Xactimate / regional benchmarks** | Keeps cost estimates grounded in real data; avoids hallucination of repair costs |

---

## Safety & Human-Centric Design

### Human-in-the-Loop (HITL)
The agent is explicitly **decision support**, not a decision maker. The final approval always rests with a human adjuster:

- **Auto-approve path**: Adjuster receives a summary and retains a 48-hour override window
- **Escalation path**: Adjuster receives the full package — damage report, policy summary, cost estimate, fraud score, and a draft settlement offer to accept, modify, or reject

### Conflict Resolution
| Conflict Type | System Response |
|---|---|
| Photo shows minor damage; text claims major | Flag discrepancy · Downgrade recommendation · Escalate to adjuster |
| EXIF timestamp ≠ claimed date of loss | Raise fraud flag · Require adjuster review before any payout |
| Cost estimate >> regional benchmark | Soft flag · Synthesizer must include justification in recommendation |
| Policy exclusion partially applies | Policy Auditor surfaces ambiguity · Synthesizer escalates rather than decides |

### Security
| Threat | Mitigation |
|---|---|
| PII exposure to LLMs | PII redacted in Security Layer before any evidence reaches a model |
| Prompt injection via free-text claim fields | Input sanitisation in Security Layer; system prompt isolation |
| Fraudulent imagery (stock photos, recycled images) | EXIF metadata check + reverse image search at ingestion |
| Adversarial image manipulation | Perceptual hash comparison against known fraud imagery DB |

---

## Data Flow

```
Claimant submits evidence
        │
        ▼
Security Layer: PII redaction · prompt injection guard · image auth check
        │
        ▼
Orchestrator creates claim context window
        │
        ├──► [PARALLEL] Damage Analyst ──────► damage type + severity + flags
        ├──► [PARALLEL] Policy Auditor ──────► coverage summary + exclusions
        └──► [PARALLEL] Legacy Connector ───► claimant history from CRM
        │
        ▼ (all three complete)
Cost Estimator ──► itemised repair cost + draft settlement offer
        │
        ▼
Synthesizer ──► conflict detection ──► recommendation + fraud risk score
        │
   ┌────┴──────────┬──────────────────┐
   │               │                  │
Approve        Request Info      Dispatch Assessor
(HITL light)   (notify claimant) (full package to adjuster)
   │               │                  │
   └───────────────┴──────────────────┘
                   │
        Notification Agent ──► claimant + CMS update + payment trigger
```

---

## Claim State Machine

```
SUBMITTED ──► EVIDENCE_REVIEW ──► PENDING_INFO ──► EVIDENCE_REVIEW
                    │
                    ▼
             SYNTHESIZING
                    │
        ┌───────────┼────────────────┐
        │           │                │
   AUTO_APPROVED  AWAITING_INFO  AWAITING_ASSESSOR
        │                            │
        └────────────┬───────────────┘
                     │
               ADJUSTER_REVIEW
                     │
              ┌──────┴──────┐
           APPROVED       DENIED
              │               │
              └──────┬────────┘
                   CLOSED
```

---

## Artifacts

| Artifact | Location |
|---|---|
| This architecture doc | `README.md` |
| Agent prompt designs | `artifacts/agent-prompts.md` |
| State machine definition | `artifacts/state-machine.md` |
| Tool schemas | `artifacts/tool-schemas.md` |
| Diagrams (Mermaid source) | `diagrams/` |

---

## Next Steps

- [ ] Define prompts for Damage Analyst, Policy Auditor, and Synthesizer
- [ ] Specify tool schemas for CMS and CRM connectors
- [ ] Build RAG index over sample policy documents and repair cost data
- [ ] Prototype Synthesizer conflict resolution logic on sample claims
- [ ] Evaluate Gemini 1.5 Pro vs. Claude on multi-modal damage classification accuracy
