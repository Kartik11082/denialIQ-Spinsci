"""models.py — Pydantic data models for the DenialIQ ingestion pipeline.

Three models define the contract between the API, the processing pipeline,
and storage:

- RawDenialInput:      what comes in (from the API or the 835 converter)
- ClassificationResult: the root-cause classification attached to each denial
- ProcessedDenial:      the final record stored in denials.json
- APIResponse:          standard wrapper for all API responses
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class RawDenialInput(BaseModel):
    """Raw denial data as received from the API or extracted from an 835."""
    claim_id: str
    patient_name: str = "Anonymous"
    date_of_service: str = ""
    payer: str
    plan_type: str = ""
    procedure_code: str = ""
    procedure_name: str = ""
    diagnosis_code: str = ""
    billed_amount: float = 0.0
    denial_reason_code: str = ""
    denial_reason_text: str = ""
    department: str = ""
    provider_name: str = ""


class ClassificationResult(BaseModel):
    """Root-cause classification produced by the classifier."""
    root_cause: str           # e.g. MISSING_PRIOR_AUTH, CODING_ERROR
    upstream_step: str        # e.g. SCHEDULING, CODING, REGISTRATION
    confidence: float         # 0.0 – 1.0
    explanation: str          # human-readable reason
    recommended_fix: str      # actionable next step
    payer_rule: str           # which payer rule applies


class ProcessedDenial(BaseModel):
    """A fully processed denial record ready for storage."""
    claim_id: str
    patient_name: str
    date_of_service: str
    payer: str
    plan_type: str
    procedure_code: str
    procedure_name: str
    diagnosis_code: str
    billed_amount: float
    denial_reason_code: str
    denial_reason_text: str
    department: str
    provider_name: str
    classification: ClassificationResult
    processed_at: str
    status: str = "CLASSIFIED"

    # Fields added by the 837 matcher (populated when a matching claim exists)
    matched_claim_id: Optional[str] = None
    diagnosis_codes: list[str] = Field(default_factory=list)
    submitted_charge: Optional[float] = None


class APIResponse(BaseModel):
    """Standard envelope for every API response."""
    success: bool
    message: str
    data: Optional[Any] = None
