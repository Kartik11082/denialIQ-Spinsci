"""main.py — FastAPI application for the DenialIQ ingestion service.

This is the API layer.  It wires together the processing pipeline:

    POST /ingest/837  →  edi837.py  →  claim_storage.py  →  data/claims.json
    POST /ingest/835  →  edi835.py  →  parser.py  →  classifier.py  →  matcher.py  →  storage.py  →  data/denials.json
    POST /ingest      →  (manual denial — same pipeline as 835 but for one record)

Read endpoints return stored data with no processing:

    GET /claims, /claims/{id}, /denials, /denials/{id}, /stats
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Body, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app import claim_storage, classifier, edi835, edi837, matcher, parser, storage
from app.models import APIResponse, ProcessedDenial, RawDenialInput

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    print("DenialIQ Ingestion Service running on http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    yield


app = FastAPI(title="DenialIQ Ingestion Service", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _error(message: str, status_code: int = 400) -> JSONResponse:
    """Return a standard error response."""
    return JSONResponse(
        status_code=status_code,
        content=APIResponse(success=False, message=message).model_dump(),
    )


def _validation_message(error: ValidationError) -> str:
    """Extract a human-readable message from a Pydantic validation error."""
    first = error.errors()[0] if error.errors() else {}
    field = first.get("loc", ["input"])[-1]
    if first.get("type") == "missing":
        return f"{field} is required"
    return first.get("msg", "Invalid request")


def _is_835_shaped(payload: dict) -> bool:
    """Check if a payload looks like a parsed 835 (has claims + payment_info)."""
    return isinstance(payload.get("claims"), list) and isinstance(
        payload.get("payment_info"), dict
    )


# ---------------------------------------------------------------------------
# Core processing pipeline
# ---------------------------------------------------------------------------


def _build_denial_record(raw: RawDenialInput, source_meta: dict) -> dict:
    """Process a single denial through the full pipeline.

    Steps:
        1. Normalise fields (parser)
        2. Match against stored 837 claims (matcher)
        3. Classify root cause (classifier)
        4. Build the final record
    """
    # Step 1: normalise the raw input
    parsed = parser.parse_denial(raw)

    # Step 2: try to match to a stored 837 claim by claim_id + procedure_code.
    #   The raw claim_id from 835 has a sequence suffix (e.g. "PATACCT-99213-1")
    #   so we split on "-" to get the original claim_id for matching.
    original_claim_id = raw.claim_id.split("-")[0]
    match = matcher.find_matching_claim(original_claim_id, raw.procedure_code)
    parsed = matcher.enrich_denial_from_match(parsed, match)

    # Step 3: classify the root cause
    classification = classifier.classify(parsed)

    # Step 4: assemble the final record
    processed = ProcessedDenial(
        **{k: v for k, v in parsed.items() if k in ProcessedDenial.model_fields},
        classification=classification,
    )
    record = processed.model_dump()

    # Add matcher results and source metadata
    record["matched_claim_id"] = parsed.get("matched_claim_id")
    record["diagnosis_codes"] = parsed.get("diagnosis_codes", [])
    record["submitted_charge"] = parsed.get("submitted_charge")
    record["source"] = source_meta

    return record


def _ingest_835(parsed_835: dict, source_file: str) -> APIResponse | JSONResponse:
    """Process all CAS adjustments from a parsed 835 into denial records.

    Each service-line adjustment becomes its own denial record.  The matcher
    tries to link each one back to a stored 837 submitted claim.
    """
    raw_denials = edi835.raw_denials_from_parsed_835(
        parsed_835, source_file=source_file
    )
    if not raw_denials:
        return _error("No claim adjustments found in parsed 835 payload")

    source_meta = {
        "format": "835",
        "source_file": source_file,
        "sender_id": parsed_835.get("sender_id"),
        "receiver_id": parsed_835.get("receiver_id"),
        "payment_info": parsed_835.get("payment_info", {}),
    }

    records = []
    for raw in raw_denials:
        record = _build_denial_record(raw, source_meta)
        storage.save_denial(record)
        records.append(record)

    matched = sum(1 for r in records if r.get("matched_claim_id"))

    return APIResponse(
        success=True,
        message=f"Ingested {len(records)} denials from 835 ({matched} matched to 837 claims)",
        data={
            "source_file": source_file,
            "count": len(records),
            "matched": matched,
            "unmatched": len(records) - matched,
            "records": records,
        },
    )


# ---------------------------------------------------------------------------
# Exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request, exc: RequestValidationError
) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    field = first.get("loc", ["input"])[-1]
    msg = (
        f"{field} is required"
        if first.get("type") == "missing"
        else first.get("msg", "Invalid request")
    )
    return _error(msg)


# ---------------------------------------------------------------------------
# Routes: health check
# ---------------------------------------------------------------------------


@app.get("/")
def service_info() -> dict:
    return {
        "service": "DenialIQ Ingestion Service",
        "version": "0.3.0",
        "status": "running",
    }


# ---------------------------------------------------------------------------
# Routes: ingestion
# ---------------------------------------------------------------------------


@app.post("/ingest", response_model=APIResponse)
def ingest(payload: dict = Body(...)) -> APIResponse | JSONResponse:
    """Ingest a single manual denial or a full parsed 835 payload.

    If the payload has ``claims`` and ``payment_info`` keys it is treated
    as an 835.  Otherwise it is treated as a single manual denial.
    """
    try:
        # Auto-detect 835 payloads
        if _is_835_shaped(payload):
            return _ingest_835(
                payload, source_file=payload.get("source_file", "request body")
            )

        # Single manual denial
        try:
            raw = RawDenialInput(**payload)
        except ValidationError as error:
            return _error(_validation_message(error))

        is_valid, error_message = parser.validate_denial(raw)
        if not is_valid:
            return _error(error_message)

        record = _build_denial_record(
            raw, {"format": "manual", "source_file": "request body"}
        )
        storage.save_denial(record)

        return APIResponse(
            success=True, message="Denial ingested and classified", data=record
        )
    except Exception as error:
        return APIResponse(success=False, message=str(error))


@app.post("/ingest/837", response_model=APIResponse)
def ingest_837(
    payload: dict = Body(...),
    source_file: str = "request body",
) -> APIResponse | JSONResponse:
    """Ingest parsed 837 JSON and store submitted claims.

    Each claim in the ``claims`` list is stored in ``data/claims.json``.
    Re-ingesting the same file replaces existing records (safe to re-run).
    """
    try:
        claims = edi837.submitted_claims_from_parsed_837(
            payload, source_file=source_file
        )
        if not claims:
            return _error("No claims found in parsed 837 payload")

        for claim in claims:
            claim_storage.save_claim(claim)

        return APIResponse(
            success=True,
            message=f"Stored {len(claims)} submitted claim(s) from 837",
            data={
                "source_file": source_file,
                "count": len(claims),
                "claim_ids": [c["claim_id"] for c in claims],
            },
        )
    except Exception as error:
        return _error(str(error))


@app.post("/ingest/835", response_model=APIResponse)
def ingest_835(
    payload: dict | None = Body(default=None),
    parsed_file: str = "scripts/835_output/X221-claim-specific-negotiated-discount.json",
) -> APIResponse | JSONResponse:
    """Ingest parsed 835 JSON, classify denials, and match to 837 claims.

    Either POST a JSON body inline, or pass ``parsed_file`` to read from
    a pre-parsed file on disk.
    """
    try:
        if payload is not None:
            return _ingest_835(
                payload, source_file=payload.get("source_file", "request body")
            )

        file_path = edi835.resolve_project_path(parsed_file)
        parsed_835 = edi835.load_parsed_835(parsed_file)
        return _ingest_835(
            parsed_835, source_file=str(file_path.relative_to(edi835.PROJECT_ROOT))
        )
    except Exception as error:
        return _error(str(error))


# ---------------------------------------------------------------------------
# Routes: read claims (837)
# ---------------------------------------------------------------------------


@app.get("/claims", response_model=APIResponse)
def list_claims(
    payer: str | None = None,
    limit: int = Query(default=50, ge=1),
) -> APIResponse:
    """Return stored 837 submitted claims, optionally filtered by payer."""
    records = claim_storage.get_all()

    if payer:
        records = [r for r in records if r.get("payer", "").lower() == payer.lower()]

    return APIResponse(
        success=True, message="Submitted claims retrieved", data=records[:limit]
    )


@app.get("/claims/{claim_id}", response_model=APIResponse)
def get_claim(claim_id: str) -> APIResponse | JSONResponse:
    """Return one submitted claim and all matched 835 denials."""
    claim = claim_storage.get_by_claim_id(claim_id)
    if claim is None:
        return JSONResponse(
            status_code=404,
            content=APIResponse(success=False, message="Claim not found").model_dump(),
        )

    # Find all denials that were matched back to this claim
    matched_denials = [
        r for r in storage.load_all() if r.get("matched_claim_id") == claim_id
    ]

    return APIResponse(
        success=True,
        message="Claim retrieved",
        data={
            "submitted_claim": claim,
            "matched_denials": matched_denials,
        },
    )


# ---------------------------------------------------------------------------
# Routes: read denials (835)
# ---------------------------------------------------------------------------


@app.get("/denials", response_model=APIResponse)
def list_denials(
    payer: str | None = None,
    root_cause: str | None = None,
    matched: bool | None = None,
    limit: int = Query(default=50, ge=1),
) -> APIResponse:
    """Return processed denial records with optional filters.

    Filters (all case-insensitive):
        - payer: exact payer name match
        - root_cause: e.g. MISSING_PRIOR_AUTH, CODING_ERROR
        - matched: true = has matched 837 claim, false = unmatched
    """
    records = storage.get_all_processed()

    if payer:
        records = [r for r in records if r.get("payer", "").lower() == payer.lower()]

    if root_cause:
        records = [
            r
            for r in records
            if r.get("classification", {}).get("root_cause", "").lower()
            == root_cause.lower()
        ]

    if matched is True:
        records = [r for r in records if r.get("matched_claim_id") is not None]
    elif matched is False:
        records = [r for r in records if r.get("matched_claim_id") is None]

    return APIResponse(success=True, message="Denials retrieved", data=records[:limit])


@app.get("/denials/{claim_id}", response_model=APIResponse)
def get_denial(claim_id: str) -> APIResponse | JSONResponse:
    """Return a single denial record by its claim ID."""
    record = storage.get_by_claim_id(claim_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content=APIResponse(success=False, message="Denial not found").model_dump(),
        )
    return APIResponse(success=True, message="Denial retrieved", data=record)


# ---------------------------------------------------------------------------
# Routes: stats
# ---------------------------------------------------------------------------


@app.get("/stats", response_model=APIResponse)
def get_stats() -> APIResponse:
    """Return aggregate statistics across all claims and denials."""
    denial_stats = storage.get_stats()
    denial_stats["total_claims"] = len(claim_storage.load_all())
    return APIResponse(success=True, message="Stats retrieved", data=denial_stats)


# ---------------------------------------------------------------------------
# Routes: reset
# ---------------------------------------------------------------------------


@app.delete("/reset", response_model=APIResponse)
def reset(claims: bool = False) -> APIResponse:
    """Delete all denial records.  Pass ``claims=true`` to also wipe 837 claims."""
    storage.delete_all()
    message = "All denial records deleted"
    if claims:
        claim_storage.delete_all()
        message += " and all submitted claims deleted"
    return APIResponse(success=True, message=message)
