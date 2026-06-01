from datetime import datetime
from pathlib import Path

from app.edi835 import convert_835_date

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Procedure-code prefixes that appear in 837 CLM/SV1 segments
# and the qualifier positions used by clearinghouses.
_CODE_QUALIFIER_SEPARATORS = ("|", ":")


def normalize_procedure_code(code: str) -> str:
    """Strip qualifier prefixes like HC|, AD|, B3|, WK| from procedure codes.

    ANSI X12 837 service lines encode the code set qualifier and the code
    together (e.g. ``HC|99213`` or ``HC:99213``).  We only need the bare
    code for matching and storage.
    """
    code = code.strip()
    for sep in _CODE_QUALIFIER_SEPARATORS:
        if sep in code:
            return code.split(sep)[-1].strip()
    return code


# ---------------------------------------------------------------------------
# Field-name aliases
#
# Different 837 parsers (and clearinghouses) surface the same logical fields
# under different key names.  Each tuple below lists accepted aliases in
# priority order; the first non-empty value wins.
# ---------------------------------------------------------------------------


def _first(*values) -> str:
    """Return the first truthy string value, or empty string."""
    for v in values:
        if v and str(v).strip():
            return str(v).strip()
    return ""


def _first_float(*values, default: float = 0.0) -> float:
    """Return the first value that can be coerced to float."""
    for v in values:
        if v is not None and str(v).strip():
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return default


def _resolve_claim_id(claim: dict) -> str:
    """Return the claim ID from whichever field name the parser used."""
    return _first(
        claim.get("claim_id"),
        claim.get("claim_submitter_id"),  # common in professional 837 parsers
        claim.get("submitter_claim_id"),
        claim.get("patient_control_number"),
        claim.get("id"),
    )


def _resolve_diagnosis_codes(claim: dict) -> list[str]:
    """Return diagnosis codes from whichever field name the parser used."""
    for key in ("diagnosis_codes", "diagnoses", "dx_codes", "icd_codes"):
        value = claim.get(key)
        if value and isinstance(value, list):
            return [str(d).strip() for d in value if d]
    return []


def _extract_service_lines(
    raw_lines: list[dict], claim_level_dx: list[str]
) -> list[dict]:
    """Convert raw parsed 837 service lines into the clean internal format.

    Accepts multiple field-name aliases so the function is resilient to
    different 837 parser outputs.

    Claim-level diagnosis codes are propagated down to service lines that
    don't carry their own.
    """
    lines = []
    for line in raw_lines:
        procedure_code = normalize_procedure_code(
            _first(
                line.get("procedure_code"), line.get("cpt_code"), line.get("hcpcs_code")
            )
        )
        if not procedure_code:
            continue

        charge_amount = _first_float(
            line.get("charge_amount"),
            line.get("line_charge"),  # ambulance / HCFA parsers often use this
            line.get("billed_amount"),
            line.get("submitted_amount"),
            default=0.0,
        )

        # Line-level dx codes; fall back to claim-level if absent.
        line_dx: list[str] = []
        for key in ("diagnosis_codes", "diagnoses", "dx_codes"):
            v = line.get(key)
            if v and isinstance(v, list):
                line_dx = [str(d).strip() for d in v if d]
                break

        if not line_dx:
            line_dx = claim_level_dx

        lines.append(
            {
                "procedure_code": procedure_code,
                "charge_amount": charge_amount,
                "diagnosis_codes": line_dx,
                "modifiers": list(line.get("modifiers") or []),
                "units": _first(str(line.get("units") or ""), "1"),
            }
        )
    return lines


def _resolve_patient_name(parsed_837: dict, claim: dict) -> str:
    """Return the patient name from whichever location the parser put it."""
    # 1. Claim-level patient name
    name = _first(
        claim.get("patient_name"),
        (
            claim.get("patient", {}).get("name")
            if isinstance(claim.get("patient"), dict)
            else ""
        ),
    )
    if name:
        return name

    # 2. Top-level patient/subscriber
    patient_block = parsed_837.get("patient") or {}
    subscriber_block = parsed_837.get("subscriber") or {}

    return _first(
        parsed_837.get("patient_name"),
        patient_block.get("name") if isinstance(patient_block, dict) else "",
        subscriber_block.get("name") if isinstance(subscriber_block, dict) else "",
        parsed_837.get("subscriber_name"),
    )


def _resolve_provider_name(parsed_837: dict, claim: dict) -> str:
    """Return the billing/rendering provider name."""
    billing_provider = parsed_837.get("billing_provider") or {}

    return _first(
        claim.get("provider_name"),
        claim.get("rendering_provider"),
        parsed_837.get("provider_name"),
        billing_provider.get("name") if isinstance(billing_provider, dict) else "",
        parsed_837.get("billing_provider_name"),
    )


def _resolve_payer_name(parsed_837: dict, claim: dict) -> str:
    """Return the payer name."""
    payer_block = parsed_837.get("payer") or {}

    return _first(
        claim.get("payer_name"),
        parsed_837.get("payer_name"),
        payer_block.get("name") if isinstance(payer_block, dict) else "",
        parsed_837.get("receiver_id"),
        "Unknown Payer",
    )


def _resolve_date_of_service(parsed_837: dict, claim: dict) -> str:
    """Return the date of service in ISO format, trying multiple field names."""
    raw = _first(
        claim.get("date_of_service"),
        claim.get("service_date"),
        claim.get("dos"),
        claim.get("statement_from_date"),
        parsed_837.get("date_of_service"),
        parsed_837.get("transaction_date"),
    )
    return convert_835_date(raw)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def submitted_claims_from_parsed_837(
    parsed_837: dict,
    source_file: str = "",
) -> list[dict]:
    """Convert a parsed 837 JSON document into a list of submitted claim records.

    Each claim in the ``claims`` list becomes one entry in ``data/claims.json``.
    The function accepts multiple field-name conventions so it works with
    output from different 837 EDI parsers without modification.

    Args:
        parsed_837: The parsed 837 JSON — either from a parser script or
            posted directly to the API.
        source_file: Optional label for tracing which source file this
            came from.

    Returns:
        List of normalised submitted-claim dicts ready for storage.
    """
    ingested_at = datetime.now().isoformat()
    claims: list[dict] = []

    for claim in parsed_837.get("claims") or []:
        claim_id = _resolve_claim_id(claim)
        if not claim_id:
            continue

        claim_level_dx = _resolve_diagnosis_codes(claim)
        service_lines = _extract_service_lines(
            claim.get("service_lines") or [],
            claim_level_dx,
        )

        total_charge = _first_float(
            claim.get("total_charge"),
            claim.get("total_billed_amount"),  # common alias
            claim.get("billed_amount"),
            claim.get("clm_amount"),
            default=0.0,
        )

        claims.append(
            {
                "claim_id": claim_id,
                "patient_name": _resolve_patient_name(parsed_837, claim),
                "payer": _resolve_payer_name(parsed_837, claim),
                "provider_name": _resolve_provider_name(parsed_837, claim),
                "date_of_service": _resolve_date_of_service(parsed_837, claim),
                "total_charge": total_charge,
                "diagnosis_codes": claim_level_dx,
                "service_lines": service_lines,
                "source": "837",
                "source_file": source_file or parsed_837.get("source_file", ""),
                "ingested_at": ingested_at,
            }
        )

    return claims
