"""insight_service.py

Generates plain-English LLM annotations that are stored directly on denial
and claim records at ingestion time.  Reading endpoints return these fields
as regular data — no LLM call ever happens at read time.

Three annotation functions are exposed:

- annotate_denial(denial, use_mock)  → adds insight, appeal_potential,
                                        appeal_rationale to a denial dict
- summarize_stats(stats, use_mock)   → returns a narrative string for /stats
- summarize_claim(claim, denials, use_mock) → returns a narrative string for
                                              /claims/{claim_id}
"""

import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

_bedrock = None


def _get_client():
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
    return _bedrock


def _invoke(system: str, user: str) -> str:
    """Call Claude via Bedrock and return the text response.

    Falls back to an empty string on any error so that a Bedrock outage
    never breaks ingestion.
    """
    try:
        client = _get_client()
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        response = client.invoke_model(
            modelId=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-haiku-4-5-20251001"),
            body=json.dumps(body),
        )
        return json.loads(response["body"].read())["content"][0]["text"].strip()
    except Exception as error:
        return f"[Insight unavailable: {error}]"


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_DENIAL_SYSTEM = (
    "You are a healthcare revenue cycle expert who explains insurance claim "
    "denials in plain English to hospital billing coordinators. "
    "Be concise, factual, and actionable. No jargon. No markdown. "
    "Write in complete sentences. Maximum 3 sentences per field."
)

_STATS_SYSTEM = (
    "You are a healthcare revenue cycle analyst writing a brief executive "
    "summary of denial statistics for a revenue cycle director. "
    "Be specific about numbers and patterns. No markdown. 3-4 sentences."
)

_CLAIM_SYSTEM = (
    "You are a healthcare billing expert explaining what happened to a "
    "submitted insurance claim. Summarise the outcome clearly for a billing "
    "coordinator. No markdown. 2-3 sentences."
)


# ---------------------------------------------------------------------------
# Mock responses (returned when use_mock=True)
# ---------------------------------------------------------------------------

def _mock_denial_insight(denial: dict) -> dict:
    code = denial.get("denial_reason_code", "")
    payer = denial.get("payer", "the payer")
    proc = denial.get("procedure_code", "this service")
    root_cause = denial.get("classification", {}).get("root_cause", "UNKNOWN")
    dx = denial.get("diagnosis_codes") or []

    insight_map = {
        "MISSING_PRIOR_AUTH": (
            f"{payer} denied procedure {proc} because prior authorization was not obtained "
            f"before the service was performed. "
            f"The scheduling team should have confirmed approval before booking this appointment. "
            f"Submit an appeal with medical records and implement a prior-auth check for this payer."
        ),
        "ELIGIBILITY_GAP": (
            f"{payer} denied this claim because the patient's coverage was not active on the "
            f"date of service. "
            f"Registration failed to verify eligibility before the visit. "
            f"Check the patient's current insurance status and resubmit or bill the patient if appropriate."
        ),
        "CODING_ERROR": (
            f"{payer} rejected procedure {proc} due to a coding issue. "
            + (f"The submitted diagnosis {dx[0]} may not support this service under payer policy. " if dx else "")
            + f"Review the CPT and ICD-10 combination with a certified coder before resubmitting."
        ),
        "MEDICAL_NECESSITY": (
            f"{payer} determined that procedure {proc} does not meet their medical necessity criteria. "
            f"The payer's policy requires clinical documentation supporting the need for this service. "
            f"Submit an appeal with physician notes and any supporting clinical evidence."
        ),
        "TIMELY_FILING": (
            f"{payer} denied this claim because it was submitted after their filing deadline. "
            f"The billing team needs to monitor claim aging to prevent future late submissions. "
            f"If you have proof of timely submission, include it in an appeal."
        ),
    }

    insight = insight_map.get(
        root_cause,
        (
            f"{payer} adjusted claim {denial.get('claim_id', '')} with code {code}. "
            f"Review the denial reason and payer contract to determine the correct next step. "
            f"Contact the payer if the adjustment appears incorrect."
        ),
    )

    appeal_map = {
        "MISSING_PRIOR_AUTH": ("MEDIUM", "Prior auth denials can be appealed with clinical records, but retro-authorization approval is not guaranteed."),
        "ELIGIBILITY_GAP": ("LOW", "Eligibility denials are rarely overturned unless the payer made a coverage verification error."),
        "CODING_ERROR": ("HIGH", "Coding errors are correctable — resubmit with the right codes and the claim is likely to pay."),
        "MEDICAL_NECESSITY": ("MEDIUM", "Medical necessity appeals succeed when strong clinical documentation is submitted."),
        "TIMELY_FILING": ("LOW", "Timely filing denials are only overturned with proof of original submission within the deadline."),
        "DUPLICATE_CLAIM": ("LOW", "Duplicate denials are overturned only if the original claim was never actually paid."),
    }
    appeal_potential, appeal_rationale = appeal_map.get(
        root_cause, ("UNKNOWN", "Manual review required to assess appeal potential.")
    )

    return {
        "insight": insight,
        "appeal_potential": appeal_potential,
        "appeal_rationale": appeal_rationale,
    }


def _mock_stats_narrative(stats: dict) -> str:
    total = stats.get("total_denials", 0)
    revenue = stats.get("total_revenue_at_risk", 0.0)
    match_rate = stats.get("match_rate", 0.0)
    top_cause = max(stats.get("by_root_cause", {}).items(), key=lambda x: x[1], default=("UNKNOWN", 0))
    top_payer = max(stats.get("by_payer", {}).items(), key=lambda x: x[1], default=("Unknown", 0))

    return (
        f"You have {total} processed denial records representing ${revenue:,.2f} in revenue at risk. "
        f"The leading root cause is {top_cause[0].replace('_', ' ').title()} "
        f"({top_cause[1]} denials), and {top_payer[0]} is your highest-volume denial payer "
        f"({top_payer[1]} denials). "
        f"{'All denials have been matched to submitted 837 claims, giving full billing context.' if match_rate == 1.0 else f'{int(match_rate * 100)}% of denials have been matched to a submitted 837 claim — ingest the corresponding 837 files to enrich unmatched records.'}"
    )


def _mock_claim_summary(claim: dict, denials: list) -> str:
    claim_id = claim.get("claim_id", "")
    patient = claim.get("patient_name", "the patient")
    payer = claim.get("payer", "the payer")
    total = claim.get("total_charge", 0)
    denial_count = len(denials)

    if not denials:
        return (
            f"Claim {claim_id} for {patient} was submitted to {payer} "
            f"for ${total:,.2f} with no denial adjustments recorded yet. "
            f"Ingest the matching 835 remittance file to see how the payer responded."
        )

    total_denied = sum(d.get("billed_amount", 0) for d in denials)
    causes = list({d.get("classification", {}).get("root_cause", "UNKNOWN") for d in denials})
    cause_str = " and ".join(c.replace("_", " ").title() for c in causes[:2])

    return (
        f"Claim {claim_id} for {patient} received {denial_count} adjustment(s) from {payer} "
        f"totalling ${total_denied:,.2f} in denied or adjusted amounts. "
        f"The primary issue(s) identified: {cause_str}. "
        f"Review the matched denial records below for specific appeal and correction guidance."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def annotate_denial(denial: dict, use_mock: bool = True) -> dict:
    """Add insight, appeal_potential, and appeal_rationale to a denial dict.

    Modifies the dict in place and also returns it.  Called once at
    ingestion time; the result is stored so read endpoints are always fast.
    """
    if use_mock:
        annotations = _mock_denial_insight(denial)
    else:
        classification = denial.get("classification", {})
        dx = denial.get("diagnosis_codes") or []
        user_prompt = f"""Denial record:
- Claim ID: {denial.get('claim_id')}
- Payer: {denial.get('payer')}
- Procedure: {denial.get('procedure_code')} — {denial.get('procedure_name')}
- Diagnosis codes: {dx if dx else 'not available'}
- Denial code: {denial.get('denial_reason_code')}
- Denial text: {denial.get('denial_reason_text')}
- Billed amount: ${denial.get('billed_amount', 0)}
- Root cause: {classification.get('root_cause')}
- Upstream step: {classification.get('upstream_step')}
- Matched to 837 claim: {'YES' if denial.get('matched_claim_id') else 'NO'}
- Classifier explanation: {classification.get('explanation')}

Return a JSON object with exactly these three keys:
{{
  "insight": "2-3 sentences explaining what happened and what to do next, in plain English for a billing coordinator",
  "appeal_potential": "HIGH or MEDIUM or LOW or NONE",
  "appeal_rationale": "One sentence explaining why this denial is or is not worth appealing"
}}"""

        try:
            raw = _invoke(_DENIAL_SYSTEM, user_prompt)
            parsed = json.loads(raw)
            annotations = {
                "insight": str(parsed.get("insight", "")),
                "appeal_potential": str(parsed.get("appeal_potential", "UNKNOWN")),
                "appeal_rationale": str(parsed.get("appeal_rationale", "")),
            }
        except Exception:
            annotations = _mock_denial_insight(denial)

    denial.update(annotations)
    return denial


def summarize_stats(stats: dict, use_mock: bool = True) -> str:
    """Return a plain-English narrative paragraph summarising the stats dict.

    This is called at request time for GET /stats because stats change
    frequently.  The response is lightweight (one string) so LLM latency
    here is acceptable.
    """
    if use_mock:
        return _mock_stats_narrative(stats)

    user_prompt = f"Denial statistics:\n{json.dumps(stats, indent=2)}"
    return _invoke(_STATS_SYSTEM, user_prompt)


def summarize_claim(claim: dict, denials: list, use_mock: bool = True) -> str:
    """Return a plain-English summary of a claim and its matched denials.

    Called at request time for GET /claims/{{claim_id}}.
    """
    if use_mock:
        return _mock_claim_summary(claim, denials)

    user_prompt = (
        f"Submitted claim:\n{json.dumps(claim, indent=2)}\n\n"
        f"Matched denial records ({len(denials)}):\n{json.dumps(denials, indent=2)}"
    )
    return _invoke(_CLAIM_SYSTEM, user_prompt)
