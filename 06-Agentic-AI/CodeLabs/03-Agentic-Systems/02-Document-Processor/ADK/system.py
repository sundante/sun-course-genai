"""
Document Processor — Google ADK Implementation
==============================================
System    : 02 — Document Processor
Framework : Google Agent Development Kit (ADK)
Model     : gemini-2.0-flash

What this demonstrates:
  - ADK SequentialAgent for pipeline pattern
  - Each stage as an ADK Agent with a specific role
  - Tool-equipped extraction agent (classify_document_type tool)
  - State passing through ADK's conversation context

Architecture:
  SequentialAgent(classifier_agent, extractor_agent, validator_agent, router_agent)
"""

import os
import json
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import FunctionTool
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService

load_dotenv()

SAMPLE_INVOICE = """
INVOICE #INV-2024-0892
Date: December 15, 2024  |  Due Date: January 15, 2025
Vendor: Acme Software Solutions
Bill To: TechCorp Inc., 123 Main St, San Francisco CA 94105
Line Items:
- Enterprise License (12 months): $24,000.00
- Professional Services: $8,000.00
- Support Package: $3,600.00
Total Due: $38,626.00
"""


# ── Tools ──────────────────────────────────────────────────────────────────────

def get_extraction_schema(document_type: str) -> dict:
    """Get the extraction schema for a given document type.

    Args:
        document_type: The document type (invoice, contract, resume, other)

    Returns:
        dict with required_fields and extraction_instructions
    """
    schemas = {
        "invoice": {
            "required_fields": ["vendor", "total_amount", "invoice_date", "due_date"],
            "instructions": "Extract vendor name, total amount as a number, invoice date (YYYY-MM-DD), due date (YYYY-MM-DD), and line items as a list"
        },
        "contract": {
            "required_fields": ["parties", "effective_date"],
            "instructions": "Extract party names as a list, effective date, key terms, and termination clause if present"
        },
        "resume": {
            "required_fields": ["full_name", "email"],
            "instructions": "Extract full name, email, phone, skills list, work experience list, and education list"
        },
        "other": {
            "required_fields": [],
            "instructions": "Extract any structured data as key-value pairs"
        }
    }
    return schemas.get(document_type, schemas["other"])


def check_routing_rules(document_type: str, validation_passed: bool) -> dict:
    """Look up the routing destination for a document type.

    Args:
        document_type: The classified document type
        validation_passed: Whether validation succeeded

    Returns:
        dict with destination and reason
    """
    if not validation_passed:
        return {"destination": "error_queue", "reason": "Validation failed — manual review required"}

    destinations = {
        "invoice": "accounts_payable_system",
        "contract": "legal_document_management",
        "resume": "hr_applicant_tracking_system",
        "other": "general_document_archive",
    }
    dest = destinations.get(document_type, "general_document_archive")
    return {"destination": dest, "reason": f"{document_type} documents are processed by {dest}"}


# ── ADK Agents ─────────────────────────────────────────────────────────────────

classifier_agent = Agent(
    name="document_classifier",
    model="gemini-2.0-flash",
    description="Classifies document type and confidence",
    instruction="""You are a document classification specialist. Given a document:
    1. Identify the document type: invoice, contract, resume, or other
    2. Estimate your confidence (0.0-1.0) — be honest, use low values for ambiguous documents
    3. Explain your reasoning briefly

    Output format:
    CLASSIFICATION: [type]
    CONFIDENCE: [0.0-1.0]
    REASONING: [explanation]""",
)

extractor_agent = Agent(
    name="data_extractor",
    model="gemini-2.0-flash",
    description="Extracts structured data from classified documents",
    instruction="""You are a data extraction specialist. Based on the document type identified by the classifier:
    1. Use the get_extraction_schema tool to get the correct schema for the document type
    2. Extract all fields specified in the schema
    3. Return the extracted data as a JSON object

    Use null for fields that cannot be found. Return valid JSON only.""",
    tools=[FunctionTool(get_extraction_schema)],
)

validator_agent = Agent(
    name="data_validator",
    model="gemini-2.0-flash",
    description="Validates extracted data completeness and correctness",
    instruction="""You are a data quality validator. Review the extracted data:
    1. Check that all required fields are present and non-null
    2. Verify data types look reasonable
    3. Check for obvious inconsistencies

    Output:
    VALIDATION: PASSED or FAILED
    ISSUES: [list any specific problems, or "none"]
    SUMMARY: [one sentence]""",
)

router_agent = Agent(
    name="document_router",
    model="gemini-2.0-flash",
    description="Routes processed documents to the appropriate handler",
    instruction="""You are a document routing specialist.
    1. Use the check_routing_rules tool with the document_type and whether validation passed
    2. Report the routing decision clearly

    Output:
    DESTINATION: [system name]
    REASON: [why this destination]
    STATUS: success or failed""",
    tools=[FunctionTool(check_routing_rules)],
)

# ── Compose pipeline ────────────────────────────────────────────────────────────

document_processor = SequentialAgent(
    name="document_processing_pipeline",
    description="Complete document processing pipeline: classify → extract → validate → route",
    sub_agents=[classifier_agent, extractor_agent, validator_agent, router_agent],
)


# ── Runner ──────────────────────────────────────────────────────────────────────

def process_document(document_text: str) -> str:
    session_service = InMemorySessionService()
    runner = InProcessRunner(
        agent=document_processor,
        session_service=session_service,
        app_name="document_processor",
    )
    session = session_service.create_session(app_name="document_processor", user_id="u001")

    from google.adk.types import Content, Part
    response = runner.run(
        user_id="u001",
        session_id=session.id,
        new_message=Content(parts=[Part(text=f"Process this document:\n\n{document_text}")]),
    )
    return response.text if hasattr(response, 'text') else str(response)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DOCUMENT PROCESSOR — ADK")
    print("="*60)

    result = process_document(SAMPLE_INVOICE)

    print("\n" + "="*60)
    print("PROCESSING RESULT")
    print("="*60)
    print(result)
