import json
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "denials.json"


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


def save_denial(denial: dict) -> None:
    records = load_all()
    records.append(denial)
    DATA_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")


def get_by_claim_id(claim_id: str) -> dict | None:
    for record in load_all():
        if record.get("claim_id") == claim_id:
            return record

    return None


def get_all_processed() -> list:
    return sorted(
        load_all(),
        key=lambda record: record.get("processed_at", ""),
        reverse=True,
    )


def delete_all() -> None:
    _ensure_data_file()
    DATA_FILE.write_text("[]", encoding="utf-8")


def get_stats() -> dict:
    records = load_all()

    matched = [r for r in records if r.get("matched_claim_id") is not None]
    unmatched = [r for r in records if r.get("matched_claim_id") is None]
    total = len(records)

    stats: dict[str, Any] = {
        "total_denials": total,
        "total_revenue_at_risk": sum(
            record.get("billed_amount", 0.0) for record in records
        ),
        "matched_denials": len(matched),
        "unmatched_denials": len(unmatched),
        "match_rate": round(len(matched) / total, 4) if total else 0.0,
        "by_root_cause": {},
        "by_payer": {},
        "by_upstream_step": {},
        "by_department": {},
    }

    for record in records:
        classification = record.get("classification", {})
        root_cause = classification.get("root_cause", "UNKNOWN")
        upstream_step = classification.get("upstream_step", "UNKNOWN")
        payer = record.get("payer", "UNKNOWN")
        department = record.get("department", "UNKNOWN")

        stats["by_root_cause"][root_cause] = (
            stats["by_root_cause"].get(root_cause, 0) + 1
        )
        stats["by_payer"][payer] = stats["by_payer"].get(payer, 0) + 1
        stats["by_upstream_step"][upstream_step] = (
            stats["by_upstream_step"].get(upstream_step, 0) + 1
        )
        stats["by_department"][department] = (
            stats["by_department"].get(department, 0) + 1
        )

    return stats
