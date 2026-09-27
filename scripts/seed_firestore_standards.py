from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.demo_engine import DEMO_CASES  # noqa: E402
from app.firebase_service import get_firestore_client  # noqa: E402


def main() -> None:
    print("BharatStandards AI — exact DEMO knowledge migration")
    print("=" * 58)
    db = get_firestore_client()
    root = db.collection("datasets").document("demo")
    batch = db.batch()
    for case in DEMO_CASES:
        standard = case["standard"]
        sid = standard["standardId"]
        document_id = sid.replace("/", "_").replace(" ", "_")
        record = {
            **standard,
            "caseId": case["caseId"],
            "productFamily": case["productFamily"],
            "identityAliases": case.get("identityAliases", []),
            "categories": case.get("categories", []),
            "subcategories": case.get("subcategories", []),
            "applications": case.get("applications", []),
            "materials": case.get("materials", []),
            "relationships": case.get("relationships", []),
            "version": case.get("version", {}),
            "certifications": case.get("certifications", []),
            "qcos": case.get("qcos", []),
            "dataMode": "DEMO",
            "verificationStatus": "DEMO",
            "standard": standard,
        }
        batch.set(root.collection("standards").document(document_id), record, merge=True)
        print(f"Queued: {sid} | {case['productFamily']}")
    batch.set(root, {"dataMode": "DEMO", "name": "BharatStandards AI Demo Dataset"}, merge=True)
    batch.commit()
    print(f"Uploaded {len(DEMO_CASES)} exact matcher records to datasets/demo/standards.")
    print("Existing documents are merged; REAL data is untouched.")


if __name__ == "__main__":
    main()
