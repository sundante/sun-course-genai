"""
Document Processor — CrewAI Implementation
==========================================
System    : 02 — Document Processor
Framework : CrewAI
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Sequential CrewAI process for pipeline pattern
  - Task context passing: each task receives previous task outputs
  - Role-based agents for classification, extraction, and validation
  - Structured output via expected_output descriptions

Architecture:
  Classifier Agent → Extractor Agent → Validator Agent → Router Agent
  (sequential, each task gets previous task as context)
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

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

# ── Agents ─────────────────────────────────────────────────────────────────────

classifier = Agent(
    role="Document Classification Specialist",
    goal="Accurately classify document types and assess confidence",
    backstory="""You are an expert at identifying document types from their content and structure.
    You provide confidence scores that reflect your actual certainty — you never overstate confidence.
    When a document is ambiguous, you say so clearly.""",
    llm=llm,
    verbose=True,
)

extractor = Agent(
    role="Structured Data Extraction Specialist",
    goal="Extract all relevant structured fields from documents with high accuracy",
    backstory="""You specialize in extracting structured data from business documents.
    You know the key fields for invoices, contracts, resumes, and other common document types.
    You always return valid JSON and mark fields as null when they cannot be found.""",
    llm=llm,
    verbose=True,
)

validator = Agent(
    role="Data Quality Validator",
    goal="Verify that extracted data meets completeness and consistency requirements",
    backstory="""You ensure that document processing outputs meet quality standards.
    You check for required fields, data type consistency, and logical correctness.
    You provide specific, actionable feedback when validation fails.""",
    llm=llm,
    verbose=True,
)

router = Agent(
    role="Document Routing Specialist",
    goal="Route processed documents to the correct downstream system based on type and validation status",
    backstory="""You manage document workflow routing. You know which system handles each document type:
    invoices → accounts_payable, contracts → legal_document_management,
    resumes → hr_applicant_tracking, failed documents → error_queue.""",
    llm=llm,
    verbose=True,
)


# ── Build crew ─────────────────────────────────────────────────────────────────

def build_processing_crew(document_text: str) -> Crew:
    classify_task = Task(
        description=f"""Classify this document and return a JSON result:
        {{
          "document_type": "invoice|contract|resume|other",
          "confidence": 0.0-1.0,
          "reasoning": "explanation"
        }}

        Document to classify:
        {document_text}

        Be honest about confidence. Use values below 0.7 for ambiguous documents.""",
        expected_output="JSON object with document_type, confidence score, and reasoning",
        agent=classifier,
    )

    extract_task = Task(
        description=f"""Extract structured data from this document based on its type (from the classification result).

        For invoices extract: vendor, total_amount, invoice_date, due_date, line_items
        For resumes extract: full_name, email, skills, years_experience, education
        For contracts extract: parties, effective_date, key_terms
        For other: extract any structured information

        Document:
        {document_text}

        Return valid JSON. Use null for missing fields.""",
        expected_output="JSON object with all relevant structured fields extracted from the document",
        agent=extractor,
        context=[classify_task],
    )

    validate_task = Task(
        description="""Validate the extracted data from the previous step.

        Check:
        1. Are all required fields present and non-null?
           - invoice: vendor, total_amount, invoice_date required
           - resume: full_name, email required
           - contract: parties, effective_date required
        2. Do data types look correct? (amounts are numbers, dates are strings)
        3. Are there any obvious inconsistencies?

        Return: {"valid": true/false, "issues": ["list of specific issues"], "summary": "one line"}""",
        expected_output="JSON validation result with valid boolean, issues list, and summary",
        agent=validator,
        context=[classify_task, extract_task],
    )

    route_task = Task(
        description="""Determine the routing destination for this processed document.

        Routing rules:
        - invoice (valid) → accounts_payable_system
        - contract (valid) → legal_document_management
        - resume (valid) → hr_applicant_tracking_system
        - other (valid) → general_document_archive
        - any (invalid/failed validation) → error_queue

        Based on the document type and validation result from previous tasks,
        determine the destination and explain why.

        Return: {"destination": "system_name", "reason": "explanation", "status": "success|failed"}""",
        expected_output="JSON routing decision with destination, reason, and status",
        agent=router,
        context=[classify_task, extract_task, validate_task],
    )

    return Crew(
        agents=[classifier, extractor, validator, router],
        tasks=[classify_task, extract_task, validate_task, route_task],
        process=Process.sequential,
        verbose=True,
    )


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DOCUMENT PROCESSOR — CrewAI")
    print("="*60)

    crew = build_processing_crew(SAMPLE_INVOICE)
    result = crew.kickoff()

    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(result)
