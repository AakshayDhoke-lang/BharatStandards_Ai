from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.coverage import evaluate_standard_coverage
from app.demo_engine import recommend_demo_standards, resolve_canonical_product
from app.standards_repository import build_knowledge_evidence_bundle, build_matcher_cases

DATA = json.loads((ROOT / "demo_data" / "complete_demo_database.json").read_text())
KNOWLEDGE = {k: v for k, v in DATA.items() if isinstance(v, list)}
CASES = build_matcher_cases(KNOWLEDGE)

REPRESENTATIVE = [
    "Ceiling Fan",
    "Pvc Insulated Cable",
    "Structural Steel",
    "Reinforcement Steel Bar",
    "Ordinary Portland Cement",
    "Coarse Aggregate",
    "Plain Concrete",
    "Upvc Pipe",
    "Centrifugal Water Pump",
    "Medical Examination Gloves",
    "Surgical Rubber Gloves",
    "Portable Fire Extinguisher",
    "Industrial Safety Helmet",
    "Information Technology Equipment",
    "Crystalline Silicon Pv Module",
]


def product_by_name(name: str):
    for p in KNOWLEDGE["products"]:
        if str(p.get("productName", "")).lower() == name.lower():
            return p
    return None


def main() -> None:
    standards = {str(s.get("standardId")): s for s in KNOWLEDGE["standards"]}
    findings: list[str] = []

    # Referential integrity.
    for p in KNOWLEDGE["products"]:
        pid = p.get("productId")
        primary = str(p.get("primaryStandardId") or "")
        if primary and primary not in standards:
            findings.append(f"dangling product primary standard: {pid} -> {primary}")
        for sid in p.get("linkedStandards") or []:
            if str(sid) not in standards:
                findings.append(f"dangling product linked standard: {pid} -> {sid}")
    for c in KNOWLEDGE["certifications"]:
        sid = str(c.get("standardId") or "")
        if sid and sid not in standards:
            findings.append(f"dangling certification standard: {c.get('certificationId')} -> {sid}")
    for q in KNOWLEDGE["qcos"]:
        ids = [str(q.get("standardId") or "")] + [str(x) for x in q.get("standardIds") or []]
        for sid in [x for x in ids if x]:
            if sid not in standards:
                findings.append(f"dangling qco standard: {q.get('qcoId')} -> {sid}")
    for v in KNOWLEDGE["amendments"]:
        sid = str(v.get("standardId") or "")
        if sid and sid not in standards:
            findings.append(f"dangling version standard: {v.get('versionRecordId')} -> {sid}")

    print("REPRESENTATIVE PRODUCT REGRESSION")
    print("Product | Expected Primary | Actual Primary | Coverage | Result")
    for name in REPRESENTATIVE:
        p = product_by_name(name)
        if not p:
            print(f"{name} | MISSING PRODUCT | - | - | FAIL")
            findings.append(f"representative product absent: {name}")
            continue
        profile = {
            "product": {"name": p["productName"], "category": p.get("category", "")},
            "application": {"useCase": (p.get("applications") or [""])[0]},
        }
        resolved, _ = resolve_canonical_product(profile, p["productName"], KNOWLEDGE["products"])
        recs, _, _ = recommend_demo_standards(profile, p["productName"], CASES)
        actual = recs[0]["standardId"] if recs else None
        expected = p.get("primaryStandardId")
        bundle = build_knowledge_evidence_bundle(dataset="demo", knowledge=KNOWLEDGE, canonical_product=resolved, primary_standard=recs[0] if recs else None, matcher_cases=CASES)
        coverage = evaluate_standard_coverage(requirement_profile=profile, knowledge_bundle=bundle)
        product_row = next((r for r in coverage.get("requirements", []) if r.get("key") == "product"), None)
        ok = bool(resolved and actual == expected and coverage.get("evaluated") and product_row and product_row.get("status") == "COVERED")
        print(f"{name} | {expected} | {actual} | {product_row.get('status') if product_row else '-'} | {'PASS' if ok else 'FAIL'}")
        if not ok:
            findings.append(f"representative regression failed: {name}")

    # Unsupported/ambiguous product must not be forced to a standard.
    unsupported_profile = {"product": {"name": "industrial fire alarm control panel", "category": "Fire Safety"}}
    recs, _, _ = recommend_demo_standards(unsupported_profile, "industrial fire alarm control panel with smoke detector inputs", CASES)
    if recs:
        findings.append(f"unsupported product forced match: {recs[0].get('standardId')}")
    print(f"Unsupported product no-force-match: {'PASS' if not recs else 'FAIL'}")

    # DEMO/REAL isolation at matcher input boundary: empty REAL knowledge cannot see DEMO cases.
    real_cases = build_matcher_cases({k: [] for k in KNOWLEDGE})
    real_recs, _, _ = recommend_demo_standards({"product": {"name": "Ceiling Fan"}}, "Ceiling Fan", real_cases) if real_cases else ([], [], None)
    if real_recs:
        findings.append("REAL empty dataset contaminated by DEMO")
    print(f"Empty REAL dataset isolation: {'PASS' if not real_recs else 'FAIL'}")

    # Security/config invariants required by the canonical prompt.
    firestore_rules = (ROOT / "firestore.rules").read_text()
    storage_rules = (ROOT / "storage.rules").read_text()
    if "request.auth.uid == userId" not in firestore_rules or "analyses/{analysisId}" not in firestore_rules:
        findings.append("personal analysis rule invariant not found")
    if "role == resource.data.role" not in firestore_rules:
        findings.append("self role escalation guard not found")
    if "request.auth.uid == userId || contributor()" not in storage_rules:
        findings.append("ingestion storage read ownership/contributor rule not found")

    # Secrets must not be exposed via VITE_ variables.
    for env_name in [".env", ".env.example", ".env.production.example"]:
        path = ROOT / env_name
        if path.exists():
            for line in path.read_text(errors="ignore").splitlines():
                if line.startswith("VITE_") and ("NVIDIA_API_KEY" in line or "API_KEY=" in line and "FIREBASE" not in line):
                    findings.append(f"potential frontend secret in {env_name}: {line.split('=',1)[0]}")

    if findings:
        print("FINAL AUDIT CHECKS: FAIL")
        for f in findings:
            print(" -", f)
        raise SystemExit(1)
    print("FINAL AUDIT CHECKS: PASS")


if __name__ == "__main__":
    main()
