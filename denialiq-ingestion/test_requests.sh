#!/usr/bin/env bash

BASE_URL="http://localhost:8000"

echo
echo "1. Health check"
# Tests service info and confirms the API is running.
curl -s "${BASE_URL}/" | python3 -m json.tool

echo
echo "2. Ingest UnitedHealth prior auth denial"
# Tests POST /ingest in mock mode for a prior authorization denial.
curl -s -X POST "${BASE_URL}/ingest?use_mock=true" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2026-0847",
    "patient_name": "Mary Johnson",
    "date_of_service": "2026-04-10",
    "payer": "UnitedHealth",
    "plan_type": "Choice Plus",
    "procedure_code": "73721",
    "billed_amount": 2500.00,
    "denial_reason_code": "CO-197",
    "denial_reason_text": "Prior authorization required and not obtained",
    "department": "Radiology",
    "provider_name": "Dr. Raj Patel"
  }' | python3 -m json.tool

echo
echo "3. Ingest Aetna coding error denial"
# Tests POST /ingest in mock mode for an Aetna coding-related denial.
curl -s -X POST "${BASE_URL}/ingest?use_mock=true" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2026-0901",
    "patient_name": "James Smith",
    "date_of_service": "2026-04-15",
    "payer": "Aetna",
    "procedure_code": "99213",
    "billed_amount": 180.00,
    "denial_reason_code": "CO-4",
    "denial_reason_text": "Service, equipment or drug is not covered",
    "department": "Primary Care",
    "provider_name": "Dr. Sarah Chen"
  }' | python3 -m json.tool

echo
echo "4. Ingest BCBS eligibility denial"
# Tests POST /ingest in mock mode for a BCBS eligibility denial.
curl -s -X POST "${BASE_URL}/ingest?use_mock=true" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2026-0923",
    "patient_name": "Linda Garcia",
    "date_of_service": "2026-03-22",
    "payer": "BCBS",
    "procedure_code": "93000",
    "billed_amount": 320.00,
    "denial_reason_code": "PR-1",
    "denial_reason_text": "Patient not eligible on date of service",
    "department": "Cardiology",
    "provider_name": "Dr. Michael Torres"
  }' | python3 -m json.tool

echo
echo "5. Get all denials"
# Tests GET /denials and returns the stored processed denials.
curl -s "${BASE_URL}/denials" | python3 -m json.tool

echo
echo "6. Filter by payer"
# Tests GET /denials filtered by payer name.
curl -s "${BASE_URL}/denials?payer=UnitedHealth" | python3 -m json.tool

echo
echo "7. Filter by root cause"
# Tests GET /denials filtered by classification root cause.
curl -s "${BASE_URL}/denials?root_cause=MISSING_PRIOR_AUTH" | python3 -m json.tool

echo
echo "8. Get single denial"
# Tests GET /denials/{claim_id} for a known claim ID.
curl -s "${BASE_URL}/denials/CLM-2026-0847" | python3 -m json.tool

echo
echo "9. Get stats"
# Tests GET /stats for aggregate denial metrics.
curl -s "${BASE_URL}/stats" | python3 -m json.tool

echo
echo "10. Test validation error"
# Tests POST /ingest validation with a missing claim_id.
curl -s -X POST "${BASE_URL}/ingest?use_mock=true" \
  -H "Content-Type: application/json" \
  -d '{
    "payer": "Aetna",
    "denial_reason_code": "CO-197",
    "denial_reason_text": "Prior auth required"
  }' | python3 -m json.tool

echo
echo "11. List real 835 mock files"
# Tests GET /835/mock-files and returns available X221 835 EDI examples.
curl -s "${BASE_URL}/835/mock-files" | python3 -m json.tool

echo
echo "12. Get parsed 835 example"
# Tests GET /835/parsed-example using scripts/output_claims_2.json.
curl -s "${BASE_URL}/835/parsed-example" | python3 -m json.tool

echo
echo "13. Ingest parsed 835 example"
# Tests POST /ingest/835 in mock mode using scripts/output_claims_2.json.
curl -s -X POST "${BASE_URL}/ingest/835?use_mock=true" | python3 -m json.tool

echo
echo "14. Filter imported 835 records by payer"
# Tests GET /denials after importing the Delta Dental 835 example.
curl -s "${BASE_URL}/denials?payer=DELTA%20DENTAL%20OF%20ABC" | python3 -m json.tool

echo
echo "15. Reset all data"
# Tests DELETE /reset and clears all stored denial records.
curl -s -X DELETE "${BASE_URL}/reset" | python3 -m json.tool
