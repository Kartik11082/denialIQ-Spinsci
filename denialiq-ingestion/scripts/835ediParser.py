import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FOLDER = (
    PROJECT_ROOT / "data" / "mock" / "005010X222 Health Care Claim Professional (837)"
)
OUTPUT_FOLDER = PROJECT_ROOT / "scripts" / "837_output"


def get_value(elements, index, default=""):
    return elements[index].strip() if index < len(elements) else default


def get_person_name(elements):
    first_name = get_value(elements, 4)
    last_name = get_value(elements, 3)
    return " ".join(part for part in [last_name, first_name] if part)


def get_adjustments(elements):
    group_code = get_value(elements, 1)
    adjustments = []

    for index in range(2, len(elements), 3):
        reason_code = get_value(elements, index)
        amount = get_value(elements, index + 1)

        if reason_code:
            adjustments.append(
                {
                    "group": group_code,
                    "reason_code": reason_code,
                    "amount": amount,
                }
            )

    return adjustments


def parse_835_file(file_path):
    parsed_data = {
        "source_file": file_path.name,
        "sender_id": None,
        "receiver_id": None,
        "payer_name": None,
        "provider_name": None,
        "patient_name": None,
        "payment_info": {},
        "claims": [],
    }

    current_claim = None
    current_service_line = None
    raw_content = file_path.read_text(encoding="utf-8")
    segments = [
        segment.strip() for segment in raw_content.split("~") if segment.strip()
    ]

    for segment in segments:
        elements = segment.split("*")
        segment_type = get_value(elements, 0)

        if segment_type == "ISA":
            parsed_data["sender_id"] = get_value(elements, 6)
            parsed_data["receiver_id"] = get_value(elements, 8)

        elif segment_type == "BPR":
            parsed_data["payment_info"] = {
                "total_payment": get_value(elements, 2),
                "payment_method": get_value(elements, 4),
                "transaction_date": get_value(elements, 16),
            }

        elif segment_type == "N1":
            entity_type = get_value(elements, 1)
            if entity_type == "PR":
                parsed_data["payer_name"] = get_value(elements, 2)
            elif entity_type == "PE":
                parsed_data["provider_name"] = get_value(elements, 2)

        elif segment_type == "CLP":
            current_claim = {
                "claim_id": get_value(elements, 1),
                "status_code": get_value(elements, 2),
                "total_charge": get_value(elements, 3),
                "amount_paid": get_value(elements, 4),
                "patient_name": None,
                "provider_name": None,
                "date_of_service": None,
                "adjustments": [],
                "service_lines": [],
            }
            parsed_data["claims"].append(current_claim)
            current_service_line = None

        elif segment_type == "NM1" and current_claim is not None:
            entity_type = get_value(elements, 1)
            person_name = get_person_name(elements)

            if entity_type == "QC":
                current_claim["patient_name"] = person_name
                parsed_data["patient_name"] = parsed_data["patient_name"] or person_name
            elif entity_type == "82":
                current_claim["provider_name"] = person_name
                parsed_data["provider_name"] = (
                    parsed_data["provider_name"] or person_name
                )

        elif segment_type == "SVC" and current_claim is not None:
            current_service_line = {
                "procedure_code": get_value(elements, 1).replace(":", "|"),
                "charge_amount": get_value(elements, 2),
                "paid_amount": get_value(elements, 3),
                "date_of_service": None,
                "adjustments": [],
            }
            current_claim["service_lines"].append(current_service_line)

        elif segment_type == "DTM":
            date_type = get_value(elements, 1)
            date_value = get_value(elements, 2)

            if date_type == "472" and current_service_line is not None:
                current_service_line["date_of_service"] = date_value
            elif date_type in {"050", "150"} and current_claim is not None:
                current_claim["date_of_service"] = date_value

        elif segment_type == "CAS":
            target = (
                current_service_line
                if current_service_line is not None
                else current_claim
            )
            if target is not None:
                target["adjustments"].extend(get_adjustments(elements))

    return parsed_data


def save_json(parsed_data, output_file):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(parsed_data, indent=2), encoding="utf-8")


def parse_all_835_files():
    edi_files = sorted(INPUT_FOLDER.glob("*.edi"))

    for edi_file in edi_files:
        parsed_data = parse_835_file(edi_file)
        output_file = OUTPUT_FOLDER / f"{edi_file.stem}.json"
        save_json(parsed_data, output_file)
        print(f"Saved {output_file}")

    print(f"Parsed {len(edi_files)} EDI file(s).")


parse_all_835_files()
