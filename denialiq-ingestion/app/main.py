from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Body, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app import claim_storage, classifier, edi835, edi837, insight_service, matcher, parser, storage
from app.models import APIResponse, ProcessedDenial, RawDenialInput


ENDPOINTS = [
    "/",
    "POST /ingest",
    "POST /ingest/837",
    "POST /ingest/835",
    "GET  /835/mock-files",
    "GET  /835/parsed-example",
    "GET  /claims",
    "GET  /claims/{claim_id}",
    "GET  /denials",
    "GET  /denials/{claim_id}",
    "GET  /stats",
    "DELETE /reset",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    print("DenialIQ Ingestion Service running on http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    print("Mock mode: set use_mock=false to use AWS Bedrock")
    yield


app = FastAPI(title="DenialIQ Ingestion Service", version="0.2.0", lifespan=lifespan)

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


def error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=APIResponse(success=False, message=message).model_dump(),
    )


def validation_error_message(error: ValidationError) -> str:
    first_error = error.errors()[0] if error.errors() else {}
    field = first_error.get("loc", ["input"])[-1]
    if first_error.get("type") == "missing":
        return f"{field} is required"
    return first_error.get("msg", "Invalid request")


def is_835_payload(payload: dict) -> bool:
    return isinstance(payload.get("claims"), list) and isinstance(
        payload.get("payment_info"),
        dict,
    )


def classify_parsed_denial(parsed: dict, use_mock: bool):
    return (
        classifier.classify_mock(parsed)
        if use_mock
        else classifier.classify_denial(parsed)
    )


# ---------------------------------------------------------------------------
# 835 ingestion (internal helper – used by two endpoints)
# ---------------------------------------------------------------------------


def _build_denial_record(
    raw: RawDenialInput,
    use_mock: bool,
    source_meta: dict,
) -> dict:
    """Parse, classify, match, and return a fully enriched denial record.

    The matcher is called here so that every 835 denial automatically pulls
    in diagnosis codes, provider, and patient context from the stored 837
    submitted claim when a match exists.
    """
    parsed = parser.parse_denial(raw)

    # Attempt to enrich from a stored 837 claim before classification so
    # that the classifier receives the richer context (diagnosis codes, etc.)
    match = matcher.find_matching_claim(
        denial_claim_id=raw.claim_id.split("-")[0],  # strip sequence suffix
        denial_procedure_code=raw.procedure_code,
    )
    parsed = matcher.enrich_denial_from_match(parsed, match)

    classification = classify_parsed_denial(parsed, use_mock)
    processed = ProcessedDenial(**{
        k: v for k, v in parsed.items() if k in ProcessedDenial.model_fields
    }, classification=classification)
    record = processed.model_dump()
    record.update({
        "matched_claim_id": parsed.get("matched_claim_id"),
        "diagnosis_codes": parsed.get("diagnosis_codes", []),
        "submitted_charge": parsed.get("submitted_charge"),
        "source": source_meta,
    })
    # Annotate with LLM insight — runs once at write time, stored on the record.
    insight_service.annotate_denial(record, use_mock=source_meta.get("use_mock", True))
    return record


def ingest_835_payload(
    parsed_835: dict,
    use_mock: bool,
    source_file: str,
) -> APIResponse | JSONResponse:
    raw_denials = edi835.raw_denials_from_parsed_835(parsed_835, source_file=source_file)

    if not raw_denials:
        return error_response("No claim adjustments found in parsed 835 payload")

    source_meta = {
        "format": "835",
        "source_file": source_file,
        "sender_id": parsed_835.get("sender_id"),
        "receiver_id": parsed_835.get("receiver_id"),
        "payment_info": parsed_835.get("payment_info", {}),
        "use_mock": use_mock,
    }

    processed_records = []
    for raw in raw_denials:
        record = _build_denial_record(raw, use_mock, source_meta)
        storage.save_denial(record)
        processed_records.append(record)

    matched_count = sum(1 for r in processed_records if r.get("matched_claim_id"))

    return APIResponse(
        success=True,
        message=(
            f"Ingested {len(processed_records)} denial adjustments from parsed 835 "
            f"({matched_count} matched to 837 claims)"
        ),
        data={
            "source_file": source_file,
            "count": len(processed_records),
            "matched": matched_count,
            "unmatched": len(processed_records) - matched_count,
            "records": processed_records,
        },
    )


# ---------------------------------------------------------------------------
# Exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    field = first_error.get("loc", ["input"])[-1]
    message = (
        f"{field} is required"
        if first_error.get("type") == "missing"
        else first_error.get("msg", "Invalid request")
    )
    return error_response(message)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def service_info() -> dict:
    return {
        "service": "DenialIQ Ingestion Service",
        "version": "0.2.0",
        "status": "running",
        "endpoints": ENDPOINTS,
    }


# -- Legacy manual ingest (kept for backwards compatibility) ----------------


@app.post("/ingest", response_model=APIResponse)
def ingest(payload: dict = Body(...), use_mock: bool = True) -> APIResponse | JSONResponse:
    """Ingest a single manual denial JSON or a full parsed 835 payload."""
    try:
        if is_835_payload(payload):
            return ingest_835_payload(
                payload,
                use_mock,
                source_file=payload.get("source_file", "request body"),
            )

        try:
            raw = RawDenialInput(**payload)
        except ValidationError as error:
            return error_response(validation_error_message(error))

        is_valid, error_message = parser.validate_denial(raw)
        if not is_valid:
            return error_response(error_message)

        source_meta = {"format": "manual", "source_file": "request body", "use_mock": use_mock}
        record = _build_denial_record(raw, use_mock, source_meta)
        storage.save_denial(record)

        return APIResponse(
            success=True,
            message="Denial ingested and classified",
            data=record,
        )
    except Exception as error:
        return APIResponse(success=False, message=str(error))


# -- 837 ingestion ----------------------------------------------------------


@app.post("/ingest/837", response_model=APIResponse)
def ingest_parsed_837(
    payload: dict = Body(...),
    source_file: str = "request body",
) -> APIResponse | JSONResponse:
    """Accept a parsed 837 JSON document and store submitted claims.

    The payload should be the output of a 837 EDI parser — a JSON object
    that contains a ``claims`` list.  Each claim is stored individually in
    ``data/claims.json`` keyed by ``claim_id``.

    Re-ingesting the same file is safe; existing records are replaced.
    """
    try:
        claims = edi837.submitted_claims_from_parsed_837(payload, source_file=source_file)

        if not claims:
            return error_response("No claims found in parsed 837 payload")

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
        return error_response(str(error))


# -- 835 ingestion ----------------------------------------------------------


@app.post("/ingest/835", response_model=APIResponse)
def ingest_parsed_835(
    payload: dict | None = Body(default=None),
    use_mock: bool = True,
    parsed_file: str = "scripts/output/X221-claim-specific-negotiated-discount.json",
) -> APIResponse | JSONResponse:
    """Ingest a parsed 835 JSON document, classify denials, and match to 837 claims.

    Pass a JSON body to use inline data, or supply ``parsed_file`` to read
    from a pre-parsed file in ``scripts/output/``.
    """
    try:
        if payload is not None:
            return ingest_835_payload(
                payload,
                use_mock,
                source_file=payload.get("source_file", "request body"),
            )

        file_path = edi835.resolve_project_path(parsed_file)
        parsed_835 = edi835.load_parsed_835(parsed_file)
        return ingest_835_payload(
            parsed_835,
            use_mock,
            source_file=str(file_path.relative_to(edi835.PROJECT_ROOT)),
        )
    except Exception as error:
        return error_response(str(error))


# -- 835 utilities ----------------------------------------------------------


@app.get("/835/mock-files", response_model=APIResponse)
def list_835_mock_files() -> APIResponse:
    return APIResponse(
        success=True,
        message="835 mock files retrieved",
        data=edi835.list_mock_835_files(),
    )


@app.get("/835/parsed-example", response_model=APIResponse)
def get_835_parsed_example(
    parsed_file: str = "scripts/output/X221-claim-specific-negotiated-discount.json",
) -> APIResponse | JSONResponse:
    try:
        file_path = edi835.resolve_project_path(parsed_file)
        return APIResponse(
            success=True,
            message="Parsed 835 example retrieved",
            data={
                "source_file": str(file_path.relative_to(edi835.PROJECT_ROOT)),
                "content": edi835.load_parsed_835(parsed_file),
            },
        )
    except Exception as error:
        return JSONResponse(
            status_code=400,
            content=APIResponse(success=False, message=str(error)).model_dump(),
        )


# -- Claims (837) -----------------------------------------------------------


@app.get("/claims", response_model=APIResponse)
def list_claims(
    payer: str | None = None,
    limit: int = Query(default=50, ge=1),
) -> APIResponse:
    """Return stored 837 submitted claims, optionally filtered by payer."""
    records = claim_storage.get_all()

    if payer:
        records = [
            r for r in records if r.get("payer", "").lower() == payer.lower()
        ]

    return APIResponse(
        success=True,
        message="Submitted claims retrieved",
        data=records[:limit],
    )


@app.get("/claims/{claim_id}", response_model=APIResponse)
def get_claim(claim_id: str, use_mock: bool = True) -> APIResponse | JSONResponse:
    """Return one submitted claim with all matched 835 denials and an LLM summary."""
    claim = claim_storage.get_by_claim_id(claim_id)
    if claim is None:
        return JSONResponse(
            status_code=404,
            content=APIResponse(success=False, message="Claim not found").model_dump(),
        )

    matched_denials = [
        r for r in storage.load_all()
        if r.get("matched_claim_id") == claim_id
    ]

    summary = insight_service.summarize_claim(claim, matched_denials, use_mock=use_mock)

    return APIResponse(
        success=True,
        message="Claim retrieved",
        data={
            "summary": summary,
            "submitted_claim": claim,
            "matched_denials": matched_denials,
        },
    )


# -- Denials (835) ----------------------------------------------------------


@app.get("/denials", response_model=APIResponse)
def list_denials(
    payer: str | None = None,
    root_cause: str | None = None,
    matched: bool | None = None,
    limit: int = Query(default=50, ge=1),
) -> APIResponse:
    """Return processed 835 denial records.

    Optional filters:
    - ``payer``: exact match (case-insensitive)
    - ``root_cause``: exact match (case-insensitive)
    - ``matched``: ``true`` for denials with a matched 837 claim, ``false``
      for unmatched
    """
    records = storage.get_all_processed()

    if payer:
        records = [
            r for r in records if r.get("payer", "").lower() == payer.lower()
        ]

    if root_cause:
        records = [
            r for r in records
            if r.get("classification", {}).get("root_cause", "").lower()
            == root_cause.lower()
        ]

    if matched is True:
        records = [r for r in records if r.get("matched_claim_id") is not None]
    elif matched is False:
        records = [r for r in records if r.get("matched_claim_id") is None]

    return APIResponse(
        success=True,
        message="Denials retrieved",
        data=records[:limit],
    )


@app.get("/denials/{claim_id}", response_model=APIResponse)
def get_denial(claim_id: str) -> APIResponse | JSONResponse:
    record = storage.get_by_claim_id(claim_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content=APIResponse(success=False, message="Denial not found").model_dump(),
        )
    return APIResponse(success=True, message="Denial retrieved", data=record)


# -- Stats ------------------------------------------------------------------


@app.get("/stats", response_model=APIResponse)
def get_stats(use_mock: bool = True) -> APIResponse:
    denial_stats = storage.get_stats()
    claim_stats = {
        "total_claims": len(claim_storage.load_all()),
    }
    combined = {**claim_stats, **denial_stats}
    combined["narrative"] = insight_service.summarize_stats(combined, use_mock=use_mock)
    return APIResponse(
        success=True,
        message="Stats retrieved",
        data=combined,
    )


# -- Reset ------------------------------------------------------------------


@app.delete("/reset", response_model=APIResponse)
def reset(claims: bool = False) -> APIResponse:
    """Delete all denial records.  Pass ``claims=true`` to also wipe 837 claims."""
    storage.delete_all()
    message = "All denial records deleted"
    if claims:
        claim_storage.delete_all()
        message += " and all submitted claims deleted"
    return APIResponse(success=True, message=message)
