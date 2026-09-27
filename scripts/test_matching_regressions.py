from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.demo_engine import recommend_demo_standards  # noqa: E402


def run_case(name: str, profile: dict, text: str, expected_family: str, expected_standard: str | None):
    candidates, diagnostics, family = recommend_demo_standards(profile, text)
    assert family == expected_family, (name, family, expected_family)
    actual = candidates[0]["standardId"] if candidates else None
    assert actual == expected_standard, (name, actual, expected_standard)
    return candidates, diagnostics


def main() -> None:
    pipe_candidates, pipe_diag = run_case(
        "PVC water pipe",
        {
            "product": {"name": "unplasticized PVC pipe", "category": "pipe", "subcategory": "PVC"},
            "application": {"useCase": "potable water distribution", "environment": "underground service"},
            "materials": ["unplasticized PVC"],
            "dimensions": {"diameters": ["25 mm", "50 mm", "90 mm"]},
            "testing": ["dimensional tests", "pressure tests", "manufacturer test certificates"],
            "certification": {"requested": True, "details": "where applicable"},
        },
        "Procurement of 8,000 metres of unplasticized PVC pipes for potable water distribution. Underground service. Diameters 25 mm, 50 mm and 90 mm. Pressure tests required. Where BIS certification or any mandatory regulatory requirement applies, valid evidence shall be provided.",
        "PVC_WATER_PIPE",
        None,
    )
    cable_check = next(d for d in pipe_diag if d["standardId"] == "IS-694-2010")
    assert pipe_candidates == []
    assert cable_check["productCompatible"] is False
    assert cable_check["rejectReason"] == "PRODUCT_FAMILY_MISMATCH"
    assert cable_check["finalScore"] is None

    cable_candidates, _ = run_case(
        "Electrical cable",
        {"product": {"name": "PVC insulated electrical cable", "category": "electrical", "subcategory": "cable"}, "application": {"useCase": "electrical wiring"}, "materials": ["PVC", "copper"]},
        "Procurement of PVC insulated electrical cables for electrical wiring.",
        "ELECTRICAL_CABLE",
        "IS-694-2010",
    )
    assert all((e["source"] in {"INPUT_TEXT", "REQUIREMENT_PROFILE"}) for e in cable_candidates[0]["matchedEvidence"])

    run_case(
        "Ceiling fan",
        {"product": {"name": "Ceiling Fan", "category": "Electrical Appliances", "subcategory": "Fans"}, "application": {"useCase": "air circulation"}, "technicalProperties": {"voltage": "230 V", "frequency": "50 Hz"}},
        "Procurement of ceiling fans for classroom air circulation at 230 V, 50 Hz.",
        "CEILING_FAN",
        "IS-374-2019",
    )

    run_case(
        "Structural steel plate",
        {"product": {"name": "Structural Steel Plates", "category": "Materials & Structural", "subcategory": "Steel Plate"}, "application": {"useCase": "bridge fabrication"}, "materials": ["hot rolled steel"], "technicalProperties": {"yieldStrength": "250 MPa"}},
        "Structural steel plates, hot rolled, 250 MPa yield strength for bridge fabrication.",
        "STRUCTURAL_STEEL_PLATE",
        "IS-2062-2011",
    )

    # Cross-product assertions: shared materials/properties cannot establish identity.
    assert recommend_demo_standards({"product": {"name": "PVC water pipe"}, "materials": ["PVC"]}, "PVC water pipe")[0] == []
    assert recommend_demo_standards({"product": {"name": "Structural Steel Plate"}, "materials": ["steel"]}, "Structural steel plate")[0][0]["standardId"] != "IS-694-2010"
    assert recommend_demo_standards({"product": {"name": "Ceiling Fan"}}, "Ceiling fan")[0][0]["standardId"] != "IS-694-2010"

    print("MATCHING REGRESSION TESTS: PASS")
    print("PVC water pipe -> no compatible DEMO standard: PASS")
    print("PVC water pipe -> IS 694 hard rejection: PASS")
    print("Electrical cable -> IS 694: PASS")
    print("Ceiling fan -> IS 374: PASS")
    print("Structural steel plate -> IS 2062: PASS")


if __name__ == "__main__":
    main()
