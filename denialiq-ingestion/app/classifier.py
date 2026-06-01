"""classifier.py — Rule-based denial root cause classifier.

Maps denial reason codes and text patterns to standardised root cause
categories.  This runs during ingestion so every stored denial record
already carries a classification.

When an LLM service (e.g. AWS Bedrock) is integrated later, this module
is the single place to swap in the LLM call.
"""

from app.models import ClassificationResult

# ---------------------------------------------------------------------------
# Classification rules
#
# Each rule checks the denial code and/or free-text reason against known
# patterns.  The first matching rule wins.  Order matters — more specific
# rules go first.
# ---------------------------------------------------------------------------


def classify(parsed: dict) -> ClassificationResult:
    """Classify a parsed denial record into a root cause category.

    Args:
        parsed: A dict produced by ``parser.parse_denial()``.  Expected
            keys: ``denial_reason_code``, ``denial_reason_text``.

    Returns:
        A ``ClassificationResult`` with the root cause, responsible
        workflow step, confidence score, and human-readable explanation.
    """
    text = parsed.get("denial_reason_text", "").lower()
    code = parsed.get("denial_reason_code", "").upper()

    # --- Prior authorisation ---
    if "prior auth" in text or "authorization" in text or code == "CO-197":
        return ClassificationResult(
            root_cause="MISSING_PRIOR_AUTH",
            upstream_step="SCHEDULING",
            confidence=0.95,
            payer_rule="Prior authorization is required before this service is performed.",
            explanation=(
                "Authorization was required before the date of service. "
                "The scheduling workflow failed to confirm approval before the patient was seen."
            ),
            recommended_fix=(
                "Submit an appeal with medical records and add a prior-auth "
                "check for this payer and procedure at scheduling."
            ),
        )

    # --- Eligibility / coverage ---
    if "eligible" in text or "coverage" in text or code == "PR-1":
        return ClassificationResult(
            root_cause="ELIGIBILITY_GAP",
            upstream_step="REGISTRATION",
            confidence=0.90,
            payer_rule="Active benefits must be verified for the date of service.",
            explanation=(
                "The patient's coverage was not active on the service date. "
                "Registration failed to verify eligibility before the visit."
            ),
            recommended_fix=(
                "Recheck eligibility and update insurance details before "
                "resubmitting or billing the patient balance."
            ),
        )

    # --- Modifier ---
    if "modifier" in text or code == "CO-4":
        return ClassificationResult(
            root_cause="MISSING_MODIFIER",
            upstream_step="CODING",
            confidence=0.85,
            payer_rule="The appropriate modifier is required when billing this service.",
            explanation=(
                "The service was not payable as coded. "
                "The coding step likely missed a required modifier."
            ),
            recommended_fix="Add the required modifier and resubmit the corrected claim.",
        )

    # --- Bundling (CO-97) ---
    if code == "CO-97":
        return ClassificationResult(
            root_cause="OTHER",
            upstream_step="PAYER_POLICY",
            confidence=0.85,
            payer_rule="This service is bundled into payment for another related service.",
            explanation=(
                "The allowance is included in another adjudicated service. "
                "This is a payer bundling rule, not a workflow failure."
            ),
            recommended_fix=(
                "Review the related paid service. Appeal only if the "
                "service should not be bundled under the payer policy."
            ),
        )

    # --- Contractual / negotiated discount (CO-45, CO-131) ---
    if code in {"CO-45", "CO-131"} or "negotiated discount" in text:
        return ClassificationResult(
            root_cause="OTHER",
            upstream_step="PAYER_POLICY",
            confidence=0.80,
            payer_rule="The charge was reduced to the contracted or fee-schedule rate.",
            explanation=(
                "This is a contractual adjustment, not an error. "
                "The payer applied the negotiated rate from the provider contract."
            ),
            recommended_fix=(
                "Validate the allowed amount against the payer contract "
                "and flag only underpayments for follow-up."
            ),
        )

    # --- Not covered (CO-204) ---
    if code == "CO-204" or "not covered" in text:
        return ClassificationResult(
            root_cause="MEDICAL_NECESSITY",
            upstream_step="PAYER_POLICY",
            confidence=0.80,
            payer_rule="The service is not covered under the patient's current benefit plan.",
            explanation=(
                "The billed service is not covered under the benefit plan. "
                "The payer policy should be checked before submission."
            ),
            recommended_fix=(
                "Confirm benefit coverage and appeal with supporting "
                "clinical documentation if the diagnosis supports the service."
            ),
        )

    # --- Coordination of benefits (OA-23) ---
    if code == "OA-23" or "another payer" in text:
        return ClassificationResult(
            root_cause="INCORRECT_PAYER",
            upstream_step="REGISTRATION",
            confidence=0.85,
            payer_rule="Charges are covered by another payer per coordination of benefits.",
            explanation=(
                "The payer adjusted this claim because another plan is the "
                "primary payer. Registration should verify payer order at intake."
            ),
            recommended_fix=(
                "Submit the claim to the correct primary payer or confirm "
                "coordination of benefits order with the patient."
            ),
        )

    # --- Duplicate ---
    if "duplicate" in text:
        return ClassificationResult(
            root_cause="DUPLICATE_CLAIM",
            upstream_step="BILLING",
            confidence=0.95,
            payer_rule="The payer rejects claims that duplicate a previously adjudicated claim.",
            explanation=(
                "The payer has already received or paid this claim. "
                "The billing workflow resubmitted without checking claim status."
            ),
            recommended_fix=(
                "Check payer claim history. Appeal only if the duplicate "
                "determination is incorrect."
            ),
        )

    # --- Timely filing ---
    if "timely" in text:
        return ClassificationResult(
            root_cause="TIMELY_FILING",
            upstream_step="BILLING",
            confidence=0.90,
            payer_rule="Claims must be submitted within the payer's filing deadline.",
            explanation=(
                "The claim was received after the payer's filing window. "
                "The billing step missed the submission deadline."
            ),
            recommended_fix=(
                "Appeal with proof of timely submission if available. "
                "Monitor aging queues for this payer's deadline."
            ),
        )

    # --- Fallback: assume coding error ---
    return ClassificationResult(
        root_cause="CODING_ERROR",
        upstream_step="CODING",
        confidence=0.70,
        payer_rule="Submitted codes must support the billed service.",
        explanation=(
            "No specific denial pattern was matched. "
            "A coding mismatch is the most likely root cause."
        ),
        recommended_fix=(
            "Review the medical record and payer policy, then resubmit "
            "with supported CPT, ICD-10, and modifier details."
        ),
    )
