# System Architecture Diagrams

## End-to-End Agent Orchestration Flow

```mermaid
flowchart TD
    A1[Provider Portal\nStaff-submitted] --> B
    A2[EHR Auto-Trigger\nEpic / Cerner FHIR] --> B
    A3[Fax / Legacy Payer Portal\nOCR + eFax gateway] --> B

    B[Security & Compliance Layer\nPHI De-identification · Prompt Injection Guard\nBAA Verification · Audit Log Init]

    B -->|Sanitised PA package + urgency flag| C[Orchestrator Agent\nMulti-modal Foundation Model\nClaude / Gemini]

    C --> D[Evidence Aggregator\nFHIR R4 API · OCR · Document Parser\nLabs · Meds · Diagnoses · Notes]
    C --> E[Policy Interpreter\nRAG over Payer Policy Library\nCPT/ICD criteria · PDF guidelines]
    C --> F[Legacy System Connector\nEHR · Payer Portal · eFax\nPrior PA history · Status updates]

    D -->|Evidence bundle| G[Submission Readiness Agent\nGap Analysis: Evidence vs. Criteria\nMet · Missing · Partial]
    E -->|Criteria checklist + citations| G
    F -->|Prior PA history| G

    G -->|INCOMPLETE: specific gaps| H[Notify Provider\nEHR in-basket · Email · SMS\nRequest missing evidence]
    H -->|Provider responds| G

    G -->|COMPLETE| I[Decision Support Agent\nEvidence → Criteria Mapping\nConfidence Score · Recommendations]

    I -->|Approve HIGH conf.| J[✅ Recommend Approve]
    I -->|Approve MEDIUM conf.| K[⚠️ Approve with Conditions]
    I -->|Deny HIGH conf.| L[❌ Likely Deny]
    I -->|Conflict / Ambiguous| M[🔍 Peer-to-Peer Required]

    J --> N[Clinical Reviewer Queue\nFull package: evidence · criteria\nmapping · confidence · flags]
    K --> N
    L --> N
    M --> N

    N -->|Approved| O[Determination: APPROVED]
    N -->|Denied| P[Determination: DENIED\nDenial letter + appeal rights]
    N -->|Peer-to-Peer| Q[Schedule Clinical Discussion\nProvider MD ↔ Payer MD]
    Q -->|Outcome| O
    Q -->|Outcome| P

    O --> R[Notification Agent\nEHR in-basket · Letter · Portal update]
    P --> R
    R --> S[Legacy System Connector\nSubmit decision to payer CMS\nFinalise audit log]
```

## Submission Readiness Gap Analysis

```mermaid
flowchart TD
    A[Evidence Bundle\nfrom Aggregator] --> C
    B[Criteria Checklist\nfrom Policy Interpreter] --> C

    C[Submission Readiness Agent\nSystematic gap analysis]

    C --> D{All criteria\nmet?}

    D -->|Yes| E[✅ COMPLETE\nProceed to Decision Support]

    D -->|No| F[Generate Gap Notice\nSpecific missing items per criterion]
    F --> G[Notify Provider\nEHR in-basket — actionable list]
    G --> H{Provider\nresponds?}
    H -->|Provides evidence| I[Re-run Readiness Check]
    I --> D
    H -->|No response within SLA| J[Escalate to Reviewer\nas Incomplete Submission]
```

## Conflict Resolution Decision Tree

```mermaid
flowchart TD
    A[Decision Support Agent\nMaps evidence to policy criteria]

    A --> B{Any conflicts\nor flags?}

    B -->|Evidence borderline\n±10% of threshold| C[⚠️ Flag for Reviewer\nDo not auto-approve\nHighlight threshold gap]

    B -->|Provider attestation\ncontradicts clinical notes| D[🚩 Discrepancy Flag\nEscalate to reviewer\nShow both evidence items]

    B -->|Policy criteria\nambiguous / clinical judgement| E[🔍 Peer-to-Peer Required\nDo not auto-decide\nSchedule clinical discussion]

    B -->|Service on exclusion list\nfor this diagnosis| F[🚫 Hard Exclusion Flag\nReviewer must manually\noverride with reason code]

    B -->|No conflicts\nAll criteria clearly met| G[Compute Confidence Score\nGenerate structured recommendation]

    G --> H{Confidence?}
    H -->|≥ 90%| I[✅ Recommend Approve]
    H -->|68–89%| J[⚠️ Approve with Conditions\nReviewer confirms]
    H -->|< 68%| K[❌ Likely Deny\nReviewer reviews denial]
```

## PA Processing Timeline by Urgency Tier

```mermaid
gantt
    title Prior Authorization — Processing Timeline by Urgency Tier
    dateFormat HH:mm
    axisFormat %H:%M

    section URGENT — Target 4 hours
    Security + Ingestion              :u0, 00:00, 5m
    Evidence Aggregation + Policy Lookup (parallel) :u1, after u0, 20m
    Submission Readiness Check        :u2, after u1, 10m
    Decision Support + Recommendation :u3, after u2, 10m
    Clinical Reviewer SLA             :u4, after u3, 60m
    Notification + CMS submission     :u5, after u4, 5m

    section EXPEDITED — Target 24 hours
    Security + Ingestion              :e0, 00:00, 10m
    Evidence Aggregation + Policy Lookup (parallel) :e1, after e0, 30m
    Submission Readiness Check        :e2, after e1, 15m
    Provider gap response window      :e3, after e2, 120m
    Decision Support + Recommendation :e4, after e3, 15m
    Clinical Reviewer SLA             :e5, after e4, 240m
    Notification + CMS submission     :e6, after e5, 10m

    section STANDARD — Target 72 hours
    Security + Ingestion              :s0, 00:00, 15m
    Evidence Aggregation + Policy Lookup (parallel) :s1, after s0, 45m
    Submission Readiness + Provider Response :s2, after s1, 480m
    Decision Support + Recommendation :s3, after s2, 20m
    Clinical Reviewer SLA             :s4, after s3, 1440m
    Notification + CMS submission     :s5, after s4, 15m
```

## PA State Machine

```mermaid
stateDiagram-v2
    [*] --> SUBMITTED : Provider submits PA request

    SUBMITTED --> EVIDENCE_GATHERING : Security layer clears · Orchestrator dispatches agents
    EVIDENCE_GATHERING --> READINESS_CHECK : Evidence bundle + Policy criteria ready

    READINESS_CHECK --> PENDING_INFO : Evidence gaps detected · Provider notified
    PENDING_INFO --> READINESS_CHECK : Provider submits missing evidence
    PENDING_INFO --> UNDER_REVIEW : Provider non-responsive (SLA elapsed) — incomplete flag

    READINESS_CHECK --> UNDER_REVIEW : Evidence complete · Decision Support recommendation ready
    UNDER_REVIEW --> APPROVED : Reviewer approves
    UNDER_REVIEW --> DENIED : Reviewer denies
    UNDER_REVIEW --> PEER_TO_PEER : Reviewer requests clinical discussion

    PEER_TO_PEER --> APPROVED : Discussion outcome — approved
    PEER_TO_PEER --> DENIED : Discussion outcome — denied

    APPROVED --> CLOSED : Determination letter sent · CMS updated · Audit finalised
    DENIED --> CLOSED : Denial letter + appeal rights sent · Audit finalised
```
