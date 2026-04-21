# Agentic System: Prior Authorization Workflow

## Interview Problem Statement

> **"A national health insurer wants to reduce prior authorization processing time from an average of 3–5 business days to under 4 hours for its provider network of 50,000 physicians. Design an agentic system to support the end-to-end prior authorization workflow. Please draw the architecture."**

### Why this wording works as an interview question

| Design choice | Rationale |
|---|---|
| "National health insurer" | Stakes are clear; HIPAA/PHI compliance is implied but not stated |
| "50,000 physicians" | Forces scale thinking without prescribing exact request volume |
| "3–5 days → under 4 hours" | Gives a concrete goal while leaving implementation fully open |
| "Support the workflow" | Intentionally vague — candidate must ask: support *whom*? Providers? Reviewers? Both? |
| No mention of evidence type | Forces clarifying question on EHR, imaging, notes |
| No mention of legacy systems | Forces clarifying question on Epic, fax, payer portals |

---

## Clarifying Questions (asked before designing)

Prior authorization is a multi-stakeholder workflow. These questions must be answered before committing to a design:

| Question | Why It Matters |
|---|---|
| Who submits the PA request — provider staff, EHR auto-trigger, or both? | Determines the intake surface and whether the system needs an EHR integration vs. a standalone portal |
| What clinical evidence is available digitally? (EHR notes, lab results, imaging reports, medication history) | Defines what the Evidence Aggregator must fetch and in what formats (FHIR, PDF, HL7) |
| Are payer policy documents structured (JSON criteria sets) or unstructured (PDF clinical guidelines)? | Structured criteria → rules engine; unstructured → RAG over PDFs; most real deployments need both |
| Which EHR platforms must the system integrate with? (Epic, Cerner, etc.) Is fax still in use? | Defines the Legacy System Connector's complexity; fax is still dominant in US healthcare |
| Are there urgency tiers — standard, expedited, concurrent/urgent? | Same pipeline but priority queue routing; urgent PAs need a near-real-time path |
| What is the scope? (medications, procedures, imaging, DME, or all authorization types?) | Each type has different policy criteria structures and evidence requirements |

---

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         SUBMISSION SURFACE                                        │
│                                                                                   │
│   ┌──────────────────┐   ┌──────────────────┐   ┌───────────────────────────┐   │
│   │  Provider Portal  │   │  EHR Auto-Trigger │   │  Fax / Legacy Payer       │   │
│   │  (web / mobile)   │   │  (Epic / Cerner   │   │  Portal Ingestion         │   │
│   │  Staff-submitted  │   │   FHIR R4 event)  │   │  (OCR + eFax gateway)    │   │
│   └────────┬──────────┘   └────────┬──────────┘   └──────────────┬────────────┘  │
└────────────┼──────────────────────┼─────────────────────────────┼───────────────┘
             │                      │                             │
             └──────────────────────┴──────────────┬─────────────┘
                                                   │  PA request + metadata
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY & COMPLIANCE LAYER                                    │
│                                                                                   │
│   • PHI De-identification: strip / tokenize patient identifiers before           │
│     passing clinical text to any cloud LLM                                       │
│   • Prompt Injection Guard: sanitise all free-text clinical note fields          │
│   • BAA Verification: confirm model provider has signed Business Associate       │
│     Agreement before routing PHI; route to on-prem model if not                 │
│   • Audit Log Init: create immutable audit record for this PA request            │
│     (required for HIPAA and appeals traceability)                                │
└──────────────────────────────┬───────────────────────────────────────────────────┘
                               │  Sanitised PA package + urgency flag
                               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                       ORCHESTRATOR AGENT                                          │
│                                                                                   │
│   Model: Multi-modal Foundation Model (Claude / Gemini)                          │
│   Pattern: Plan → Dispatch → Reflect → Route                                     │
│                                                                                   │
│   • Creates PA context window shared across all sub-agents                       │
│   • Routes to URGENT queue (target: 4hr) or STANDARD queue (target: 24hr)       │
│   • Dispatches Evidence Aggregator + Policy Interpreter in parallel              │
│   • Detects conflicts between evidence and policy findings                       │
│   • Applies escalation rules before routing to reviewer                          │
└──────┬──────────────────────────┬──────────────────────────────────────┬─────────┘
       │                          │                                      │
       ▼                          ▼                                      ▼
┌─────────────────┐   ┌───────────────────────┐             ┌───────────────────────┐
│    EVIDENCE     │   │     POLICY            │             │  LEGACY SYSTEM        │
│   AGGREGATOR    │   │    INTERPRETER        │             │   CONNECTOR           │
│                 │   │                       │             │                       │
│ • Fetches       │   │ • Identifies the      │             │ • Reads patient        │
│   structured    │   │   authorization       │             │   history from        │
│   clinical data │   │   criteria for the    │             │   EHR (Epic FHIR)     │
│   via FHIR API  │   │   requested service   │             │ • Submits approved    │
│   (labs, meds,  │   │   code (CPT/ICD)      │             │   PAs back to payer  │
│   diagnoses,    │   │ • RAG retrieval over  │             │   portal or via eFax │
│   vitals)       │   │   payer policy PDF    │             │ • Pulls prior PA      │
│ • OCR for       │   │   library             │             │   history for        │
│   scanned docs  │   │ • Returns structured  │             │   context            │
│   and imaging   │   │   criteria checklist: │             │ • Writes PA status   │
│   reports       │   │   ✓ required evidence │             │   updates back to    │
│ • Structures    │   │   ✓ medical necessity │             │   CMS / payer system │
│   output as     │   │     thresholds        │             │                      │
│   evidence      │   │   ✓ exclusion flags   │             │                      │
│   bundle        │   │   ✓ documentation     │             │                      │
│                 │   │     requirements      │             │                      │
└────────┬────────┘   └──────────┬────────────┘             └───────────┬───────────┘
         │                       │                                       │
         └───────────────────────┴──────────────────────────────────────┘
                                 │  Evidence bundle + Policy criteria + Prior PA history
                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    SUBMISSION READINESS AGENT                                     │
│                                                                                   │
│   Compares the evidence bundle against the policy criteria checklist:            │
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  CRITERIA CHECK          │  STATUS     │  ACTION                        │   │
│   ├─────────────────────────────────────────────────────────────────────────┤   │
│   │  Diagnosis codes present │  ✅ Found   │  —                             │   │
│   │  Clinical notes ≥ 90 days│  ✅ Found   │  —                             │   │
│   │  Lab result: HbA1c       │  ❌ Missing │  Request from provider         │   │
│   │  Prior treatment failed  │  ⚠️ Partial │  Needs clarification           │   │
│   │  Step therapy documented │  ✅ Found   │  —                             │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
│   Output: COMPLETE (proceed) or INCOMPLETE (notify provider of gaps)            │
└──────────────────────────────┬───────────────────────────────────────────────────┘
                               │
             ┌─────────────────┴──────────────────┐
             │                                     │
             ▼                                     ▼
     INCOMPLETE                               COMPLETE
  Notify provider                               │
  of specific gaps  ◄────── provider         ▼
  (request info)    ────── responds ──► re-run readiness
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                       DECISION SUPPORT AGENT                                      │
│                                                                                   │
│   Maps each piece of evidence to its corresponding policy criterion:             │
│                                                                                   │
│   Evidence: "Lab result 11/03/25: HbA1c = 9.2%"                                 │
│   → Criterion: "HbA1c ≥ 8.0% required for medication class approval"           │
│   → Match: ✅ MEETS THRESHOLD  [citation: Policy §4.2.1]                        │
│                                                                                   │
│   Evidence: "Clinical note 10/15/25: patient trialed metformin ×6 months"       │
│   → Criterion: "Step therapy: metformin trial ≥ 90 days required"              │
│   → Match: ✅ MEETS THRESHOLD  [citation: Policy §4.3]                          │
│                                                                                   │
│   CONFLICT RESOLUTION (built in):                                                │
│   • Evidence borderline (within 10% of threshold) → flag for reviewer           │
│   • Evidence contradicts claim (e.g., notes say no prior treatment but          │
│     provider checked "step therapy complete") → raise discrepancy flag          │
│   • Policy criteria ambiguous → escalate, do not auto-decide                   │
│                                                                                   │
│   Output: structured recommendation                                              │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  RECOMMENDATION  │  CONFIDENCE  │  CONDITIONS                            │  │
│   ├──────────────────────────────────────────────────────────────────────────┤  │
│   │  ✅ Approve       │  HIGH (92%)  │  All criteria met, no conflicts        │  │
│   │  ⚠️ Approve w/    │  MEDIUM      │  Minor gap or borderline criterion     │  │
│   │     conditions    │  (68–85%)    │  — reviewer must confirm               │  │
│   │  ❌ Likely Deny   │  HIGH        │  Required criterion unmet              │  │
│   │  🔍 Peer-to-Peer  │  LOW (<68%)  │  Conflicting evidence or ambiguous     │  │
│   │     Required      │              │  policy — clinical discussion needed   │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬───────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│               HUMAN-IN-THE-LOOP — CLINICAL REVIEWER QUEUE                        │
│                                                                                   │
│   AI is decision SUPPORT. Final approve / deny rests with a licensed reviewer.  │
│                                                                                   │
│   Reviewer sees:                                                                  │
│   • Evidence bundle (structured, pre-organised)                                  │
│   • Policy criteria checklist with evidence citations                            │
│   • Confidence score + recommendation                                            │
│   • Conflict / discrepancy flags (if any)                                        │
│   • Draft determination letter                                                   │
│                                                                                   │
│   Reviewer actions: APPROVE · DENY · REQUEST PEER-TO-PEER · REQUEST MORE INFO   │
│                                                                                   │
│   SLA routing:                                                                    │
│   • URGENT / Concurrent PA   → reviewer within 1 hour                           │
│   • EXPEDITED PA             → reviewer within 4 hours                          │
│   • STANDARD PA              → reviewer within 24 hours                         │
└──────────────────────────────┬───────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────────────┐
              │                │                        │
              ▼                ▼                        ▼
          APPROVED          DENIED              PEER-TO-PEER
              │           Denial letter         Scheduled call
              │           + appeal rights       between provider
              │           notice generated      MD and payer MD
              │                │                        │
              └────────────────┴────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │       NOTIFICATION AGENT        │
              │                                │
              │ • EHR in-basket alert to       │
              │   ordering provider            │
              │ • Determination letter to      │
              │   provider + patient           │
              │ • CMS / payer portal update    │
              │   via Legacy System Connector  │
              │ • Audit log finalised          │
              └────────────────────────────────┘
```

---

## Agent Breakdown

### 1. Orchestrator Agent
**Model:** Multi-modal foundation model (Claude / Gemini) — single model handles both text (clinical notes) and structured data (lab values, FHIR resources).

| Responsibility | Details |
|---|---|
| PA context window | Creates and maintains shared state across all sub-agents for the duration of the PA |
| Urgency routing | Standard (72hr SLA) · Expedited (24hr) · Urgent/Concurrent (4hr) — same pipeline, different priority queue |
| Parallel dispatch | Evidence Aggregator + Policy Interpreter run simultaneously to minimise latency |
| Conflict detection | Compares sub-agent outputs before routing to Decision Support Agent |
| Escalation logic | Applies confidence thresholds and conflict flags to determine reviewer queue |

### 2. Evidence Aggregator
**Tools:** FHIR R4 API (Epic / Cerner), OCR engine, document parser, eFax ingestion

- Fetches structured clinical data: diagnoses (ICD-10), procedures (CPT), medications, lab results, vitals
- OCRs scanned documents (paper referrals, imaging reports, specialist letters)
- Normalises all evidence into a structured evidence bundle with source citations
- Flags evidence that is stale (e.g., lab result older than 12 months for chronic condition criteria)

### 3. Policy Interpreter
**Model:** LLM with RAG over payer policy library
**Tools:** Vector store of payer PDF guidelines + structured JSON criteria sets

- Looks up the authorisation criteria for the requested service code (CPT / HCPCS / NDC)
- RAG retrieval over unstructured policy PDFs; rules engine for structured JSON criteria
- Returns a structured criteria checklist with each required evidence element, threshold, and policy citation
- Handles policy versioning — always retrieves criteria valid at the date of service

> **Build vs. Fine-tune:** General-purpose LLM + RAG is preferred over a fine-tuned model. PA criteria vary per payer, per service line, and are updated quarterly. RAG over a maintained policy library avoids retraining costs and keeps criteria current.

### 4. Submission Readiness Agent
**Model:** LLM comparison logic
**Tools:** Criteria checklist from Policy Interpreter, evidence bundle from Evidence Aggregator

- Performs a systematic gap analysis: compares what the policy requires against what evidence is present
- Categorises each criterion: ✅ Met · ❌ Missing · ⚠️ Partial / Needs Clarification
- Generates a provider-facing gap notice for missing items (specific, actionable — not generic)
- Re-runs after provider responds with additional evidence

### 5. Decision Support Agent
**Model:** LLM structured reasoning output
**Tools:** Evidence bundle, criteria checklist, prior PA history, conflict detection logic

- Maps each evidence item to its corresponding policy criterion with an explicit citation
- Applies numerical threshold checks (e.g., HbA1c ≥ 8.0%, BMI ≥ 35)
- Computes a per-criterion pass/fail and an overall confidence score
- Produces one of four structured recommendations: Approve · Approve with conditions · Likely Deny · Peer-to-Peer Required
- All mappings are logged for the audit trail and displayed to the reviewer

**Conflict Resolution Logic:**

| Conflict Type | System Response |
|---|---|
| Evidence borderline (within 10% of numeric threshold) | Flag for reviewer · Do not auto-approve |
| Provider attestation contradicts clinical notes | Raise discrepancy flag · Escalate to reviewer |
| Policy criteria ambiguous / subject to clinical judgement | Mark as "Peer-to-Peer Required" · Do not auto-decide |
| Requested service on exclusion list for this diagnosis | Hard flag · Reviewer must override manually with reason |

### 6. Legacy System Connector
**Tools:** FHIR R4 API, eFax gateway, payer REST/EDI APIs, CMS portal integration

- Abstracts all external system integrations into a single connector component
- Reads prior PA history and patient clinical context from EHR
- Submits final PA decisions to payer portals or via eFax for non-API payers
- Writes status updates back to EHR so providers see real-time PA status in their workflow

### 7. Notification Agent
**Tools:** EHR in-basket API, email, SMS, secure portal messaging

- EHR in-basket notification to ordering provider at each state transition
- Sends gap requests with specific missing evidence items (not generic rejection)
- Delivers determination letter (approval or denial) with policy citations
- Triggers peer-to-peer scheduling for contested denials
- All outbound communications logged to audit record

---

## Model Selection: Build vs. Buy

| Decision | Choice | Rationale |
|---|---|---|
| NLP + clinical document understanding | **Single multi-modal foundation model** (Claude / Gemini) | Clinical evidence spans text notes, structured lab values, and scanned PDFs — a unified model avoids context loss between separate NLP and document silos |
| Policy retrieval | **RAG over payer policy library** (not fine-tuning) | PA criteria update quarterly per payer; RAG over a maintained document store keeps criteria current without retraining; fine-tuning one model per payer × service line is not feasible |
| Criteria structured vs. unstructured | **Hybrid** — rules engine for JSON criteria, RAG for PDF guidelines | Most payers publish a mix; the system must handle both |
| On-prem vs. cloud LLM | **BAA-covered cloud model** or **on-prem fallback** | PHI must stay within HIPAA-compliant infrastructure; cloud model requires signed BAA; on-prem for payers with strict data residency requirements |

---

## Safety & Human-Centric Design

### Human-in-the-Loop (HITL)
The agent is **decision support only**. No PA is approved or denied without a licensed clinical reviewer:

- Reviewer receives the full evidence-to-criteria mapping with policy citations — not just a bare recommendation
- Confidence score and conflict flags surface the cases that need the most attention
- Reviewer can approve, deny, request more information, or trigger a peer-to-peer call
- Every reviewer action is logged with timestamp and reviewer ID for the audit trail

### Safety: PHI and Compliance

| Threat | Mitigation |
|---|---|
| PHI exposure to cloud LLM | De-identify / tokenize patient identifiers before any cloud model call; re-link after |
| Prompt injection via clinical notes | Sanitise free-text fields in Security Layer; system prompt isolation |
| Stale policy criteria | Policy library versioned and timestamped; Policy Interpreter always retrieves criteria valid at date of service |
| Audit trail gaps | Immutable log created at intake; every agent action appended; finalised at decision |
| Appeals traceability | Every evidence→criterion mapping stored with policy citation; retrievable for appeals process |

---

## Data Flow

```
Provider submits PA request (EHR auto-trigger / portal / fax)
        │
        ▼
Security Layer: PHI de-identification · prompt injection guard · audit log init
        │
        ▼
Orchestrator: parse service code · set urgency tier · create context window
        │
        ├──► [PARALLEL] Evidence Aggregator ──► evidence bundle (FHIR + OCR)
        └──► [PARALLEL] Policy Interpreter  ──► criteria checklist + citations
        │
        ▼ (both complete)
Legacy System Connector ──► prior PA history + patient clinical context
        │
        ▼
Submission Readiness Agent
        │
   ┌────┴────────────────┐
   │                     │
COMPLETE            INCOMPLETE
   │            Notify provider of gaps
   │            ◄── provider responds
   │            Re-run readiness
   ▼
Decision Support Agent
  evidence → criteria mapping
  confidence score + recommendation
        │
        ▼
Clinical Reviewer Queue (SLA by urgency tier)
  Full package: evidence · criteria · mapping · confidence · conflicts
        │
   ┌────┴────────────────┬──────────────────┐
   │                     │                  │
APPROVED             DENIED          PEER-TO-PEER
   │              Denial letter +      Schedule call
   │              appeal notice
   └─────────────────────┴──────────────────┘
                         │
        Notification Agent → EHR in-basket · letter · payer portal update
        Legacy System Connector → submit decision to payer CMS
        Audit Log → finalise immutable record
```

---

## PA State Machine

```
SUBMITTED
    │
    ▼
EVIDENCE_GATHERING ──► (Evidence Aggregator + Policy Interpreter running)
    │
    ▼
READINESS_CHECK
    │
    ├──► PENDING_INFO ──► (provider notified of gaps)
    │         │
    │    provider responds
    │         │
    └◄────────┘ (re-enter READINESS_CHECK)
    │
    ▼
UNDER_REVIEW ──► (in clinical reviewer queue — SLA clock running)
    │
    ├──► APPROVED ──────────────────────────────────────┐
    │                                                   │
    ├──► DENIED                                         │
    │         │                                         │
    │    provider appeals                               │
    │         ▼                                         │
    └──► PEER_TO_PEER ──► (clinical discussion) ──► APPROVED / DENIED
                                                        │
                                                        ▼
                                                     CLOSED
```

---

## Urgency Tiers

| Tier | Trigger | Target Total Time | Reviewer SLA |
|---|---|---|---|
| **Standard** | Routine elective procedure / medication | 72 hours | 24 hours |
| **Expedited** | Condition could worsen without timely treatment | 24 hours | 4 hours |
| **Urgent / Concurrent** | Patient currently admitted or in active treatment | 4 hours | 1 hour |

All tiers use the same pipeline; urgency flag sets queue priority and SLA alerts.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Multi-modal vs. separate NLP + Vision | **Single multi-modal model** | Clinical evidence is text + structured data + scanned PDFs; one model maintains coherent reasoning |
| Policy retrieval | **RAG, not fine-tuning** | Criteria change quarterly; RAG over a versioned policy store avoids retraining |
| Urgency handling | **Same pipeline, priority queue** | Avoids code duplication; urgency only changes SLA and routing speed |
| HITL threshold | **All decisions require reviewer** | Regulatory requirement; no fully automated approve/deny in PA |
| Auditability | **Immutable log + evidence citations** | HIPAA, appeals, and payer audit requirements |
| PHI handling | **De-identify before cloud LLM; BAA required** | HIPAA Safe Harbor de-identification or BAA-covered model endpoint |
| Legacy integration | **Dedicated Connector component** | Isolates messy fax/EDI/FHIR complexity from agent logic |

---

## Artifacts

| Artifact | Location |
|---|---|
| This architecture doc | `README.md` |
| Agent prompt designs | `artifacts/agent-prompts.md` |
| PA state machine (formal) | `artifacts/state-machine.md` |
| Tool schemas (FHIR, payer API) | `artifacts/tool-schemas.md` |
| Criteria checklist schema | `artifacts/criteria-schema.md` |
| Diagrams (Mermaid source) | `diagrams/` |

---

## Next Steps

- [ ] Define prompts for Evidence Aggregator, Policy Interpreter, and Decision Support Agent
- [ ] Build RAG index over sample payer policy PDFs for a specific service line (e.g., GLP-1 medications)
- [ ] Prototype Submission Readiness gap analysis on 20 sample PA requests
- [ ] Define FHIR R4 resource mappings for evidence extraction (Condition, Observation, MedicationRequest)
- [ ] Evaluate Claude vs. Gemini on clinical note comprehension and criteria mapping accuracy
- [ ] Stress-test conflict resolution logic with adversarial cases (contradictory notes, borderline labs)
