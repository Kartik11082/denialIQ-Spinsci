import re
from datetime import datetime

from app.models import RawDenialInput

DENIAL_CODE_NAMES = {
    "CO-4": "Service not covered",
    "CO-11": "Diagnosis inconsistent with procedure",
    "CO-16": "Missing or incorrect information",
    "CO-45": "Charge exceeds fee schedule or contracted arrangement",
    "CO-97": "Benefit included in global service",
    "CO-131": "Claim specific negotiated discount",
    "CO-197": "Prior authorization required",
    "CO-204": "Service not covered under benefit plan",
    "PR-1": "Deductible not met",
    "PR-2": "Coinsurance amount",
    "OA-23": "Payment adjusted - primary plan paid",
}

PROCEDURE_NAMES = {
    "73721": "MRI Knee Joint",
    "27447": "Total Knee Replacement",
    "99213": "Office Visit - Established Patient",
    "99214": "Office Visit - Moderate Complexity",
    "93000": "Electrocardiogram",
    "71046": "Chest X-Ray",
    "70553": "MRI Brain with contrast",
    "45378": "Colonoscopy",
    "80053": "Comprehensive Metabolic Panel",
}

DEPARTMENT_BY_PREFIX = {
    "7": "Radiology",
    "9": "Evaluation & Management",
    "2": "Surgery",
    "4": "Gastroenterology",
    "8": "Laboratory",
}


def parse_denial(raw: RawDenialInput) -> dict:
    denial = raw.model_dump()

    denial_code = raw.denial_reason_code.strip().upper()
    procedure_code = raw.procedure_code.strip()

    denial["denial_reason_code"] = denial_code
    denial["denial_reason_name"] = DENIAL_CODE_NAMES.get(denial_code, denial_code)
    denial["procedure_code"] = procedure_code
    denial["procedure_name"] = (
        raw.procedure_name.strip()
        or PROCEDURE_NAMES.get(procedure_code)
        or f"Procedure {procedure_code}"
    )
    denial["department"] = raw.department.strip() or DEPARTMENT_BY_PREFIX.get(
        procedure_code[:1], "General"
    )
    denial["processed_at"] = datetime.now().isoformat()

    return denial


def validate_denial(raw: RawDenialInput) -> tuple[bool, str]:
    if not raw.claim_id.strip():
        return False, "claim_id is required"

    if not raw.payer.strip():
        return False, "payer is required"

    denial_code = raw.denial_reason_code.strip().upper()
    if denial_code and not re.match(r"^(CO|PR|OA)-\d+$", denial_code):
        return False, "denial_reason_code must match pattern CO-XXX, PR-X, or OA-XX"

    if raw.billed_amount < 0:
        return False, "billed_amount must be greater than or equal to 0"

    procedure_code = raw.procedure_code.strip()
    if procedure_code and not re.match(r"^\d{5}$", procedure_code):
        return False, "procedure_code must be 5 digits"

    return True, ""
