import json
import os

import boto3
from dotenv import load_dotenv

from app.models import ClassificationResult

load_dotenv()

bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)


SYSTEM_PROMPT = """You are a healthcare revenue cycle analyst specializing 
in insurance claim denial root cause analysis. You have deep knowledge 
of payer policies, billing codes, and healthcare workflows. 
Always return valid JSON only. No markdown, no explanation outside JSON."""


def classify_denial(parsed: dict) -> ClassificationResult:
    user = f"""Analyze this denied insurance claim and classify the root cause.

Claim details:
- Payer: {parsed['payer']}
- Procedure: {parsed['procedure_code']} - {parsed['procedure_name']}
- Diagnosis: {parsed['diagnosis_code']}
- Denial code: {parsed['denial_reason_code']}
- Denial text: {parsed['denial_reason_text']}
- Department: {parsed['department']}
- Billed amount: ${parsed['billed_amount']}

Classify the root cause into exactly ONE of these categories:
- MISSING_PRIOR_AUTH: Prior authorization was required but not obtained
- ELIGIBILITY_GAP: Patient was not covered on the date of service
- CODING_ERROR: Wrong CPT or ICD-10 code was used
- MISSING_MODIFIER: A required billing modifier was absent
- TIMELY_FILING: Claim was submitted past the deadline
- MEDICAL_NECESSITY: Payer determined the service was not medically necessary
- DUPLICATE_CLAIM: Claim was already submitted or paid
- OTHER: None of the above categories apply

Identify the upstream workflow step where the error occurred:
- SCHEDULING: Error happened when appointment was booked
- REGISTRATION: Error in patient demographics or insurance capture
- CODING: Error in how the service was coded
- BILLING: Error in claim preparation or submission
- PAYER_POLICY: Payer changed a rule the hospital was unaware of

Return this exact JSON structure:
{{
    "root_cause": "CATEGORY_NAME",
    "upstream_step": "STEP_NAME", 
    "confidence": 0.95,
    "payer_rule": "One sentence describing the specific payer rule that applies",
    "explanation": "Two sentences explaining exactly why this claim was denied and which step failed",
    "recommended_fix": "One specific action to either appeal this denial or prevent it next time"
}}"""

    try:
        response = bedrock_client.invoke_model(
            modelId=os.getenv("BEDROCK_MODEL_ID"),
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 800,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user}],
                }
            ),
        )
        response_body = json.loads(response["body"].read())
        content = response_body["content"][0]["text"]
        result = json.loads(content)
        return ClassificationResult(**result)
    except Exception as error:
        return ClassificationResult(
            root_cause="UNKNOWN",
            upstream_step="UNKNOWN",
            confidence=0.0,
            explanation=f"Classification failed: {error}",
            recommended_fix="Manual review required",
            payer_rule="Unable to retrieve",
        )


def classify_mock(parsed: dict) -> ClassificationResult:
    denial_text = parsed.get("denial_reason_text", "").lower()
    denial_code = parsed.get("denial_reason_code", "").upper()

    if (
        "prior auth" in denial_text
        or "authorization" in denial_text
        or denial_code == "CO-197"
    ):
        return ClassificationResult(
            root_cause="MISSING_PRIOR_AUTH",
            upstream_step="SCHEDULING",
            confidence=0.95,
            payer_rule="The payer requires prior authorization before this service is performed.",
            explanation="The denial indicates authorization was required before the date of service. The scheduling workflow failed to confirm or obtain approval before the patient was seen.",
            recommended_fix="Submit an appeal with medical records and implement a scheduling prior-auth check for this payer and procedure.",
        )

    if "eligible" in denial_text or "coverage" in denial_text or denial_code == "PR-1":
        return ClassificationResult(
            root_cause="ELIGIBILITY_GAP",
            upstream_step="REGISTRATION",
            confidence=0.90,
            payer_rule="The payer only covers services when active benefits are verified for the date of service.",
            explanation="The denial suggests the patient's coverage or benefits were not active for the service date. Registration failed to verify eligibility before claim submission.",
            recommended_fix="Recheck eligibility for the service date and update insurance details before resubmitting or billing the patient balance as appropriate.",
        )

    if "modifier" in denial_text or denial_code == "CO-4":
        return ClassificationResult(
            root_cause="MISSING_MODIFIER",
            upstream_step="CODING",
            confidence=0.85,
            payer_rule="The payer requires the appropriate modifier when billing this service under the claim context.",
            explanation="The denial points to a coding issue where the submitted service was not payable as coded. The coding step likely missed a required modifier or related code detail.",
            recommended_fix="Review the payer policy and add the required modifier before corrected claim submission.",
        )

    if denial_code == "CO-97":
        return ClassificationResult(
            root_cause="OTHER",
            upstream_step="PAYER_POLICY",
            confidence=0.85,
            payer_rule="The payer bundles this service into payment for another related service.",
            explanation="The 835 adjustment indicates the service allowance is included in another adjudicated service. This is driven by payer bundling policy rather than a missing registration or scheduling step.",
            recommended_fix="Review the related paid service and appeal only if the service should not have been bundled under the payer policy.",
        )

    if denial_code in {"CO-45", "CO-131"} or "negotiated discount" in denial_text:
        return ClassificationResult(
            root_cause="OTHER",
            upstream_step="PAYER_POLICY",
            confidence=0.80,
            payer_rule="The payer reduced the submitted charge according to its fee schedule or contracted rate.",
            explanation="The 835 adjustment reflects a contractual or negotiated discount on the service line. This is usually a payer contract rule rather than a preventable claim workflow failure.",
            recommended_fix="Validate the expected allowed amount against the payer contract and flag only underpayments for follow-up.",
        )

    if denial_code == "CO-204" or "not covered" in denial_text:
        return ClassificationResult(
            root_cause="MEDICAL_NECESSITY",
            upstream_step="PAYER_POLICY",
            confidence=0.80,
            payer_rule="The payer does not cover this service under the patient's benefit plan unless policy criteria are met.",
            explanation="The denial indicates the billed service is not covered under the current benefit plan. The payer policy check should be reviewed before claim submission or appeal.",
            recommended_fix="Confirm benefit coverage and submit an appeal with supporting documentation if the service meets policy criteria.",
        )

    if "duplicate" in denial_text:
        return ClassificationResult(
            root_cause="DUPLICATE_CLAIM",
            upstream_step="BILLING",
            confidence=0.95,
            payer_rule="The payer rejects claims that duplicate a previously submitted or paid claim.",
            explanation="The denial text indicates the payer has already received or adjudicated this claim. The billing workflow likely resubmitted the claim without confirming prior claim status.",
            recommended_fix="Check payer claim history and void, correct, or appeal only if the duplicate determination is incorrect.",
        )

    if "timely" in denial_text:
        return ClassificationResult(
            root_cause="TIMELY_FILING",
            upstream_step="BILLING",
            confidence=0.90,
            payer_rule="The payer requires claims to be submitted within its timely filing deadline.",
            explanation="The denial indicates the claim was received after the payer's filing window. The billing step failed to submit or correct the claim before the deadline.",
            recommended_fix="Appeal with proof of timely submission if available and monitor aging queues for this payer deadline.",
        )

    return ClassificationResult(
        root_cause="CODING_ERROR",
        upstream_step="CODING",
        confidence=0.70,
        payer_rule="The payer requires submitted diagnosis and procedure codes to support the billed service.",
        explanation="The denial does not match a more specific automated category, so a coding mismatch is the most likely root cause. The coding workflow should review whether the CPT and diagnosis combination supports payment.",
        recommended_fix="Review the medical record and payer policy, then submit a corrected claim with supported CPT, ICD-10, and modifier details.",
    )
