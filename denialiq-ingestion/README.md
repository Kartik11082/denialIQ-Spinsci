# DenialIQ Ingestion

DenialIQ Ingestion is a FastAPI service that accepts denied healthcare claims, normalizes them, classifies the denial root cause, and stores the processed result in a local JSON file.

## What It Does

At a high level, this service is the entry point for DenialIQ.
It turns raw denial data into clean, structured denial records that other services can analyze later.

The service supports two input types:

1. Manual denial JSON sent directly to the API.
2. Parsed 835 claim payment advice JSON generated from real mock EDI files.

After ingestion, every denial goes through the same flow:

```text
Input denial
  -> validate required fields
  -> normalize payer, procedure, department, denial code, and timestamps
  -> classify root cause
  -> save processed denial to data/denials.json
```

## Why This Exists

Hospitals receive denials from payers in different formats.
Some denials are entered manually, while many come from 835 EDI remittance files.

This API creates one consistent internal format:

```text
Raw payer denial data -> ProcessedDenial
```

That makes downstream services simpler.
For example, a future Pattern Detection Service can read `data/denials.json` and find repeated issues like prior authorization misses, payer policy changes, coding errors, or eligibility problems.

## Project Structure

```text
app/
  main.py          FastAPI routes
  models.py        Pydantic request and response models
  parser.py        Normalizes manual denial input
  classifier.py    Mock classifier and AWS Bedrock classifier
  storage.py       Local JSON file storage
  edi835.py        Converts parsed 835 JSON into denial records

data/
  denials.json     Stored processed denials
  mock/            Real mock 835 EDI examples

scripts/
  ediParser.py     Converts .edi files into JSON
  output/          JSON output for every parsed 835 file
```

## How The API Works

### Manual Ingestion

Use this when you already have denial data in JSON form.

Endpoint:

```text
POST /ingest?use_mock=true
```

Example input:

```json
{
  "claim_id": "CLM-2026-0847",
  "patient_name": "Mary Johnson",
  "date_of_service": "2026-04-10",
  "payer": "UnitedHealth",
  "plan_type": "Choice Plus",
  "procedure_code": "73721",
  "billed_amount": 2500.0,
  "denial_reason_code": "CO-197",
  "denial_reason_text": "Prior authorization required and not obtained",
  "department": "Radiology",
  "provider_name": "Dr. Raj Patel"
}
```

What happens internally:

```text
RawDenialInput
  -> parser.validate_denial()
  -> parser.parse_denial()
  -> classifier.classify_mock() or classifier.classify_denial()
  -> storage.save_denial()
```

Example output:

```json
{
  "success": true,
  "message": "Denial ingested and classified",
  "data": {
    "claim_id": "CLM-2026-0847",
    "patient_name": "Mary Johnson",
    "date_of_service": "2026-04-10",
    "payer": "UnitedHealth",
    "procedure_code": "73721",
    "procedure_name": "MRI Knee Joint",
    "billed_amount": 2500.0,
    "denial_reason_code": "CO-197",
    "denial_reason_text": "Prior authorization required and not obtained",
    "department": "Radiology",
    "classification": {
      "root_cause": "MISSING_PRIOR_AUTH",
      "upstream_step": "SCHEDULING",
      "confidence": 0.95,
      "payer_rule": "The payer requires prior authorization before this service is performed.",
      "explanation": "The denial indicates authorization was required before the date of service.",
      "recommended_fix": "Submit an appeal with medical records and implement a scheduling prior-auth check."
    },
    "processed_at": "2026-05-31T15:00:00.000000",
    "status": "CLASSIFIED"
  }
}
```

## 835 EDI Ingestion

835 files are payer remittance files.
They contain claim payment information and denial or adjustment reasons.

The mock EDI files live here:

```text
data/mock/005010X221 Health Care Claim Payment Advice
```

First, convert the `.edi` files into JSON:

```bash
python scripts/ediParser.py
```

This creates one JSON file per EDI file:

```text
scripts/output/X221-claim-adjustment-reason-code-45.json
scripts/output/X221-claim-specific-negotiated-discount.json
...
```

Then ingest a parsed 835 JSON file:

```text
POST /ingest/835?use_mock=true
```

By default, the API reads:

```text
scripts/output/X221-claim-specific-negotiated-discount.json
```

You can pass another parsed file:

```text
POST /ingest/835?use_mock=true&parsed_file=scripts/output/X221-claim-specific-negotiated-discount.json
```

What happens internally:

```text
Parsed 835 JSON
  -> app.edi835.raw_denials_from_parsed_835()
  -> one RawDenialInput per CAS adjustment
  -> parser.parse_denial()
  -> classifier
  -> storage.save_denial()
```

Example: one 835 claim can contain multiple service lines.
Each service-line CAS adjustment becomes its own DenialIQ denial record.

For example:

```json
{
  "procedure_code": "AD|D0120",
  "charge_amount": "46",
  "paid_amount": "25",
  "adjustments": [
    {
      "group": "CO",
      "reason_code": "131",
      "amount": "21"
    }
  ]
}
```

Becomes a denial with:

```json
{
  "denial_reason_code": "CO-131",
  "denial_reason_text": "Claim specific negotiated discount",
  "billed_amount": 21.0,
  "department": "Dental"
}
```

## Classification Modes

Mock mode does not require AWS:

```text
POST /ingest?use_mock=true
POST /ingest/835?use_mock=true
```

Bedrock mode uses AWS Bedrock Claude:

```text
POST /ingest?use_mock=false
POST /ingest/835?use_mock=false
```

To use Bedrock mode, add credentials to `.env`:

```text
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001
```

## Run The API

Install dependencies with UV, then start the server:

```bash
uv sync
./run.sh
```

The API runs here:

```text
http://localhost:8000
```

Interactive docs:

```text
http://localhost:8000/docs
```

## Endpoints

| Method   | Path                  | What It Does                                   | Params                         |
| -------- | --------------------- | ---------------------------------------------- | ------------------------------ |
| `GET`    | `/`                   | Health check and service info                  | None                           |
| `POST`   | `/ingest`             | Ingest one manual denial JSON object           | `use_mock=true/false`          |
| `POST`   | `/ingest/835`         | Ingest parsed 835 JSON and save denial records | `use_mock`, `parsed_file`      |
| `GET`    | `/835/mock-files`     | List available mock 835 EDI files              | None                           |
| `GET`    | `/835/parsed-example` | Return parsed 835 JSON content                 | `parsed_file`                  |
| `GET`    | `/denials`            | Return stored processed denials                | `payer`, `root_cause`, `limit` |
| `GET`    | `/denials/{claim_id}` | Return one denial by claim ID                  | `claim_id`                     |
| `GET`    | `/stats`              | Return denial counts and grouped metrics       | None                           |
| `DELETE` | `/reset`              | Delete all stored denials                      | None                           |

## Simple Curl Examples

Health check:

```bash
curl -s http://localhost:8000/ | python3 -m json.tool
```

Ingest manual denial:

```bash
curl -s -X POST "http://localhost:8000/ingest?use_mock=true" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2026-0847",
    "patient_name": "Mary Johnson",
    "date_of_service": "2026-04-10",
    "payer": "UnitedHealth",
    "procedure_code": "73721",
    "billed_amount": 2500.00,
    "denial_reason_code": "CO-197",
    "denial_reason_text": "Prior authorization required and not obtained"
  }' | python3 -m json.tool
```

Ingest parsed 835 file:

```bash
curl -s -X POST "http://localhost:8000/ingest/835?use_mock=true&parsed_file=scripts/output/X221-claim-specific-negotiated-discount.json" \
  | python3 -m json.tool
```

Get all denials:

```bash
curl -s http://localhost:8000/denials | python3 -m json.tool
```

Get stats:

```bash
curl -s http://localhost:8000/stats | python3 -m json.tool
```

Reset data:

```bash
curl -s -X DELETE http://localhost:8000/reset | python3 -m json.tool
```

## Test Script

Run all manual API checks:

```bash
./test_requests.sh
```

## MVP End-To-End Plan

The MVP goal is simple:

```text
Take denial data in
  -> normalize it
  -> classify it
  -> find repeated denial patterns
  -> show what to fix first
```

The MVP does not need a full database, user accounts, queues, or a complex frontend.
It should work end to end with local JSON files and clear API endpoints.

### MVP Flow

```text
837/835 parsers
  -> parsed JSON
  -> ingestion API
  -> matched ProcessedDenial records
  -> data/denials.json
  -> pattern detection
  -> analytics summary
  -> appeal worklist
```

### MVP Components

| Component         | Purpose                                                     | Keep It Simple By                                              |
| ----------------- | ----------------------------------------------------------- | -------------------------------------------------------------- |
| Ingestion API     | Accept manual denial JSON and parsed 835 JSON               | Store normalized records in `data/denials.json`                |
| Matching          | Connect payer response data back to submitted claim context | Match by `claim_id`, `procedure_code`, payer, and service date |
| Classification    | Identify root cause and workflow step                       | Use mock mode first, Bedrock mode later                        |
| Pattern Detection | Find repeated denial problems                               | Group by payer, denial code, CPT, department, and root cause   |
| Appeal Worklist   | Identify denials worth reviewing                            | Use rule-based scoring first                                   |
| Exports           | Let users inspect results outside the API                   | Return CSV from local JSON data                                |
| Basic UI or Docs  | Make the MVP usable                                         | Start with Swagger docs and curl examples                      |

### MVP Data Files

Use local JSON files for the first version:

```text
data/denials.json       processed and classified denials
data/claims.json        optional matched 837 claim records
data/patterns.json      generated denial patterns
data/appeals.json       generated appeal candidates
```

The most important file is:

```text
data/denials.json
```

That is the handoff from ingestion to the rest of DenialIQ.

### Final Processed Denial Shape

Every downstream feature should use one consistent denial object.

Example:

```json
{
  "claim_id": "PATACCT-99213-1",
  "matched_claim_id": "PATACCT",
  "patient_name": "DOE JOHN",
  "payer": "ANY PLAN USA",
  "provider_name": "PROVIDER",
  "department": "Evaluation & Management",
  "date_of_service": "2019-01-01",
  "procedure_code": "99213",
  "procedure_name": "Office Visit - Established Patient",
  "diagnosis_code": "J01.90",
  "billed_amount": 150.0,
  "paid_amount": 80.0,
  "denial_amount": 70.0,
  "denial_reason_code": "CO-45",
  "denial_reason_text": "Charge exceeds fee schedule or contracted arrangement",
  "classification": {
    "root_cause": "OTHER",
    "upstream_step": "PAYER_POLICY",
    "confidence": 0.8,
    "payer_rule": "The payer reduced the submitted charge according to its fee schedule.",
    "explanation": "The payer adjusted the claim according to contract rules.",
    "recommended_fix": "Validate the allowed amount against the payer contract."
  },
  "processed_at": "2026-05-31T15:00:00",
  "status": "CLASSIFIED"
}
```

### Pattern Detection MVP

Pattern detection reads `data/denials.json` and groups repeated problems.

Start with these groupings:

```text
payer + denial_reason_code
payer + root_cause
payer + procedure_code
department + root_cause
provider_name + root_cause
procedure_code + denial_reason_code
```

Example pattern:

```json
{
  "pattern_id": "PATTERN-001",
  "title": "ANY PLAN USA CO-45 office visit adjustments",
  "payer": "ANY PLAN USA",
  "denial_reason_code": "CO-45",
  "procedure_code": "99213",
  "root_cause": "OTHER",
  "count": 12,
  "revenue_at_risk": 840.0,
  "recommendation": "Review payer contract fee schedule for CPT 99213."
}
```

### Appeal Worklist MVP

Not every denial should be appealed.
The MVP can use simple rules.

Example rules:

```text
CO-197 -> appeal candidate
CO-204 -> review for medical documentation
CO-45 -> contract validation, usually not appeal
CO-97 -> bundled service review, usually low priority
high denial amount -> higher priority
repeated pattern -> higher priority
```

Example appeal candidate:

```json
{
  "claim_id": "PATACCT-85003-2",
  "appealable": true,
  "priority": "HIGH",
  "reason": "High-dollar medical necessity denial with matched claim context.",
  "next_action": "Collect documentation and submit appeal."
}
```

### MVP API Endpoints To Add

The current ingestion endpoints are the base.
Add these simple endpoints next:

| Method  | Path                         | Purpose                                                   |
| ------- | ---------------------------- | --------------------------------------------------------- |
| `GET`   | `/analytics/summary`         | Total denials, revenue at risk, top payer, top root cause |
| `GET`   | `/analytics/patterns`        | Repeated denial patterns                                  |
| `GET`   | `/appeals/worklist`          | Denials that should be reviewed or appealed               |
| `PATCH` | `/denials/{claim_id}/status` | Update denial status                                      |
| `GET`   | `/export/denials.csv`        | Export processed denials                                  |
| `GET`   | `/export/patterns.csv`       | Export detected patterns                                  |
| `GET`   | `/export/appeals.csv`        | Export appeal worklist                                    |

### Denial Statuses

Keep the workflow small:

```text
CLASSIFIED
NEEDS_REVIEW
APPEAL_READY
APPEALED
RESOLVED
WRITTEN_OFF
```

### MVP Build Order

Build in this order:

```text
1. Freeze the ProcessedDenial schema
2. Keep ingestion writing clean records to data/denials.json
3. Add pattern detection from data/denials.json
4. Add /analytics/summary
5. Add /analytics/patterns
6. Add appeal candidate rules
7. Add /appeals/worklist
8. Add status updates for denials
9. Add CSV exports
10. Add a very small dashboard only after APIs work
```

### MVP Done Criteria

The MVP is complete when this works:

```text
1. Run parser on sample 835 files
2. Ingest parsed 835 JSON through the API
3. Store classified denials in data/denials.json
4. View all denials through /denials
5. View summary metrics through /analytics/summary
6. View repeated denial patterns through /analytics/patterns
7. View appeal candidates through /appeals/worklist
8. Export denials, patterns, and appeals as CSV
```

At that point the project works end to end as a simple denial intelligence MVP.

## Storage

This MVP does not use a database.
Processed denials are stored locally in:

```text
data/denials.json
```

That file is the handoff point for the next service.
