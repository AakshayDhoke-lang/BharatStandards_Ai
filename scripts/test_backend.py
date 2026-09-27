from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.document_processing import parse_document_bytes
from app.demo_engine import recommend_demo_standards


def main() -> None:
    txt = parse_document_bytes("tender.txt", b"Procurement of ceiling fans, 230 V AC, 50 Hz, 1200 mm sweep")
    assert txt["status"] == "SUCCESS" and txt["processingEngine"] == "NATIVE_TEXT"

    import fitz
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Procurement of ceiling fans 230 V 50 Hz")
    pdf = parse_document_bytes("tender.pdf", document.tobytes())
    document.close()
    assert pdf["processingEngine"] == "PYMUPDF" and pdf["characterCount"] > 10

    profile = {
        "product": {"name": "Ceiling Fan", "category": "Electrical Appliances"},
        "technicalProperties": {"voltage": "230 V", "frequency": "50 Hz"},
        "dimensions": {"sweep": "1200 mm"},
    }
    candidates, diagnostics, family = recommend_demo_standards(profile, txt["fullText"])
    assert candidates and candidates[0]["isNumber"] == "IS 374 : 2019"
    assert family == "CEILING_FAN" and diagnostics
    print("BharatStandards AI backend self-test: PASS")
    print("Parser: lightweight stack")
    print("Data hand-off: normalized text -> requirement profile -> DEMO matcher")


if __name__ == "__main__":
    main()
