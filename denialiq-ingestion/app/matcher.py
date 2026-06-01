from app import claim_storage
from app.edi837 import normalize_procedure_code


def _normalize(code: str) -> str:
    """Return the bare procedure code, stripping any qualifier prefix."""
    return normalize_procedure_code(code).upper()


def find_matching_claim(
    denial_claim_id: str, denial_procedure_code: str
) -> dict | None:
    """Find the submitted 837 claim and service line that match a denial.

    Matching is a two-step process:

    1. Match the claim by ``claim_id`` (exact string comparison).
    2. Within that claim, match the service line by normalised procedure code.

    Args:
        denial_claim_id: The claim ID carried on the 835 denial record.
        denial_procedure_code: The procedure code on the 835 service line
            (may include a qualifier prefix such as ``HC|``).

    Returns:
        A dict with enrichment fields from the matched 837 service line, or
        ``None`` if no match was found.  Shape::

            {
                "matched_claim_id": str,
                "diagnosis_codes": list[str],
                "submitted_charge": float,
                "patient_name": str,
                "provider_name": str,
                "payer": str,
                "date_of_service": str,
            }
    """
    submitted_claims = claim_storage.load_all()
    normalised_denial_code = _normalize(denial_procedure_code)

    for claim in submitted_claims:
        if claim.get("claim_id") != denial_claim_id:
            continue

        # Claim ID matched. Now find the service line.
        for line in claim.get("service_lines") or []:
            line_code = _normalize(str(line.get("procedure_code") or ""))
            if line_code == normalised_denial_code:
                return {
                    "matched_claim_id": claim["claim_id"],
                    "diagnosis_codes": list(line.get("diagnosis_codes") or []),
                    "submitted_charge": line.get("charge_amount", 0.0),
                    "patient_name": claim.get("patient_name", ""),
                    "provider_name": claim.get("provider_name", ""),
                    "payer": claim.get("payer", ""),
                    "date_of_service": claim.get("date_of_service", ""),
                }

        # Claim matched but no service line matched.  Return claim-level
        # context so the denial is still enriched even without a line match.
        return {
            "matched_claim_id": claim["claim_id"],
            "diagnosis_codes": [],
            "submitted_charge": None,
            "patient_name": claim.get("patient_name", ""),
            "provider_name": claim.get("provider_name", ""),
            "payer": claim.get("payer", ""),
            "date_of_service": claim.get("date_of_service", ""),
        }

    return None


def enrich_denial_from_match(denial: dict, match: dict | None) -> dict:
    """Merge 837 match context into a processed denial record.

    If ``match`` is ``None`` the denial is returned unchanged except that
    ``matched_claim_id`` is set to ``None`` to make the unmatched state
    explicit.

    Args:
        denial: A processed denial record dict (as returned by
            ``ProcessedDenial.model_dump()``).
        match: The result of :func:`find_matching_claim`, or ``None``.

    Returns:
        The enriched denial dict.
    """
    if match is None:
        denial["matched_claim_id"] = None
        denial["diagnosis_codes"] = denial.get("diagnosis_codes") or []
        return denial

    denial["matched_claim_id"] = match["matched_claim_id"]
    denial["diagnosis_codes"] = match["diagnosis_codes"]

    # Only back-fill fields that the denial doesn't already carry.
    if not denial.get("patient_name") or denial["patient_name"] == "Anonymous":
        denial["patient_name"] = match["patient_name"] or denial.get("patient_name", "")

    if not denial.get("provider_name"):
        denial["provider_name"] = match["provider_name"]

    if not denial.get("payer"):
        denial["payer"] = match["payer"]

    if not denial.get("date_of_service"):
        denial["date_of_service"] = match["date_of_service"]

    if match.get("submitted_charge") is not None:
        denial["submitted_charge"] = match["submitted_charge"]

    return denial
