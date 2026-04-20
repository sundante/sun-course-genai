"""
Document Processor — LangGraph Implementation
=============================================
System    : 02 — Document Processor
Framework : LangGraph
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Pipeline pattern as a LangGraph StateGraph
  - Confidence-gated HITL: conditional edge routes to human review below 0.85
  - Validation-gated routing: conditional edge routes to error handler if invalid
  - TypedDict state flowing through classify → extract → validate → route
  - Simulated HITL node (in production: interrupt_before + human input)

Architecture:
  classify → [confidence gate] → extract → validate → [valid gate] → route → END
                  ↓                                         ↓
           hitl_confirm                               error_handler
                  ↓
               extract
"""

import os
import json
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

load_dotenv()

# ── State definition ───────────────────────────────────────────────────────────

class DocumentState(TypedDict):
    document_text: str
    document_type: str
    classification_confidence: float
    classification_reasoning: str
    hitl_triggered: bool
    extracted_data: dict
    validation_result: dict
    routed_to: str
    final_output: dict
    error: Optional[str]


# ── Sample documents ───────────────────────────────────────────────────────────

SAMPLE_DOCS = {
    "invoice": """
    INVOICE #INV-2024-0892
    Date: December 15, 2024
    Due Date: January 15, 2025

    Vendor: Acme Software Solutions
    Bill To: TechCorp Inc., 123 Main St, San Francisco CA 94105

    Line Items:
    - Enterprise License (12 months): $24,000.00
    - Professional Services (40 hours @ $200/hr): $8,000.00
    - Support Package: $3,600.00

    Subtotal: $35,600.00
    Tax (8.5%): $3,026.00
    Total Due: $38,626.00
    """,

    "resume": """
    Jane Smith
    jane.smith@email.com | (555) 123-4567 | San Francisco, CA

    SUMMARY
    Senior Software Engineer with 8 years experience in distributed systems and ML infrastructure.

    SKILLS
    Python, Go, Kubernetes, Spark, TensorFlow, PostgreSQL, Redis

    EXPERIENCE
    Senior Software Engineer — TechCorp (2021-present)
    - Led migration of ML pipeline to Kubernetes, reducing inference latency by 40%
    - Built real-time feature store serving 50M requests/day

    Software Engineer — StartupXYZ (2018-2021)
    - Designed event-driven architecture processing 1B events/day

    EDUCATION
    B.S. Computer Science — UC Berkeley, 2016
    """,

    "ambiguous": """
    This document contains some general information about our products and services.
    We offer various solutions for enterprise customers. Contact us for pricing.
    Our team is available Monday through Friday 9am-5pm Pacific Time.
    """,
}

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

HITL_CONFIDENCE_THRESHOLD = 0.85


# ── Graph nodes ────────────────────────────────────────────────────────────────

def classify_document(state: DocumentState) -> dict:
    """Classify the document type and estimate confidence."""
    print("\n[Classifier] Analyzing document type...")

    response = llm.invoke([
        SystemMessage(content="""Classify this document. Return JSON only:
        {
          "document_type": "invoice|contract|resume|other",
          "confidence": 0.0-1.0,
          "reasoning": "brief explanation"
        }
        Be honest about confidence — use low values when the document is ambiguous."""),
        HumanMessage(content=f"Document:\n{state['document_text']}")
    ]).content

    try:
        # Strip markdown fences if present
        clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        result = {"document_type": "other", "confidence": 0.3, "reasoning": "Could not parse document"}

    confidence = float(result.get("confidence", 0.5))
    doc_type = result.get("document_type", "other")

    print(f"[Classifier] Type: {doc_type} | Confidence: {confidence:.2f}")
    print(f"[Classifier] Reasoning: {result.get('reasoning', '')}")

    return {
        "document_type": doc_type,
        "classification_confidence": confidence,
        "classification_reasoning": result.get("reasoning", ""),
        "hitl_triggered": confidence < HITL_CONFIDENCE_THRESHOLD,
    }


def hitl_confirm(state: DocumentState) -> dict:
    """Simulated HITL node: human confirms the document type.

    In production: use LangGraph's interrupt_before to pause execution
    and wait for actual human input via an API endpoint.
    """
    print(f"\n[HITL Gate] Confidence {state['classification_confidence']:.2f} below threshold {HITL_CONFIDENCE_THRESHOLD}")
    print(f"[HITL Gate] Classifier suggested: '{state['document_type']}'")
    print(f"[HITL Gate] Reasoning: {state['classification_reasoning']}")
    print(f"[HITL Gate] [SIMULATED] Human reviews and confirms: 'invoice'")

    # In production: pause here and wait for human input
    # human_confirmed_type = await get_human_approval(state)
    human_confirmed_type = "invoice"  # Simulated human decision

    return {
        "document_type": human_confirmed_type,
        "hitl_triggered": True,
    }


def extract_data(state: DocumentState) -> dict:
    """Extract structured data based on document type."""
    doc_type = state["document_type"]
    print(f"\n[Extractor] Extracting data for type: {doc_type}")

    schema_instructions = {
        "invoice": "Extract: vendor (str), total_amount (float), invoice_date (str), due_date (str), line_items (list of {description, amount})",
        "contract": "Extract: parties (list of str), effective_date (str), key_terms (list of str), termination_clause (str)",
        "resume": "Extract: full_name (str), email (str), skills (list of str), years_experience (int), education (list of {degree, institution, year})",
        "other": "Extract any structured information you can find as key-value pairs",
    }

    instructions = schema_instructions.get(doc_type, schema_instructions["other"])

    response = llm.invoke([
        SystemMessage(content=f"""You are a data extraction specialist for {doc_type} documents.
        {instructions}
        Return valid JSON only. Use null for missing fields."""),
        HumanMessage(content=f"Document:\n{state['document_text']}")
    ]).content

    try:
        clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        extracted = json.loads(clean)
    except json.JSONDecodeError:
        extracted = {"error": "extraction_failed", "raw": response[:200]}

    print(f"[Extractor] Extracted {len(extracted)} fields")
    return {"extracted_data": extracted}


def validate_extraction(state: DocumentState) -> dict:
    """Validate the extracted data for completeness and consistency."""
    print("\n[Validator] Checking extraction quality...")

    doc_type = state["document_type"]
    extracted = state["extracted_data"]

    required_fields = {
        "invoice": ["vendor", "total_amount", "invoice_date"],
        "resume": ["full_name", "email", "skills"],
        "contract": ["parties", "effective_date"],
        "other": [],
    }

    required = required_fields.get(doc_type, [])
    missing = [f for f in required if f not in extracted or extracted[f] is None]
    has_error = "error" in extracted

    valid = not missing and not has_error
    issues = []
    if missing:
        issues.append(f"Missing required fields: {missing}")
    if has_error:
        issues.append(f"Extraction error: {extracted.get('error')}")

    if valid:
        print("[Validator] Validation PASSED")
    else:
        print(f"[Validator] Validation FAILED: {issues}")

    return {"validation_result": {"valid": valid, "issues": issues}}


def route_document(state: DocumentState) -> dict:
    """Route the validated document to the appropriate handler."""
    doc_type = state["document_type"]

    routing_map = {
        "invoice": "accounts_payable_system",
        "contract": "legal_document_management",
        "resume": "hr_applicant_tracking_system",
        "other": "general_document_archive",
    }

    destination = routing_map.get(doc_type, "general_document_archive")
    print(f"\n[Router] Routing {doc_type} → {destination}")

    return {
        "routed_to": destination,
        "final_output": {
            "document_type": doc_type,
            "confidence": state["classification_confidence"],
            "hitl_triggered": state["hitl_triggered"],
            "extracted_data": state["extracted_data"],
            "validation": state["validation_result"],
            "routed_to": destination,
            "status": "success",
        }
    }


def handle_error(state: DocumentState) -> dict:
    """Error handler for validation failures."""
    print(f"\n[Error Handler] Processing validation failure")
    print(f"[Error Handler] Issues: {state['validation_result']['issues']}")

    return {
        "routed_to": "error_queue",
        "final_output": {
            "document_type": state["document_type"],
            "extracted_data": state["extracted_data"],
            "validation": state["validation_result"],
            "routed_to": "error_queue",
            "status": "failed",
            "error": "Validation failed — manual review required",
        }
    }


# ── Conditional routing functions ──────────────────────────────────────────────

def route_after_classification(state: DocumentState) -> str:
    """Route to HITL if confidence is low, else extract directly."""
    if state["classification_confidence"] < HITL_CONFIDENCE_THRESHOLD:
        return "hitl_confirm"
    return "extract_data"


def route_after_validation(state: DocumentState) -> str:
    """Route to error handler if validation failed, else route document."""
    if state["validation_result"]["valid"]:
        return "route_document"
    return "handle_error"


# ── Build the graph ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(DocumentState)

    graph.add_node("classify_document", classify_document)
    graph.add_node("hitl_confirm", hitl_confirm)
    graph.add_node("extract_data", extract_data)
    graph.add_node("validate_extraction", validate_extraction)
    graph.add_node("route_document", route_document)
    graph.add_node("handle_error", handle_error)

    graph.set_entry_point("classify_document")

    graph.add_conditional_edges("classify_document", route_after_classification, {
        "hitl_confirm": "hitl_confirm",
        "extract_data": "extract_data",
    })

    graph.add_edge("hitl_confirm", "extract_data")
    graph.add_edge("extract_data", "validate_extraction")

    graph.add_conditional_edges("validate_extraction", route_after_validation, {
        "route_document": "route_document",
        "handle_error": "handle_error",
    })

    graph.add_edge("route_document", END)
    graph.add_edge("handle_error", END)

    return graph.compile()


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = build_graph()

    # Test with different documents
    for doc_name, doc_text in SAMPLE_DOCS.items():
        print(f"\n{'='*60}")
        print(f"DOCUMENT PROCESSOR — LangGraph")
        print(f"Processing: {doc_name} document")
        print(f"{'='*60}")

        initial_state = DocumentState(
            document_text=doc_text,
            document_type="",
            classification_confidence=0.0,
            classification_reasoning="",
            hitl_triggered=False,
            extracted_data={},
            validation_result={},
            routed_to="",
            final_output={},
            error=None,
        )

        final_state = app.invoke(initial_state)

        print(f"\n--- Final Output ---")
        print(f"Status: {final_state['final_output'].get('status')}")
        print(f"Type: {final_state['final_output'].get('document_type')}")
        print(f"HITL triggered: {final_state['final_output'].get('hitl_triggered')}")
        print(f"Routed to: {final_state['final_output'].get('routed_to')}")

        print("\n")  # separator between documents
