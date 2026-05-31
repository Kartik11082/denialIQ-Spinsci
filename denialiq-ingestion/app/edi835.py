import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.models import RawDenialInput

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PARSED_835_FILE = (
    PROJECT_ROOT / "scripts" / "output" / "X221-claim-specific-negotiated-discount.json"
)
MOCK_835_DIR = (
    PROJECT_ROOT / "data" / "mock" / "005010X221 Health Care Claim Payment Advice"
)

CARC_DESCRIPTIONS = {
    "45": "Charge exceeds fee schedule, maximum allowable, or contracted arrangement",
    "97": "Benefit included in payment or allowance for another service already adjudicated",
    "131": "Claim specific negotiated discount",
    "197": "Prior authorization required and not obtained",
    "204": "Service not covered under the patient's current benefit plan",
}


def resolve_project_path(
    path: str | None, default_path: Path = DEFAULT_PARSED_835_FILE
) -> Path:
    candidate = default_path if not path else PROJECT_ROOT / path
    resolved = candidate.resolve()

    if PROJECT_ROOT not in resolved.parents and resolved != PROJECT_ROOT:
        raise ValueError("Path must stay inside the denialiq-ingestion project")

    return resolved


def list_mock_835_files() -> list[dict[str, Any]]:
    if not MOCK_835_DIR.exists():
        return []

    return [
        {
            "file_name": file_path.name,
            "relative_path": str(file_path.relative_to(PROJECT_ROOT)),
            "size_bytes": file_path.stat().st_size,
        }
        for file_path in sorted(MOCK_835_DIR.glob("*.edi"))
    ]


def load_parsed_835(path: str | None = None) -> dict:
    file_path = resolve_project_path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Parsed 835 file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Parsed 835 file is empty: {file_path}")

    return json.loads(content)


def convert_835_date(value: str | None) -> str:
    if not value:
        return ""

    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return value


def parse_amount(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_procedure_code(value: str | None) -> str:
    if not value:
        return ""

    code = value.strip()
    for separator in ("|", ":"):
        if separator in code:
            code = code.split(separator)[-1]

    return code


def infer_department_from_procedure(procedure_code: str) -> str:
    if procedure_code.upper().startswith("D"):
        return "Dental"

    if procedure_code.startswith("8"):
        return "Laboratory"

    if procedure_code.startswith("9"):
        return "Evaluation & Management"

    if procedure_code.startswith("7"):
        return "Radiology"

    return "General"


def build_denial_reason_text(adjustment: dict) -> str:
    reason_code = str(adjustment.get("reason_code", "")).strip()
    description = CARC_DESCRIPTIONS.get(reason_code)
    if description:
        return description

    group = str(adjustment.get("group", "")).strip().upper()
    return f"835 adjustment {group}-{reason_code}".strip()


def raw_denials_from_parsed_835(
    parsed_835: dict, source_file: str = ""
) -> list[RawDenialInput]:
    payment_info = parsed_835.get("payment_info", {})
    transaction_date = convert_835_date(payment_info.get("transaction_date"))
    payer = (
        parsed_835.get("payer_name")
        or parsed_835.get("sender_id")
        or parsed_835.get("receiver_id")
        or "Unknown Payer"
    )

    raw_denials: list[RawDenialInput] = []
    sequence = 1

    for claim in parsed_835.get("claims", []):
        claim_id = str(claim.get("claim_id", "")).strip()
        service_lines = claim.get("service_lines") or []
        patient_name = (
            claim.get("patient_name") or parsed_835.get("patient_name") or "Anonymous"
        )
        provider_name = claim.get("provider_name") or parsed_835.get(
            "provider_name", ""
        )
        claim_service_date = (
            convert_835_date(claim.get("date_of_service")) or transaction_date
        )

        for service_line in service_lines:
            procedure_code = clean_procedure_code(service_line.get("procedure_code"))
            charge_amount = parse_amount(service_line.get("charge_amount"))
            paid_amount = parse_amount(service_line.get("paid_amount"))
            default_risk_amount = max(charge_amount - paid_amount, 0.0)

            for adjustment in service_line.get("adjustments", []):
                group = str(adjustment.get("group", "")).strip().upper()
                reason_code = str(adjustment.get("reason_code", "")).strip()
                adjustment_amount = parse_amount(
                    adjustment.get("amount"), default_risk_amount
                )
                denial_code = (
                    f"{group}-{reason_code}" if group and reason_code else reason_code
                )

                raw_denials.append(
                    RawDenialInput(
                        claim_id=f"{claim_id}-{procedure_code}-{sequence}",
                        patient_name=patient_name,
                        date_of_service=convert_835_date(
                            service_line.get("date_of_service")
                        )
                        or claim_service_date,
                        payer=payer,
                        plan_type=payment_info.get("payment_method", ""),
                        procedure_code=procedure_code,
                        procedure_name="",
                        diagnosis_code="",
                        billed_amount=adjustment_amount,
                        denial_reason_code=denial_code,
                        denial_reason_text=build_denial_reason_text(adjustment),
                        department=infer_department_from_procedure(procedure_code),
                        provider_name=provider_name,
                    )
                )
                sequence += 1

        for adjustment in claim.get("adjustments", []):
            group = str(adjustment.get("group", "")).strip().upper()
            reason_code = str(adjustment.get("reason_code", "")).strip()
            denial_code = (
                f"{group}-{reason_code}" if group and reason_code else reason_code
            )

            raw_denials.append(
                RawDenialInput(
                    claim_id=f"{claim_id}-CLAIM-{sequence}",
                    patient_name=patient_name,
                    date_of_service=claim_service_date,
                    payer=payer,
                    plan_type=payment_info.get("payment_method", ""),
                    procedure_code="",
                    procedure_name="Claim-level adjustment",
                    diagnosis_code="",
                    billed_amount=parse_amount(adjustment.get("amount")),
                    denial_reason_code=denial_code,
                    denial_reason_text=build_denial_reason_text(adjustment),
                    department="General",
                    provider_name=provider_name,
                )
            )
            sequence += 1

    return raw_denials
