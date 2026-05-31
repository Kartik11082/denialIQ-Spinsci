import json
from pathlib import Path

# Setup paths (Adjust as needed)
INPUT_FOLDER = Path("../data/mock/005010X222 Health Care Claim Professional (837)")
OUTPUT_FOLDER = Path("./837_output")


def get_value(elements, index, default=""):
    return elements[index].strip() if index < len(elements) else default


def get_person_name(elements):
    # NM1 segments: 3 is Last Name/Org, 4 is First Name
    last_name = get_value(elements, 3)
    first_name = get_value(elements, 4)
    return f"{first_name} {last_name}".strip()


def parse_837_file(file_path):
    parsed_data = {
        "source_file": file_path.name,
        "billing_provider": {},
        "subscriber": {},
        "patient": {},
        "claims": [],
    }

    current_claim = None
    raw_content = file_path.read_text(encoding="utf-8")
    # Clean and split segments
    segments = [s.strip() for s in raw_content.split("~") if s.strip()]

    for segment in segments:
        elements = segment.split("*")
        tag = get_value(elements, 0)

        # 1. Header Information
        if tag == "BHT":
            parsed_data["transaction_date"] = get_value(elements, 4)
            parsed_data["claim_type"] = get_value(elements, 6)

        # 2. Entity Identification (Names & NPIs)
        elif tag == "NM1":
            entity_type = get_value(elements, 1)
            name = get_person_name(elements)
            npi = get_value(elements, 9)

            if entity_type == "85":  # Billing Provider
                parsed_data["billing_provider"] = {"name": name, "npi": npi}
            elif entity_type == "IL":  # Subscriber
                parsed_data["subscriber"] = {"name": name, "id": npi}
            elif entity_type == "QC":  # Patient (if different from subscriber)
                parsed_data["patient"] = {"name": name}

        # 3. Claim Level Information (The "Invoice" Header)
        elif tag == "CLM":
            current_claim = {
                "claim_submitter_id": get_value(elements, 1),
                "total_billed_amount": get_value(elements, 2),
                "place_of_service": get_value(elements, 5).split(":")[0],
                "diagnoses": [],
                "service_lines": [],
            }
            parsed_data["claims"].append(current_claim)

        # 4. Diagnosis Codes (ICD-10)
        elif tag == "HI" and current_claim is not None:
            # HI segments can contain multiple diagnoses (e.g., HI*BK:M1711*BF:M1901)
            for entry in elements[1:]:
                if ":" in entry:
                    code = entry.split(":")[1]
                    current_claim["diagnoses"].append(code)

        # 5. Service Line Detail (Procedures/CPT)
        elif tag == "SV1" and current_claim is not None:
            # SV1*HC:99214*150*UN*1***1:2:3~
            proc_info = get_value(elements, 1).split(":")
            current_line = {
                "procedure_code": proc_info[1] if len(proc_info) > 1 else proc_info[0],
                "modifiers": proc_info[2:] if len(proc_info) > 2 else [],
                "line_charge": get_value(elements, 2),
                "units": get_value(elements, 4),
            }
            current_claim["service_lines"].append(current_line)

        # 6. Service Date
        elif tag == "DTM" and current_claim:
            date_type = get_value(elements, 1)
            if date_type == "472":  # Service Date
                if current_claim["service_lines"]:
                    current_claim["service_lines"][-1]["date"] = get_value(elements, 2)
                else:
                    current_claim["date_of_service"] = get_value(elements, 2)

    return parsed_data


def run_conversion():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    for edi_file in INPUT_FOLDER.glob("*.edi"):
        data = parse_837_file(edi_file)
        output_path = OUTPUT_FOLDER / f"{edi_file.stem}_837.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Successfully converted {edi_file.name}")


if __name__ == "__main__":
    run_conversion()
