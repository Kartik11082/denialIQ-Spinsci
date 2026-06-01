import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "claims.json"


def _ensure_data_file() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_all() -> list:
    _ensure_data_file()
    content = DATA_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return json.loads(content)


def save_claim(claim: dict) -> None:
    """Append a submitted claim record to claims.json.

    If a record with the same ``claim_id`` already exists it is replaced so
    that re-ingesting the same 837 file is idempotent.
    """
    records = load_all()
    claim_id = claim.get("claim_id")
    updated = False

    for index, existing in enumerate(records):
        if existing.get("claim_id") == claim_id:
            records[index] = claim
            updated = True
            break

    if not updated:
        records.append(claim)

    DATA_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")


def get_by_claim_id(claim_id: str) -> dict | None:
    for record in load_all():
        if record.get("claim_id") == claim_id:
            return record
    return None


def get_all() -> list:
    return sorted(
        load_all(),
        key=lambda record: record.get("ingested_at", ""),
        reverse=True,
    )


def delete_all() -> None:
    _ensure_data_file()
    DATA_FILE.write_text("[]", encoding="utf-8")
