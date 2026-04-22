# Interview Response: Smart Diagnostic Assistant for Factory Floor Technicians

> **Role:** Senior Platform Architect / AI Practice Lead
> **Question:** "A global automotive manufacturer wants to equip their factory floor technicians with a Smart Diagnostic Assistant on phone or tablet. When a machine breaks down, the technician should be able to use the app to get repair instructions. Design the end-to-end architecture."

---

## How I Would Open (Framing the Problem)

Before touching the architecture, I want to reframe what makes this problem genuinely hard — because it's easy to sketch a "RAG chatbot with a nice UI" and call it done. That's wrong for this use case in at least three ways.

**This is a safety-critical system.** Wrong repair instructions don't just produce a bad user experience — they can injure a technician, damage a $2M piece of equipment, or trigger a production line shutdown costing tens of thousands of dollars per minute. The safety layer is not a feature. It's a non-negotiable architectural constraint that touches every component.

**This is a mobile-first, physically hostile environment.** A technician standing next to a broken CNC machine has oil on their hands, is wearing PPE, and may have noise levels above 85dB. Voice input is primary, not secondary. Tap targets need to work with gloved hands. Screen brightness must be readable under industrial lighting. These are UX constraints that change the architecture.

**This is potentially an offline-first system.** Large factory floors, basement plant rooms, and EMI-shielded machine enclosures frequently have dead zones where WiFi and cellular don't reach. An assistant that stops working when the machine breaks down is worse than useless — it creates a false dependency. Offline capability is load-bearing, not a nice-to-have.

With those three constraints established, this becomes a multimodal, safety-critical, offline-capable agentic system — not a chatbot.

---

## Clarifying Questions I'd Ask First

These questions are not optional. The answers change the architecture significantly.

### Machine & Knowledge Base

| Question | Why It Matters |
|---|---|
| How many distinct machine models are in the factory? (10? 500? 2,000?) | Determines knowledge base scale — 10 models means focused RAG; 2,000 means machine-identity routing before retrieval |
| What format are the repair manuals in today? (PDFs, CAD files, scanned paper, structured CMMS database?) | PDFs → Document AI pipeline; scanned paper → OCR + heavy cleanup; structured DB → direct import |
| Is there historical repair log data? (past repairs, parts used, outcomes?) | If yes: gold for RAG — real repair outcomes beat manual instructions for common failure modes |
| Are machines connected (IoT sensors, PLC fault codes, OBD-style diagnostics)? | If yes: real-time machine state (error code, sensor readings) dramatically improves diagnostic accuracy |
| How many distinct failure modes per machine type, on average? | High volume → knowledge graph; low volume → flat RAG may suffice |

### Connectivity & Environment

| Question | Why It Matters |
|---|---|
| What is WiFi coverage like on the factory floor? Any known dead zones? | Determines offline architecture depth — partial offline vs. full offline-first |
| What devices will technicians use? (iOS? Android? Company-issued or BYOD?) | Affects app framework choice (Flutter cross-platform vs. native) and MDM deployment strategy |
| Are there areas where camera use is restricted (explosion risk zones, secure areas)? | May require alternative input modes for those zones |
| What is the ambient noise level? (Does the technician need to use the app while nearby machines are still running?) | High noise → voice input needs noise cancellation; may need visual-only mode |

### Safety & Compliance

| Question | Why It Matters |
|---|---|
| What safety standards apply? (ISO 45001, IATF 16949, OSHA, country-specific?) | Directly defines what the safety guardrail layer must enforce |
| Are there repair procedures that require LOTO (Lock-Out/Tag-Out) before starting? | LOTO must be surfaced automatically — the system must never allow a technician to skip it |
| What is the escalation policy for major failures? (Always escalate for electrical? Above a certain machine value threshold?) | Defines the agent's escalation logic and hard stops |
| Are technicians tiered by skill level (junior/senior/specialist)? | If yes: instructions must be scoped to the technician's certification level — a junior must not receive instructions for repairs they're not qualified to perform |

### Integration & Operations

| Question | Why It Matters |
|---|---|
| Is there a CMMS (e.g., SAP PM, IBM Maximo, ServiceNow)? | Repair logs, work orders, parts inventory — all need to flow back |
| Is parts inventory accessible via API? | Enables real-time check: "this repair requires Part X — you have 3 in stock, Bay 7" |
| What languages do technicians speak? (Single factory or global rollout across multiple countries?) | Multilingual from Day 1 or later? Changes embedding model choice and UI localization scope |
| What is the acceptable response time? (Machine down = production loss — is 3 seconds acceptable?) | Factory lines can cost $10k–$50k per hour of downtime; P99 latency is a business SLA, not just a UX metric |

**Assumed answers for this design:**
- ~300 distinct machine models, mix of PDF manuals and historical CMMS data
- Machines have PLC fault codes (structured) but not full IoT sensor streaming
- WiFi coverage is 85% of factory floor; 15% dead zones (basement plant rooms)
- Company-issued Android tablets + smartphones; MDM-managed
- ISO 45001 + IATF 16949 apply; LOTO procedures are mandatory for electrical
- Technicians are tiered (L1/L2/L3); instructions scoped to level
- SAP PM as CMMS; parts inventory API available
- Target response time: < 5 seconds P99 (machine down = line down)

---

## Scale Reality Check

Unlike the email campaign problem, this is not a throughput problem. It's a **latency + reliability** problem.

- 5,000 technicians — not concurrent; peak load maybe 200–300 simultaneous queries
- Each query: one multimodal LLM call + RAG retrieval + safety check + CMMS lookup
- Target P99: < 5 seconds (machine down = line down = $$$/min)
- Knowledge base: ~300 machine models × ~500 pages/manual + historical logs ≈ **~5M document chunks**
- Offline cache per device: top 50 failure modes × 300 machines = ~15,000 pre-generated guides ≈ **~2GB per device** (manageable on modern tablets)

The scale numbers are small enough that a simple Cloud Run deployment handles the peak load. The hard problems here are **latency**, **safety**, **offline**, and **multimodal input** — not throughput.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MOBILE APP (Android / iOS)                                │
│                        Flutter — MDM deployed                                    │
│                                                                                  │
│  Input Capture                     Offline Mode                                  │
│  ┌────────────────────────────┐    ┌──────────────────────────────────────┐      │
│  │ Voice (primary)            │    │ Firebase local cache                 │      │
│  │ → on-device STT (Whisper)  │    │ Pre-generated guides: top 50 failure │      │
│  │   + cloud STT fallback     │    │ modes × 300 machine models           │      │
│  │                            │    │ Sync on WiFi restore                 │      │
│  │ Photo capture              │    │ Firestore offline persistence        │      │
│  │ → machine damage photo     │    └──────────────────────────────────────┘      │
│  │                            │                                                  │
│  │ QR / barcode scan          │    Session State                                 │
│  │ → machine_id resolution    │    ┌──────────────────────────────────────┐      │
│  │                            │    │ Current machine_id                   │      │
│  │ Text (fallback)            │    │ Active repair session                │      │
│  │ → large touch targets,     │    │ Step progress tracker                │      │
│  │   glove-friendly keyboard  │    │ Escalation state                     │      │
│  └────────────────────────────┘    └──────────────────────────────────────┘      │
└───────────────────────────────────────────┬─────────────────────────────────────┘
                                            │ HTTPS / REST + Firebase Realtime
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY + BACKEND (Cloud Run)                         │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Auth: Firebase Auth + IAP — technician identity + skill tier             │  │
│  │  Rate limiting: 300 concurrent sessions max                               │  │
│  │  Session context: Firestore (machine_id, technician_id, repair_session)   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────┬─────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     INPUT PROCESSING PIPELINE (Cloud Run)                        │
│                                                                                  │
│  ┌──────────────────┐  ┌──────────────────────┐  ┌───────────────────────────┐  │
│  │ Voice → Text     │  │ Image Analysis       │  │ Machine ID Resolution     │  │
│  │                  │  │                      │  │                           │  │
│  │ Vertex AI        │  │ Gemini 1.5 Pro Vision│  │ QR scan → machine_id      │  │
│  │ Speech-to-Text   │  │                      │  │ → Firestore machine       │  │
│  │ (noise-suppress  │  │ Identify:            │  │   registry lookup         │  │
│  │  model)          │  │ - damaged component  │  │                           │  │
│  │                  │  │ - failure type       │  │ Outputs:                  │  │
│  │ Output: text     │  │ - severity estimate  │  │ - machine_model           │  │
│  │ transcript       │  │ - part number match  │  │ - machine_location        │  │
│  └──────────────────┘  └──────────────────────┘  │ - PLC fault codes         │  │
│                                                   │ - last maintenance date   │  │
│                                                   └───────────────────────────┘  │
│                                    │                                             │
│                                    ▼                                             │
│              ┌────────────────────────────────────────────┐                     │
│              │  Unified Problem Description               │                     │
│              │  {machine_id, model, location,             │                     │
│              │   fault_codes[], symptom_text,             │                     │
│              │   damage_image_analysis,                   │                     │
│              │   technician_id, skill_tier}               │                     │
│              └────────────────────────────────────────────┘                     │
└───────────────────────────────────────────┬─────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     DIAGNOSTIC AGENT (Cloud Run — ADK / LangGraph)               │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Step 1: Failure Mode Classification                                      │  │
│  │  Input: fault_codes + symptom_text + image analysis                       │  │
│  │  → Gemini 1.5 Pro: classify into failure_mode + affected_component        │  │
│  │  → Confidence score: high (>0.85) → proceed; low → ask clarifying Q      │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Step 2: Hybrid Knowledge Retrieval                                       │  │
│  │                                                                           │  │
│  │  Tool A: graph_query(machine_model, component, failure_mode)              │  │
│  │  → Spanner Graph: Machine → Component → FailureMode → RepairProcedure    │  │
│  │  → Returns: procedure_id, required_parts[], safety_class, skill_level    │  │
│  │                                                                           │  │
│  │  Tool B: vector_search(symptom_text + failure_mode)                      │  │
│  │  → Vertex AI Vector Search: repair manuals + historical repair logs      │  │
│  │  → Returns: top-5 relevant manual sections + past repair outcomes        │  │
│  │                                                                           │  │
│  │  Tool C: get_machine_context(machine_id)                                 │  │
│  │  → Firestore: last maintenance, known issues, open work orders           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Step 3: Safety Gate (HARD STOP — non-negotiable)                        │  │
│  │                                                                           │  │
│  │  Check A: Skill level gate                                               │  │
│  │  procedure.required_skill_tier > technician.skill_tier → ESCALATE        │  │
│  │  Never generate instructions beyond technician's certification level      │  │
│  │                                                                           │  │
│  │  Check B: LOTO requirement                                               │  │
│  │  procedure.safety_class IN ["electrical", "hydraulic", "pneumatic"]      │  │
│  │  → ALWAYS prepend LOTO procedure steps before any repair instructions    │  │
│  │  → Technician must explicitly confirm LOTO complete before continuing    │  │
│  │                                                                           │  │
│  │  Check C: Escalation triggers                                            │  │
│  │  - Structural damage detected in image (confidence > 0.7)               │  │
│  │  - Machine value > $500k AND failure_class = "major"                    │  │
│  │  - Repair requires >4 hours estimated time (L1/L2 cannot authorize)     │  │
│  │  → ESCALATE: create work order, page senior technician / maintenance eng │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Step 4: Instruction Generation                                          │  │
│  │                                                                           │  │
│  │  Gemini 1.5 Pro: synthesize repair procedure from:                       │  │
│  │  - Graph-retrieved procedure template                                    │  │
│  │  - Manual sections (RAG)                                                 │  │
│  │  - Machine context (last maintenance, known issues)                      │  │
│  │  - Historical outcomes for this failure mode on this machine model       │  │
│  │                                                                           │  │
│  │  Output: numbered steps, tool requirements, parts list,                  │  │
│  │          estimated time, safety warnings, images/diagrams (if available) │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Step 5: Real-time Integrations (parallel, non-blocking)                 │  │
│  │                                                                           │  │
│  │  Tool D: check_parts_inventory(parts_list)                               │  │
│  │  → SAP PM API: is Part X in stock? Location in warehouse?               │  │
│  │                                                                           │  │
│  │  Tool E: create_work_order(machine_id, failure_mode, technician_id)      │  │
│  │  → SAP PM: log the repair, open work order, timestamp                   │  │
│  │                                                                           │  │
│  │  Tool F: check_maintenance_history(machine_id, failure_mode)             │  │
│  │  → Firestore: has this exact failure occurred before? Outcome?          │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────┬─────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE BASE LAYER                                         │
│                                                                                  │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌──────────────────┐  │
│  │ Spanner Graph          │  │ Vertex AI Vector Search│  │ Firestore        │  │
│  │                        │  │                        │  │                  │  │
│  │ Machine                │  │ Repair manuals         │  │ Machine registry │  │
│  │  └─ Model              │  │ (chunked, embedded)    │  │ Technician       │  │
│  │      └─ Component      │  │                        │  │   profiles       │  │
│  │           └─ Failure   │  │ Historical repair logs │  │ Active sessions  │  │
│  │                Mode    │  │ (outcome-annotated)    │  │ Open work orders │  │
│  │                └─ Proc │  │                        │  │ Offline sync     │  │
│  │                   edure│  │ Safety bulletins       │  │   queue          │  │
│  │                        │  │ Parts catalog          │  │                  │  │
│  └────────────────────────┘  └────────────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     FEEDBACK + LEARNING LOOP                                     │
│                                                                                  │
│  Post-repair: technician marks outcome → "Resolved" / "Partial" / "Escalated"   │
│  Outcome + steps_used → Pub/Sub → Cloud Run → BigQuery                          │
│  Weekly: failed repairs reviewed by maintenance engineers → knowledge update     │
│  Monthly: RAGAS-style eval on sample of repair sessions                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## The Three Hard Problems in Detail

### Hard Problem 1: Offline Mode

A machine that breaks in a dead zone is the worst-case scenario — the assistant must work there.

**Architecture decision: offline-first with pre-generated guides, not on-device model.**

Running a full LLM on a factory-floor Android tablet is impractical today (model size, battery, inference latency). The better approach is predictive pre-caching:

- **Pre-generation at ingestion time:** For every known failure mode × machine model combination, generate the repair guide offline during ingestion. Store as structured JSON in Cloud Storage.
- **Device cache via Firebase:** Nightly, the app syncs the guides relevant to machines in the technician's assigned zone. Each guide is ~10–20KB of JSON + image thumbnails.
- **What's cached:** top 50 failure modes per machine type × technician's 20 assigned machines = ~1,000 guides ≈ 50–100MB per device (well within limits).
- **Offline interaction:** No LLM call. The app uses the cached guide with a simple keyword + QR code lookup. Static steps, no dynamic generation.
- **What offline can't do:** Image-based diagnosis, real-time parts inventory check, work order creation. These are queued and synced when connectivity returns.
- **Sync on reconnect:** All technician actions during offline mode (steps completed, notes added) are stored in Firestore local cache and synced automatically.

**Identifying what's in cache:** When the technician opens the app in offline mode, they see: "Offline — showing cached guides for your machines." They select their machine model and reported symptom from a structured dropdown, which maps to the pre-generated guide.

---

### Hard Problem 2: Safety Layer

This is not a content moderation problem. It's a procedural safety enforcement problem.

**Three classes of safety enforcement:**

**Class 1: Skill tier enforcement (hard gate)**
Every repair procedure in the knowledge graph has a `required_tier` field (L1/L2/L3/Specialist). The agent queries this before generating instructions. If `procedure.required_tier > technician.tier`, the app:
- Does not generate repair instructions
- Shows: "This repair requires L3 certification. Escalating to maintenance engineer."
- Creates a work order automatically
- This gate cannot be bypassed by the technician

**Class 2: LOTO enforcement (mandatory prepend)**
For any procedure in safety class `{electrical, hydraulic, pneumatic, stored-energy}`:
- LOTO steps are always prepended, rendered as a distinct checklist with mandatory confirmation checkboxes
- The app will not show Step 1 of the repair until all LOTO checkboxes are ticked
- LOTO completion is logged with timestamp + technician ID for compliance records
- This is implemented as a UI-level gate, not an LLM prompt instruction — it cannot be hallucinated away

**Class 3: Confidence-based escalation (soft gate)**
If the diagnostic agent's confidence in the failure mode classification is < 0.75:
- Do not generate repair instructions
- Ask 1–2 clarifying questions to narrow the diagnosis
- After 2 clarifications with still low confidence: escalate

The reason for the confidence threshold: **generating confident-sounding wrong instructions is more dangerous than admitting uncertainty.** An "I'm not sure — let me escalate" response is always safer than a hallucinated repair procedure.

---

### Hard Problem 3: Multimodal Input in a Hostile Environment

Factory floors are harsh for UX. Design choices that matter:

**Voice as primary input:**
- Technician holds up the tablet, says: "Machine 47-B, hydraulic press. It's making a grinding noise from the left side and stopped mid-cycle."
- Vertex AI Speech-to-Text with `enhanced_phone_call` model (handles background noise)
- On-device Whisper model as offline fallback (no network needed)
- Voice input must work at 80–90 dB ambient noise — use noise-canceling audio processing before STT

**Photo as diagnostic input:**
- Technician photographs the damaged component
- Gemini Vision identifies: component name, failure type (crack, wear, leak, burn mark), severity
- Output becomes part of the problem description — not just visual context
- Photo is stored with the repair session for compliance documentation

**QR code as machine identifier:**
- Every machine has a QR code on the control panel (generated at CMMS registration)
- App scans QR → resolves machine_id → loads machine context (model, last maintenance, known issues, fault codes)
- This bypasses the need to type or verbally spell machine names, which are often technical alphanumeric codes (e.g., "KUKA KR 210 R2700, cell 7B")

**Glove-friendly UI design:**
- All interactive elements: minimum 56px touch targets (Apple HIG for glove use)
- No small text input — voice first, large dropdown selects for structured fields
- High-contrast display mode for bright industrial lighting
- Step-by-step view: one step per screen, large typography, clear "Next" / "Back" navigation

---

## Knowledge Base Ingestion Pipeline

```
Repair manuals (PDFs)
       │
       ▼
Cloud Run: Document AI (OCR + layout detection)
       │  structured: text blocks, tables, figures, diagrams
       ▼
Cloud Run: Chunker
  ├── Semantic chunks: 512 tokens, procedure-boundary aware
  │   (don't split a numbered step across chunk boundaries)
  ├── Metadata: machine_model, section_type (safety/procedure/parts),
  │             procedure_id, step_number
  └── Image extraction: diagrams → Cloud Storage → linked to chunk
       │
       ▼
Vertex AI text-embedding-005 → Vertex AI Vector Search (RAG index)

Structured CMMS data (SAP PM export)
       │
       ▼
Dataflow: transform → Spanner Graph upsert
  Nodes: Machine, Model, Component, FailureMode, RepairProcedure, Part
  Edges: HAS_COMPONENT, EXHIBITS_FAILURE, RESOLVED_BY, REQUIRES_PART

Historical repair logs (CMMS export)
       │
       ▼
Cloud Run: Outcome annotator
  ├── Parse: machine_id, failure_description, steps_taken, outcome, duration
  ├── Link: to procedure_id in knowledge graph
  └── Embed: failure_description → Vector Search (outcome-annotated index)
```

**Why historical repair logs matter:** When the knowledge graph says "Procedure P-47 resolves this failure" but historical logs show that P-47 failed in 60% of cases on this machine model and P-52 succeeds in 90%, the RAG retrieval should surface that signal. Outcome-annotated history is more valuable than the manual alone.

---

## GCP Services Map

| Component | GCP Service | Why |
|---|---|---|
| Mobile app backend | Firebase (Auth, Firestore, Realtime DB) | Offline sync, push notifications, fast auth |
| App deployment | Firebase App Distribution + MDM | Enterprise device management |
| Offline content sync | Firebase + Cloud Storage | Nightly guide sync to devices |
| API backend | Cloud Run | Stateless, scales to 300 concurrent sessions |
| Auth + rate limiting | Firebase Auth + Identity-Aware Proxy | Technician identity + skill tier enforcement |
| Session state | Firestore | Machine_id, active repair session, step progress |
| Voice → text | Vertex AI Speech-to-Text (enhanced) | Industrial noise model, low-latency streaming |
| On-device STT (offline) | Whisper (on-device, bundled in app) | Offline voice input fallback |
| Image analysis | Vertex AI Gemini 1.5 Pro (Vision) | Multimodal damage identification |
| Failure classification | Vertex AI Gemini 1.5 Pro | Reasoning over fault codes + symptoms + image |
| Knowledge graph | Spanner Graph | Machine → Component → Failure → Procedure graph |
| RAG index (manuals + logs) | Vertex AI Vector Search | Semantic search over 5M manual chunks |
| Instruction generation | Vertex AI Gemini 1.5 Pro | Synthesize contextual repair steps |
| Machine registry | Firestore | QR code → machine_id resolution, <10ms |
| Document ingestion (manuals) | Document AI (OCR + Form Parser) | Layout-aware PDF parsing |
| Ingestion pipeline | Dataflow | Parallel manual processing + graph upsert |
| Parts inventory integration | Cloud Run → SAP PM API proxy | Real-time stock check |
| CMMS work order creation | Cloud Run → SAP PM API proxy | Automatic repair log + work order |
| Repair session logs | BigQuery | Full audit trail per session + outcome |
| Feedback processing | Pub/Sub + Cloud Run | Async outcome annotation + knowledge update |
| Content cache (pre-gen guides) | Cloud Storage + Cloud CDN | Low-latency offline guide delivery |
| Monitoring | Cloud Monitoring + Cloud Trace | P99 latency per step, safety gate trigger rate |
| Secrets (SAP API keys) | Secret Manager | Credentials for CMMS + inventory APIs |

---

## Key Trade-offs I Would Call Out

**1. On-device LLM vs. pre-generated offline guides**

The "obvious" offline solution is to run a small LLM on-device (Gemma 2B, Phi-3 Mini). The reality: even a 3B model struggles on mid-range Android tablets, generates instructions in 15–30 seconds, and hallucinates at a higher rate than a well-tuned cloud model. For safety-critical repair instructions, hallucination rate is not acceptable. Pre-generated guides for known failure modes are deterministic, fast (<1ms), and auditable. The trade-off: pre-generated guides only cover known failure modes. Novel failures that don't match any cached guide will show "Connectivity required for this diagnosis" in offline mode — which is honest and safe rather than generating potentially wrong instructions.

**2. Graph + RAG vs. RAG alone**

Pure vector search over repair manuals can retrieve relevant sections, but it can't answer: "What skill level is required for this procedure?" or "Does this machine model have a known issue with this component?" Those are structured relational facts, not semantic retrieval questions. The knowledge graph answers those questions deterministically in <100ms. RAG fills the unstructured knowledge gap (manual prose, historical notes). The combination is more accurate and faster than RAG alone for this domain.

**3. Confidence threshold calibration**

Setting the failure classification confidence threshold too high (>0.90) means too many escalations for repairable failures — frustrating for technicians and expensive for maintenance engineers. Too low (<0.60) means generating instructions for misdiagnosed failures — dangerous. The right threshold is calibrated on historical data: run the classifier against labeled past repairs and tune the threshold to maximize precision on dangerous failure classes (electrical, hydraulic, structural). I'd start at 0.75 and adjust based on the first 30 days of production data.

**4. Real-time PLC fault code integration vs. manual symptom entry**

If machines have OPC-UA or MQTT connectivity, the app can automatically pull fault codes the moment a technician scans the machine QR code — no symptom entry needed, dramatically improving diagnostic accuracy. This is the right long-term architecture. But it requires connectivity between the app backend and the factory's OT (Operational Technology) network — which typically has strict IT/OT segmentation policies, requires OT team sign-off, and can take months to approve. Design for it, but plan for manual symptom entry as the Day 1 fallback.

**5. Safety gates as UI vs. LLM instructions**

A common mistake: implementing safety gates as LLM prompt instructions ("Always include LOTO steps before electrical repairs"). LLM instructions can be reasoned around, misapplied, or hallucinated. LOTO enforcement must be a hard UI gate — a checklist that blocks progression, rendered from the knowledge graph's `safety_class` field, independent of what the LLM generates. The LLM writes the repair instructions; the safety layer is a separately-engineered, deterministic overlay. Never trust a language model with life-safety enforcement.

**6. Single-turn vs. multi-turn repair session**

Simple repairs: single-turn (describe → get instructions → execute). Complex repairs with 20+ steps: multi-turn (execute step 1–5, hit unexpected issue, ask follow-up, get adapted instructions). The session model in Firestore preserves step progress and context, enabling the agent to answer mid-repair follow-ups like "Step 7 says to remove the coupling — but mine doesn't have a coupling. What do I do?" with full context of the machine and prior steps.

---

## Failure Scenarios and Handling

| Failure | Impact | Mitigation |
|---|---|---|
| Network drop mid-repair (step 6 of 12) | Technician stranded mid-procedure | Firestore local cache: all received steps cached; technician can continue with cached content; new steps queued for delivery on reconnect |
| Gemini misclassifies failure mode (confidence > threshold but wrong) | Wrong repair instructions → potential damage | Technician confirmation step: "I identified this as a bearing failure in the left drive shaft. Does this match what you're seeing?" before generating steps |
| Safety gate false positive (escalates fixable issue) | Technician frustration, unnecessary escalation | Log all escalations; weekly review by maintenance manager; adjust threshold or procedure tier if pattern identified |
| SAP PM API down | Can't create work order or check parts | Non-blocking: work order creation queued in Pub/Sub, retried when SAP recovers; show technician parts location from cached inventory snapshot |
| Outdated repair manual in knowledge base | Instructions reference superseded procedure | Every document chunk has `valid_until` metadata; stale chunks suppressed in retrieval; CMMS change notifications trigger re-ingestion |
| Technician photos wrong machine | Wrong machine context → wrong instructions | QR code scan is the authoritative machine identifier; if photo is used as supplemental input, the response includes "Confirming this is machine {id} — the {model} in {location}?" before generating steps |

---

## Pre-Deployment Checklist

| Task | Lead Time | Owner |
|---|---|---|
| Complete QR code tagging on all machines | 4–6 weeks | Maintenance team |
| Ingest all repair manuals into knowledge base | 2–4 weeks | AI Platform team + Document AI pipeline |
| Import CMMS historical repair logs | 1 week | CMMS admin |
| Build and validate knowledge graph from CMMS data | 2 weeks | AI Platform team |
| Safety gate validation: test all LOTO procedures | 2 weeks | EHS + Maintenance engineering |
| Skill tier mapping: assign tier to all repair procedures | 1 week | Maintenance manager |
| Offline guide pre-generation: all models × top failure modes | 1 day (automated) | AI Platform team |
| Device rollout via MDM: 5,000 devices | 2 weeks | IT / MDM admin |
| Pilot with 50 technicians (1 production line) | 2 weeks | Change management team |
| Go/No-go review: safety audit, accuracy audit on pilot data | 1 week | EHS, Maintenance Eng, IT Security |

---

## How I Would Measure Success

| Metric | Target | Why |
|---|---|---|
| Mean time to first repair step (from QR scan to step 1) | < 5 seconds | Machine down = line down = $$$/min |
| Diagnostic accuracy (correct failure mode identified) | ≥ 92% | Validated against maintenance engineer review of sample |
| First-time fix rate (repair resolved without escalation) | ≥ 75% | Baseline today without assistant: typically 50–60% |
| Unnecessary escalation rate (assistant escalated a fixable repair) | < 10% | Balances safety with technician autonomy |
| LOTO compliance rate (LOTO confirmed before electrical steps) | 100% | Non-negotiable; any miss is a compliance incident |
| Offline mode availability (app functional in dead zones) | 100% for known failure modes | Must work where machines are |
| Mean time to repair (MTTR) reduction vs. baseline | ≥ 20% reduction | Primary business value metric |
| Knowledge base freshness (manuals up-to-date within N days of revision) | < 7 days | Stale manuals are a safety risk |

---

## How the Interview Conversation Actually Flows

**Minutes 0–5: Framing + Clarifying Questions**
> Interviewer: "Design a Smart Diagnostic Assistant for 5,000 factory technicians."
>
> Strong candidate: "Before I start, I want to call out that this problem has some non-obvious constraints that will significantly change the architecture. Can I ask a few questions?"
>
> Key questions to raise verbally: connectivity on factory floor, machine count, manual format, LOTO/safety standards, technician skill tiers, CMMS integration.

*What the interviewer is watching for:* Do you identify safety-criticality unprompted? Do you ask about offline requirements? Do you know what LOTO is? Candidates who immediately talk about "a RAG chatbot with a nice UI" haven't thought about the environment.

**Minutes 5–10: Reframe as a Three-Constraint Problem**
> Strong candidate: "Based on those answers, I want to flag three constraints that I think are load-bearing for the architecture. Safety — wrong instructions can injure someone. Offline — factory dead zones are real. And mobile hostility — voice is the primary input, not text."

*What the interviewer is watching for:* Do you derive non-obvious constraints from the clarifications, or just restate the question?

**Minutes 10–25: Architecture walkthrough**
Draw the five stages: input capture → processing → diagnostic agent → knowledge base → integrations. Call out the safety gate explicitly as a separate, non-LLM-generated layer.

**Minutes 25–35: Deep dives (interviewer picks)**
Common probes:
- "How does offline mode actually work — what happens if the technician is in a dead zone for 6 hours?"
- "Walk me through exactly what happens when a technician scans a QR code and takes a photo."
- "How do you prevent the LLM from generating instructions that could injure a technician?"
- "The CMMS has 10 years of repair logs. How do you use that data?"
- "What happens if a technician reaches Step 7 and encounters something the manual doesn't cover?"

*Step 7 unexpected situation answer:* The session context in Firestore contains the full repair history: machine_id, failure_mode, steps completed so far, and the current manual sections used. When the technician says "Step 7 doesn't match what I'm seeing — my machine has an extra coupling here," the agent does a targeted RAG query: `vector_search("unexpected coupling + machine_model + procedure_section")` + `graph_query(machine_model, variant=?)` to find whether there's a known variant. If no match and confidence is low → escalate to senior technician with full session context pre-loaded.

**Minutes 35–45: Trade-offs**
Strong candidate proactively raises:
- "I should flag that safety gates must be implemented as UI constraints, not LLM prompt instructions — I can explain why."
- "The on-device LLM temptation for offline mode is a trap for this use case — pre-generated guides are safer."
- "IT/OT network segmentation is the biggest integration risk for real-time PLC fault code access."

**Minutes 45–55: Follow-up scenarios**
- "What if a machine is brand new and has no repair history or manual yet?"
- "How would you handle a safety recall that affects 200 machines — how do you update all their guides?"
- "What if a technician follows the instructions and the repair fails — how do you improve the system?"

*Safety recall answer:* Recall bulletin → ingestion pipeline → knowledge graph edge update: `{machine_model} REQUIRES_SAFETY_ACTION {recall_id}`. Next time any technician opens a session for that machine model, the safety gate layer checks for active recalls before generating any other content, and surfaces the recall procedure as the mandatory first action. Push notification via Firebase to all technicians assigned to affected machines. Pre-generated offline guides for affected machines are invalidated and regenerated automatically.

---

## Summary Framing for Closing the Answer

The key insight I want to leave you with is that the hardest problems in this design are not the AI problems — they're the environmental and safety constraints that most candidates forget. The LLM is capable of generating excellent repair instructions given the right context. What makes this system production-ready is everything around the LLM: the offline cache that works in dead zones, the LOTO enforcement that cannot be LLM-generated, the skill-tier gate that can't be bypassed, and the confidence threshold that chooses escalation over hallucination.

A RAG chatbot that works 95% of the time in a factory is dangerous because of the 5% where it confidently generates wrong instructions. The architecture I've described is designed so that uncertainty leads to escalation, not fabrication — and safety checks are structural, not instructional. That's the difference between a demo and a system you'd deploy to 5,000 people working with machinery that can kill them.
