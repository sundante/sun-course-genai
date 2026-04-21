"""
Document Processor — LangChain Implementation
=============================================
System    : 02 — Document Processor
Framework : LangChain (LCEL)
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Pipeline pattern implemented as sequential Python functions with LCEL chains
  - Confidence-gated HITL using simple conditional logic
  - Validation-gated routing (route to error handler if extraction fails)
  - Structured JSON extraction using LLM + output parsing

Architecture:
  classify() → [confidence gate] → extract() → validate() → route()
                     ↓
               hitl_confirm()
                     ↓
                  extract()
"""

import os
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

HITL_CONFIDENCE_THRESHOLD = 0.85

SAMPLE_INVOICE = """
INVOICE #INV-2024-0892
Date: December 15, 2024  |  Due Date: January 15, 2025

Vendor: Acme Software Solutions
Bill To: TechCorp Inc., 123 Main St, San Francisco CA 94105

Line Items:
- Enterprise License (12 months): $24,000.00
- Professional Services (40 hours @ $200/hr): $8,000.00
- Support Package: $3,600.00

Total Due: $38,626.00
"""


# ── Pipeline stage functions ────────────────────────────────────────────────────

def classify_document(document_text: str) -> dict:
    """Stage 1: Classify document type and confidence."""
    print("\n[Classifier] Analyzing document type...")

    response = llm.invoke([
        SystemMessage(content="""Classify this document. Return JSON only:
        {"document_type": "invoice|contract|resume|other", "confidence": 0.0-1.0, "reasoning": "..."}
        Use low confidence values for ambiguous documents."""),
        HumanMessage(content=f"Document:\n{document_text}")
    ]).content

    try:
        clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        result = {"document_type": "other", "confidence": 0.3, "reasoning": "Parse error"}

    print(f"[Classifier] Type: {result['document_type']} | Confidence: {result['confidence']:.2f}")
    return result


def hitl_confirm(classification: dict) -> str:
    """HITL Gate: simulated human confirmation when confidence is low."""
    print(f"\n[HITL Gate] Low confidence ({classification['confidence']:.2f}) — requesting human review")
    print(f"[HITL Gate] Classifier suggested: '{classification['document_type']}'")
    print(f"[HITL Gate] [SIMULATED] Human confirms: 'invoice'")
    return "invoice"  # Simulated human input


def extract_structured_data(document_text: str, doc_type: str) -> dict:
    """Stage 2: Extract structured fields based on document type."""
    print(f"\n[Extractor] Extracting {doc_type} fields...")

    schema_map = {
        "invoice": "vendor (str), total_amount (float), invoice_date (str), due_date (str), line_items (list)",
        "resume": "full_name (str), email (str), skills (list of str), years_experience (int)",
        "contract": "parties (list of str), effective_date (str), key_terms (list of str)",
        "other": "any structured data as key-value pairs",
    }
    schema = schema_map.get(doc_type, schema_map["other"])

    response = llm.invoke([
        SystemMessage(content=f"Extract these fields from the {doc_type} document: {schema}. Return JSON only. Use null for missing fields."),
        HumanMessage(content=document_text)
    ]).content

    try:
        clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        extracted = json.loads(clean)
    except json.JSONDecodeError:
        extracted = {"error": "extraction_failed"}

    print(f"[Extractor] Extracted {len(extracted)} fields")
    return extracted


def validate_extraction(extracted: dict, doc_type: str) -> dict:
    """Stage 3: Validate extracted data for required fields."""
    print("\n[Validator] Checking extraction completeness...")

    required = {
        "invoice": ["vendor", "total_amount", "invoice_date"],
        "resume": ["full_name", "email"],
        "contract": ["parties"],
        "other": [],
    }.get(doc_type, [])

    missing = [f for f in required if f not in extracted or extracted[f] is None]
    valid = not missing and "error" not in extracted
    issues = [f"Missing: {missing}"] if missing else []
    if "error" in extracted:
        issues.append(f"Extraction error: {extracted['error']}")

    status = "PASSED" if valid else "FAILED"
    print(f"[Validator] Validation {status}" + (f" — {issues}" if issues else ""))
    return {"valid": valid, "issues": issues}


def route_document(doc_type: str, extracted: dict, validation: dict) -> dict:
    """Stage 4: Route to appropriate handler."""
    destination = {
        "invoice": "accounts_payable_system",
        "contract": "legal_document_management",
        "resume": "hr_applicant_tracking_system",
        "other": "general_document_archive",
    }.get(doc_type, "general_document_archive")

    if not validation["valid"]:
        destination = "error_queue"

    print(f"\n[Router] → {destination}")
    return {
        "document_type": doc_type,
        "extracted_data": extracted,
        "validation": validation,
        "routed_to": destination,
        "status": "success" if validation["valid"] else "failed",
    }


# ── Pipeline orchestrator ──────────────────────────────────────────────────────

def process_document(document_text: str) -> dict:
    """Run the full document processing pipeline."""
    # Stage 1: Classify
    classification = classify_document(document_text)
    doc_type = classification["document_type"]
    confidence = classification["confidence"]

    # HITL gate
    if confidence < HITL_CONFIDENCE_THRESHOLD:
        doc_type = hitl_confirm(classification)

    # Stage 2: Extract
    extracted = extract_structured_data(document_text, doc_type)

    # Stage 3: Validate
    validation = validate_extraction(extracted, doc_type)

    # Stage 4: Route
    result = route_document(doc_type, extracted, validation)
    return result


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DOCUMENT PROCESSOR — LangChain")
    print("="*60)

    result = process_document(SAMPLE_INVOICE)

    print("\n--- Final Output ---")
    print(f"Status: {result['status']}")
    print(f"Type: {result['document_type']}")
    print(f"Routed to: {result['routed_to']}")
    print(f"Extracted fields: {list(result['extracted_data'].keys())}")
