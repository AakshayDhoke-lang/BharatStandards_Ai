from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.firebase_service import get_firestore_client  # noqa: E402

DATA_FILE = ROOT / "demo_data" / "complete_demo_database.json"
COLLECTIONS = [
    "categories",
    "products",
    "standards",
    "relationships",
    "certifications",
    "qcos",
    "amendments",
    "sources",
    "submissions",
    "ingestionJobs",
    "auditLogs",
]


def slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return value.strip("-_") or "record"


def doc_id(collection_name: str, record: dict[str, Any], index: int) -> str:
    keys = {
        "categories": ["categoryId", "name"],
        "products": ["productId", "productFamily", "productName"],
        "standards": ["standardId", "isNumber"],
        "relationships": ["relationshipId"],
        "certifications": ["certificationId"],
        "qcos": ["qcoId"],
        "amendments": ["versionRecordId", "standardId"],
        "sources": ["sourceId", "sourceName"],
        "submissions": ["submissionId"],
        "ingestionJobs": ["jobId"],
        "auditLogs": ["entityId", "action"],
    }
    for key in keys[collection_name]:
        value = record.get(key)
        if value:
            if collection_name == "auditLogs" and key == "entityId":
                return slug(f"demo-audit-{index:03d}-{record.get('action', 'event')}-{value}")
            return slug(str(value))
    return f"demo-{collection_name}-{index:03d}"


def load_payload() -> dict[str, Any]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Demo database file not found: {DATA_FILE}")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def print_plan(payload: dict[str, Any]) -> None:
    print("BharatStandards AI — Complete DEMO Firestore Seeder")
    print("=" * 62)
    print(f"Dataset: DEMO")
    print(f"Seed version: {payload['meta']['seedVersion']}")
    for name in COLLECTIONS:
        print(f"  {name:<16} {len(payload.get(name, [])):>4}")
    print("\nThis seeder only writes datasets/demo/* and never touches REAL data or user analysis history.")


def seed(dry_run: bool = False) -> None:
    payload = load_payload()
    print_plan(payload)
    if dry_run:
        print("\nDry run complete. No Firestore writes were made.")
        return

    db = get_firestore_client()
    dataset_ref = db.collection("datasets").document("demo")
    dataset_ref.set({
        **payload["meta"],
        "datasetMode": "DEMO",
        "dataMode": "DEMO",
        "active": True,
    }, merge=True)

    queued = 0
    batch = db.batch()
    for collection_name in COLLECTIONS:
        records = payload.get(collection_name, [])
        for index, record in enumerate(records, start=1):
            record = dict(record)
            record.setdefault("dataMode", "DEMO")
            record.setdefault("datasetMode", "DEMO")
            record.setdefault("seedVersion", payload["meta"]["seedVersion"])
            ref = dataset_ref.collection(collection_name).document(doc_id(collection_name, record, index))
            batch.set(ref, record, merge=True)
            queued += 1
            if queued % 400 == 0:
                batch.commit()
                batch = db.batch()
                print(f"Committed {queued} records...")

    if queued % 400:
        batch.commit()

    print("\nSeed complete.")
    print(f"Wrote/updated {queued} shared DEMO records under datasets/demo.")
    print("REAL dataset and users/{uid}/analyses were not modified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the complete BharatStandards AI DEMO knowledge base into Firestore.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without writing to Firestore.")
    args = parser.parse_args()
    seed(dry_run=args.dry_run)
