"use client";

import { useState } from "react";

// ── Types ────────────────────────────────────────────────────────────────────

type AgentType = "single" | "multi-tool" | "multi-agent" | "orchestrator";
type Complexity = "simple" | "intermediate" | "complex";

interface UseCase {
  task: string;
  agentType: AgentType;
  complexity: Complexity;
  tools: string[];
}

interface Domain {
  id: string;
  label: string;
  icon: string;
  color: string; // tailwind bg class
  borderColor: string;
  useCases: UseCase[];
}

// ── Data ────────────────────────────────────────────────────────────────────

const AGENT_TYPE_META: Record<AgentType, { label: string; color: string; desc: string }> = {
  single:        { label: "Single ReAct",      color: "#4a7c59", desc: "One LLM reasoning + one or two tools in a simple loop." },
  "multi-tool":  { label: "Multi-Tool Agent",  color: "#5a6eaa", desc: "Single agent orchestrating many tools with branching logic." },
  "multi-agent": { label: "Multi-Agent",       color: "#8a5aa5", desc: "Parallel specialised agents coordinating via messages or shared state." },
  orchestrator:  { label: "Orchestrator",      color: "#b5652a", desc: "One planner directing multiple subagents; handles complex, long-horizon tasks." },
};

const COMPLEXITY_META: Record<Complexity, { label: string; dot: string }> = {
  simple:       { label: "Simple",       dot: "#4a7c59" },
  intermediate: { label: "Intermediate", dot: "#d4a017" },
  complex:      { label: "Complex",      dot: "#c0392b" },
};

const DOMAINS: Domain[] = [
  {
    id: "software",
    label: "Software Development",
    icon: "⚙️",
    color: "bg-[#e8f0e8]",
    borderColor: "border-[#a8c8a8]",
    useCases: [
      { task: "Code generation from spec / comment", agentType: "single", complexity: "simple", tools: ["code_exec", "file_write"] },
      { task: "Bug diagnosis + fix + test run", agentType: "multi-tool", complexity: "intermediate", tools: ["code_exec", "grep", "test_runner", "docs_search"] },
      { task: "PR review: diff analysis + style + security", agentType: "multi-tool", complexity: "intermediate", tools: ["git", "static_analysis", "docs_search"] },
      { task: "Full repo refactor or migration", agentType: "orchestrator", complexity: "complex", tools: ["git", "code_exec", "file_write", "test_runner"] },
    ],
  },
  {
    id: "support",
    label: "Customer Support",
    icon: "💬",
    color: "bg-[#e8e8f0]",
    borderColor: "border-[#a8a8c8]",
    useCases: [
      { task: "Ticket triage + draft reply", agentType: "single", complexity: "simple", tools: ["crm_lookup", "email_send"] },
      { task: "Order status lookup + customer update", agentType: "multi-tool", complexity: "simple", tools: ["order_db", "shipping_api", "email_send"] },
      { task: "Return / refund processing end-to-end", agentType: "multi-tool", complexity: "intermediate", tools: ["crm", "payment_api", "policy_db", "email_send"] },
      { task: "Sentiment routing + escalation + logging", agentType: "multi-agent", complexity: "intermediate", tools: ["sentiment_api", "crm", "routing_engine", "slack"] },
    ],
  },
  {
    id: "research",
    label: "Research & Synthesis",
    icon: "🔍",
    color: "bg-[#f0ece0]",
    borderColor: "border-[#d4c090]",
    useCases: [
      { task: "Summarise a set of articles on a topic", agentType: "single", complexity: "simple", tools: ["web_search", "reader"] },
      { task: "Competitive landscape report", agentType: "multi-tool", complexity: "intermediate", tools: ["web_search", "reader", "structured_extract", "report_write"] },
      { task: "Literature review from multiple paper sources", agentType: "multi-agent", complexity: "intermediate", tools: ["arxiv_search", "reader", "citation_db"] },
      { task: "Investment due-diligence with financial data", agentType: "orchestrator", complexity: "complex", tools: ["financial_db", "web_search", "reader", "valuation_tool"] },
    ],
  },
  {
    id: "data",
    label: "Data & Reporting",
    icon: "📊",
    color: "bg-[#e8f0f0]",
    borderColor: "border-[#90c4c4]",
    useCases: [
      { task: "Natural-language to SQL query", agentType: "single", complexity: "simple", tools: ["sql_execute", "schema_lookup"] },
      { task: "Automated weekly report with charts", agentType: "multi-tool", complexity: "intermediate", tools: ["db_query", "chart_gen", "email_send"] },
      { task: "Anomaly detection + root-cause narrative", agentType: "multi-tool", complexity: "intermediate", tools: ["metrics_api", "stats_tool", "logs_search"] },
      { task: "Cross-system KPI forecasting dashboard", agentType: "orchestrator", complexity: "complex", tools: ["multiple_dbs", "ml_model", "chart_gen", "slack"] },
    ],
  },
  {
    id: "documents",
    label: "Document Processing",
    icon: "📄",
    color: "bg-[#f0e8e8]",
    borderColor: "border-[#c8a0a0]",
    useCases: [
      { task: "Invoice extraction to structured JSON", agentType: "single", complexity: "simple", tools: ["pdf_reader", "structured_extract"] },
      { task: "Contract review + clause flagging", agentType: "multi-tool", complexity: "intermediate", tools: ["pdf_reader", "clause_db", "diff_tool"] },
      { task: "Meeting transcript → action items → tasks", agentType: "multi-tool", complexity: "simple", tools: ["transcribe", "summarise", "task_tracker"] },
      { task: "High-volume multi-doc compliance check", agentType: "orchestrator", complexity: "complex", tools: ["pdf_reader", "rules_engine", "audit_log"] },
    ],
  },
  {
    id: "healthcare",
    label: "Healthcare",
    icon: "🏥",
    color: "bg-[#eaf0e8]",
    borderColor: "border-[#a8c490]",
    useCases: [
      { task: "Patient symptom intake summary", agentType: "single", complexity: "simple", tools: ["ehr_read", "symptom_db"] },
      { task: "Prior authorisation submission", agentType: "multi-tool", complexity: "intermediate", tools: ["ehr_read", "policy_db", "payer_api", "form_fill"] },
      { task: "Clinical note → SOAP note generation", agentType: "multi-tool", complexity: "intermediate", tools: ["ehr_read", "icd_db", "note_write"] },
      { task: "Multi-specialist diagnostic coordination", agentType: "orchestrator", complexity: "complex", tools: ["ehr_read", "lab_api", "imaging_api", "specialist_agents"] },
    ],
  },
  {
    id: "finance",
    label: "Finance & Legal",
    icon: "⚖️",
    color: "bg-[#ece8f0]",
    borderColor: "border-[#b4a0c8]",
    useCases: [
      { task: "Transaction compliance screen", agentType: "single", complexity: "simple", tools: ["rules_engine", "transaction_db"] },
      { task: "Earnings call analysis + key metrics", agentType: "multi-tool", complexity: "intermediate", tools: ["pdf_reader", "financial_calc", "company_db"] },
      { task: "Legal discovery: tag & summarise docs", agentType: "multi-agent", complexity: "complex", tools: ["doc_search", "reader", "tag_engine", "summary_writer"] },
      { task: "End-to-end contract drafting pipeline", agentType: "orchestrator", complexity: "complex", tools: ["template_db", "clause_gen", "legal_review", "docx_write"] },
    ],
  },
  {
    id: "personal",
    label: "Personal Productivity",
    icon: "🗂️",
    color: "bg-[#f0ede8]",
    borderColor: "border-[#c8b890]",
    useCases: [
      { task: "Email triage + draft replies", agentType: "single", complexity: "simple", tools: ["gmail", "calendar"] },
      { task: "Meeting scheduler across time zones", agentType: "single", complexity: "simple", tools: ["calendar", "email_send"] },
      { task: "Travel itinerary research + booking", agentType: "multi-tool", complexity: "intermediate", tools: ["web_search", "flight_api", "hotel_api", "calendar"] },
      { task: "Weekly personal assistant (tasks + reminders + reports)", agentType: "multi-tool", complexity: "intermediate", tools: ["calendar", "task_tracker", "email", "notes"] },
    ],
  },
];

// Decision tree questions
const QUESTIONS = [
  { id: "multistep",  text: "Does the task require multiple coordinated steps (not just one prompt → one answer)?" },
  { id: "tools",      text: "Does it need to access external data, APIs, or take real-world actions?" },
  { id: "branching",  text: "Is the path unpredictable — different inputs lead to very different sequences of steps?" },
  { id: "frequency",  text: "Does this happen frequently enough that automation has clear ROI?" },
  { id: "variability",text: "Can you tolerate some degree of output variability (vs. 100% deterministic output)?" },
];

// ── Helpers ──────────────────────────────────────────────────────────────────

function scoreToRecommendation(yesCount: number): {
  headline: string;
  body: string;
  color: string;
  border: string;
} {
  if (yesCount >= 4)
    return {
      headline: "Strong AI Agent candidate",
      body: "This problem genuinely benefits from agentic autonomy. Choose an agent architecture and pick the right complexity tier.",
      color: "bg-[#e8f0e8]",
      border: "border-[#4a7c59]",
    };
  if (yesCount === 3)
    return {
      headline: "Agent with guardrails",
      body: "An agent can help, but consider adding human-in-the-loop checkpoints or a deterministic wrapper around the unpredictable parts.",
      color: "bg-[#f4f0e0]",
      border: "border-[#c8a020]",
    };
  if (yesCount === 2)
    return {
      headline: "Simple LLM call or pipeline",
      body: "One or two unpredictable factors doesn't justify a full agent loop. A prompt chain or a single LLM call with structured output is more reliable.",
      color: "bg-[#f4ede8]",
      border: "border-[#c07040]",
    };
  return {
    headline: "No agent needed",
    body: "This is better handled by a deterministic script, a rules engine, or a simple LLM call. Agents add cost and latency without benefit here.",
    color: "bg-[#f4e8e8]",
    border: "border-[#c03030]",
  };
}

// ── Sub-components ───────────────────────────────────────────────────────────

function AgentTypeBadge({ type }: { type: AgentType }) {
  const meta = AGENT_TYPE_META[type];
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold text-white"
      style={{ backgroundColor: meta.color }}
    >
      {meta.label}
    </span>
  );
}

function ComplexityBadge({ level }: { level: Complexity }) {
  const meta = COMPLEXITY_META[level];
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[#555]">
      <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: meta.dot }} />
      {meta.label}
    </span>
  );
}

// ── Section 1: Decision Wizard ───────────────────────────────────────────────

function DecisionWizard() {
  const [answers, setAnswers] = useState<Record<string, boolean | null>>(() =>
    Object.fromEntries(QUESTIONS.map((q) => [q.id, null]))
  );

  const answered = Object.values(answers).filter((v) => v !== null).length;
  const yesCount = Object.values(answers).filter((v) => v === true).length;
  const allDone = answered === QUESTIONS.length;
  const rec = allDone ? scoreToRecommendation(yesCount) : null;

  function toggle(id: string, val: boolean) {
    setAnswers((prev) => ({ ...prev, [id]: prev[id] === val ? null : val }));
  }

  return (
    <div className="not-prose rounded-xl border border-[#FFDA47]/50 bg-white p-5 my-6">
      <h3 className="text-[15px] font-bold text-[#111] mb-1">Should you use an AI Agent?</h3>
      <p className="text-[13px] text-[#666] mb-4">Answer the five questions below. The more "Yes" answers, the stronger the case for an agent.</p>

      <div className="space-y-3">
        {QUESTIONS.map((q, i) => (
          <div key={q.id} className="flex items-start gap-3">
            <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-[#FFDA47] text-[#111] text-[11px] font-bold flex items-center justify-center">
              {i + 1}
            </span>
            <div className="flex-1">
              <p className="text-[13px] text-[#222] mb-1.5 leading-snug">{q.text}</p>
              <div className="flex gap-2">
                {[true, false].map((val) => (
                  <button
                    key={String(val)}
                    onClick={() => toggle(q.id, val)}
                    className={`px-3 py-1 rounded text-[12px] font-semibold border transition-colors cursor-pointer ${
                      answers[q.id] === val
                        ? val
                          ? "bg-[#4a7c59] border-[#4a7c59] text-white"
                          : "bg-[#c03030] border-[#c03030] text-white"
                        : "bg-white border-[#ddd] text-[#555] hover:border-[#aaa]"
                    }`}
                  >
                    {val ? "Yes" : "No"}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {allDone && rec && (
        <div className={`mt-5 rounded-lg border-2 ${rec.border} ${rec.color} px-4 py-3`}>
          <p className="text-[13px] font-bold text-[#111] mb-0.5">
            {yesCount}/5 Yes — {rec.headline}
          </p>
          <p className="text-[12px] text-[#444] leading-snug">{rec.body}</p>
        </div>
      )}

      {!allDone && answered > 0 && (
        <p className="mt-3 text-[12px] text-[#888]">{5 - answered} question{5 - answered !== 1 ? "s" : ""} remaining…</p>
      )}
    </div>
  );
}

// ── Section 2: Domain Explorer ───────────────────────────────────────────────

function DomainExplorer() {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className="not-prose my-6">
      <div className="mb-3">
        <h3 className="text-[15px] font-bold text-[#111]">Use Case Explorer - by Domain</h3>
        <p className="text-[13px] text-[#666] mt-0.5">Click a domain to explore tasks, recommended agent type, and complexity.</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
        {DOMAINS.map((d) => (
          <button
            key={d.id}
            onClick={() => setOpenId(openId === d.id ? null : d.id)}
            className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border-2 text-left transition-all cursor-pointer ${
              openId === d.id
                ? `${d.color} ${d.borderColor} shadow-sm`
                : "bg-white border-[#e0e0e0] hover:border-[#bbb]"
            }`}
          >
            <span className="text-lg leading-none">{d.icon}</span>
            <span className="text-[12px] font-semibold text-[#222] leading-tight">{d.label}</span>
          </button>
        ))}
      </div>

      {openId && (() => {
        const domain = DOMAINS.find((d) => d.id === openId)!;
        return (
          <div className={`rounded-xl border-2 ${domain.borderColor} ${domain.color} p-4`}>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">{domain.icon}</span>
              <h4 className="text-[14px] font-bold text-[#111]">{domain.label}</h4>
            </div>
            <div className="space-y-2.5">
              {domain.useCases.map((uc, i) => (
                <div key={i} className="bg-white rounded-lg px-3 py-2.5 border border-white/70 shadow-xs">
                  <p className="text-[13px] font-medium text-[#222] mb-1.5 leading-snug">{uc.task}</p>
                  <div className="flex flex-wrap items-center gap-2">
                    <AgentTypeBadge type={uc.agentType} />
                    <ComplexityBadge level={uc.complexity} />
                    <span className="text-[11px] text-[#888] leading-none">
                      Tools: {uc.tools.join(", ")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* Legend */}
      <div className="mt-3 flex flex-wrap gap-3">
        <span className="text-[11px] font-semibold text-[#888] uppercase tracking-wide">Agent Types:</span>
        {(Object.entries(AGENT_TYPE_META) as [AgentType, typeof AGENT_TYPE_META[AgentType]][]).map(([type, meta]) => (
          <span key={type} className="flex items-center gap-1 text-[11px] text-[#555]">
            <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: meta.color }} />
            {meta.label}
          </span>
        ))}
      </div>
    </div>
  );
}

// ── Section 3: Complexity & Type Guide ──────────────────────────────────────

const COMPLEXITY_GUIDE = [
  {
    tier: "Simple" as Complexity,
    agentType: "single" as AgentType,
    color: "#e8f0e8",
    border: "#4a7c59",
    dot: "#4a7c59",
    criteria: [
      "1-3 tools needed",
      "Goal is clear and narrow",
      "Single reasoning loop (no replanning)",
      "Short context window sufficient",
    ],
    examples: ["Email triage", "SQL query from NL", "Invoice extraction"],
    frameworks: ["LangChain ReAct", "ADK simple agent", "CrewAI single agent"],
  },
  {
    tier: "Intermediate" as Complexity,
    agentType: "multi-tool" as AgentType,
    color: "#f4f0e0",
    border: "#c8a020",
    dot: "#d4a017",
    criteria: [
      "3-8 tools with branching logic",
      "Multiple subtasks that depend on each other",
      "May need to retry or re-plan on failure",
      "Moderate context (past steps matter)",
    ],
    examples: ["Bug diagnosis + fix", "Competitive report", "Prior auth submission"],
    frameworks: ["LangGraph", "CrewAI multi-tool", "ADK with sub-tools"],
  },
  {
    tier: "Complex" as Complexity,
    agentType: "orchestrator" as AgentType,
    color: "#f4ede8",
    border: "#c07040",
    dot: "#c0392b",
    criteria: [
      "Many specialised capabilities needed",
      "Tasks can run in parallel",
      "Long-horizon: minutes to hours",
      "Requires persistent memory / state",
      "Human checkpoints required (compliance, safety)",
    ],
    examples: ["Full repo migration", "Investment due-diligence", "Multi-specialist medical review"],
    frameworks: ["LangGraph multi-agent", "CrewAI crews", "ADK orchestrator-subagent"],
  },
];

function ComplexityGuide() {
  return (
    <div className="not-prose my-6">
      <h3 className="text-[15px] font-bold text-[#111] mb-1">Choosing Complexity & Agent Type</h3>
      <p className="text-[13px] text-[#666] mb-4">Match your problem's characteristics to the right tier.</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {COMPLEXITY_GUIDE.map((tier) => (
          <div
            key={tier.tier}
            className="rounded-xl border-2 p-4"
            style={{ backgroundColor: tier.color, borderColor: tier.border }}
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: tier.dot }} />
              <span className="text-[13px] font-bold text-[#111]">{tier.tier}</span>
              <AgentTypeBadge type={tier.agentType} />
            </div>

            <p className="text-[11px] font-semibold text-[#555] uppercase tracking-wide mb-1.5">Use when...</p>
            <ul className="space-y-1 mb-3">
              {tier.criteria.map((c, i) => (
                <li key={i} className="flex items-start gap-1.5 text-[12px] text-[#333]">
                  <span className="mt-0.5 text-[10px]">•</span>
                  <span className="leading-snug">{c}</span>
                </li>
              ))}
            </ul>

            <p className="text-[11px] font-semibold text-[#555] uppercase tracking-wide mb-1">Examples</p>
            <div className="flex flex-wrap gap-1 mb-3">
              {tier.examples.map((ex) => (
                <span key={ex} className="px-1.5 py-0.5 rounded text-[11px] bg-white/70 text-[#444] border border-white">
                  {ex}
                </span>
              ))}
            </div>

            <p className="text-[11px] font-semibold text-[#555] uppercase tracking-wide mb-1">Frameworks</p>
            <div className="flex flex-wrap gap-1">
              {tier.frameworks.map((fw) => (
                <span key={fw} className="px-1.5 py-0.5 rounded text-[11px] font-mono bg-white/60 text-[#555] border border-white/80">
                  {fw}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Section 4: Agent Type Reference ─────────────────────────────────────────

function AgentTypeReference() {
  return (
    <div className="not-prose my-6">
      <h3 className="text-[15px] font-bold text-[#111] mb-1">Agent Type Reference</h3>
      <p className="text-[13px] text-[#666] mb-4">
        A quick comparison of the four main architectural patterns.
      </p>
      <div className="overflow-x-auto rounded-xl border border-[#e0e0e0] bg-white">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-[#eee] bg-[#fafaf9]">
              <th className="text-left px-3 py-2.5 font-semibold text-[#111] w-28">Type</th>
              <th className="text-left px-3 py-2.5 font-semibold text-[#111]">What it is</th>
              <th className="text-left px-3 py-2.5 font-semibold text-[#111]">Best for</th>
              <th className="text-left px-3 py-2.5 font-semibold text-[#111] w-24">Complexity</th>
            </tr>
          </thead>
          <tbody>
            {(Object.entries(AGENT_TYPE_META) as [AgentType, typeof AGENT_TYPE_META[AgentType]][]).map(([type, meta], i) => (
              <tr key={type} className={`border-b border-[#f0f0f0] ${i % 2 === 1 ? "bg-[#fafaf9]" : ""}`}>
                <td className="px-3 py-2.5">
                  <AgentTypeBadge type={type} />
                </td>
                <td className="px-3 py-2.5 text-[#333] leading-snug">{meta.desc}</td>
                <td className="px-3 py-2.5 text-[#555] leading-snug">
                  {type === "single" && "Narrow, well-scoped tasks. 1-3 tool calls per run."}
                  {type === "multi-tool" && "Tasks with branching conditional logic across many tools."}
                  {type === "multi-agent" && "Work that can be divided into parallel specialist roles."}
                  {type === "orchestrator" && "Long-horizon tasks with complex coordination and replanning."}
                </td>
                <td className="px-3 py-2.5">
                  <ComplexityBadge level={
                    type === "single" ? "simple"
                    : type === "multi-tool" ? "intermediate"
                    : "complex"
                  } />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Root export ──────────────────────────────────────────────────────────────

export function AgentUseCaseMindmap() {
  const [tab, setTab] = useState<"decision" | "domains" | "complexity" | "types">("decision");

  const tabs: { id: typeof tab; label: string }[] = [
    { id: "decision",   label: "Decision Wizard" },
    { id: "domains",    label: "Domain Explorer" },
    { id: "complexity", label: "Complexity Guide" },
    { id: "types",      label: "Agent Types" },
  ];

  return (
    <div className="not-prose my-8 rounded-2xl border-2 border-[#FFDA47]/60 bg-[#fafaf9] p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🗺️</span>
        <h2 className="text-[16px] font-bold text-[#111]">AI Agent Use Case Navigator</h2>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-5 bg-[#f0ece6] rounded-lg p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 text-[12px] font-semibold px-2 py-1.5 rounded-md transition-colors cursor-pointer ${
              tab === t.id
                ? "bg-[#FFDA47] text-[#111] shadow-sm"
                : "text-[#666] hover:text-[#333]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "decision"   && <DecisionWizard />}
      {tab === "domains"    && <DomainExplorer />}
      {tab === "complexity" && <ComplexityGuide />}
      {tab === "types"      && <AgentTypeReference />}
    </div>
  );
}
