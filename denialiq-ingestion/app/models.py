from typing import Any, Optional

from pydantic import BaseModel, Field


class RawDenialInput(BaseModel):
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
    root_cause: str
    upstream_step: str
    confidence: float
    explanation: str
    recommended_fix: str
    payer_rule: str


class ProcessedDenial(BaseModel):
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
    # 837 match enrichment
    matched_claim_id: Optional[str] = None
    diagnosis_codes: list[str] = Field(default_factory=list)
    submitted_charge: Optional[float] = None
    # LLM annotations (stored at write time)
    insight: str = ""
    appeal_potential: str = ""  # HIGH | MEDIUM | LOW | NONE
    appeal_rationale: str = ""


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
