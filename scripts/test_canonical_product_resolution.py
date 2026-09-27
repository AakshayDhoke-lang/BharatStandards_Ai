from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.demo_engine import recommend_demo_standards, resolve_canonical_product  # noqa: E402
from app.standards_repository import build_matcher_cases  # noqa: E402


def load_knowledge() -> dict:
    data = json.loads((ROOT / "demo_data" / "complete_demo_database.json").read_text(encoding="utf-8"))
    return {k: data.get(k, []) for k in ("categories", "products", "standards", "relationships", "certifications", "qcos", "amendments")}


def profile(product: str, category: str = "", subcategory: str = "", application: str = "") -> dict:
    return {
        "product": {"name": product, "category": category, "subcategory": subcategory},
        "application": {"useCase": application},
    }


def assert_resolves(products, text: str, expected_id: str) -> None:
    resolved, diag = resolve_canonical_product(profile(text), text, products)
    assert resolved, (text, diag)
    assert resolved.get("productId") == expected_id, (text, resolved.get("productId"), expected_id, diag)


def main() -> None:
    knowledge = load_knowledge()
    products = knowledge["products"]
    cases = build_matcher_cases(knowledge)

    positives = [
        "portable fire extinguisher",
        "portable fire extinguishers",
        "fire extinguisher for office building",
        "ABC extinguisher",
        "portable emergency fire suppression extinguisher",
    ]
    for text in positives:
        assert_resolves(products, text, "fire-safety-1")

    negatives = ["fire alarm", "sprinkler system", "fire door", "industrial water pump"]
    for text in negatives:
        resolved, _ = resolve_canonical_product(profile(text), text, products)
        assert not resolved or resolved.get("productId") != "fire-safety-1", (text, resolved)

    fire_profile = profile(
        "portable fire extinguishers",
        category="fire protection equipment",
        subcategory="portable fire extinguishers",
        application="emergency fire protection government office buildings",
    )
    fire_text = (
        "Supply of portable fire extinguishers for government office buildings. "
        "Units shall meet applicable construction and performance requirements and shall be suitable "
        "for emergency fire protection. Mandatory certification requirements, where established in the database, shall be identified."
    )
    recommendations, diagnostics, family = recommend_demo_standards(fire_profile, fire_text, cases)
    assert family == "PORTABLE_FIRE_EXTINGUISHER", family
    assert recommendations and recommendations[0]["standardId"] == "IS-15683-2018", recommendations[:2]
    assert recommendations[0]["canonicalProductId"] == "fire-safety-1"
    signals = set(recommendations[0].get("compatibilitySignals") or [])
    assert "PRODUCT_ALIAS_MATCH" in signals
    assert "PRODUCT_FAMILY_MATCH" in signals
    assert "PRIMARY_STANDARD_LINK" in signals
    assert "TECHNICAL_TERM_MATCH" in signals

    case = next(c for c in cases if c["standard"]["standardId"] == "IS-15683-2018")
    assert case["productId"] == "fire-safety-1"
    assert any(c.get("certificationId") == "cert-fire-extinguisher" for c in case["certifications"])
    assert any(q.get("qcoId") == "qco-fire-extinguishers-2023" for q in case["qcos"])
    assert case["version"].get("versionRecordId") == "ver-is-15683-2018"
    assert case["version"].get("status") == "Latest / Current DEMO Reference"

    other = {
        "ceiling fan": "electrical-appliances-1",
        "centrifugal pump": "pumps-mechanical-1",
        "structural steel plate": "structural-steel-1",
        "examination gloves": "medical-consumables-1",
        "surgical gloves": "medical-consumables-2",
        "solar pv module": "solar-renewable-1",
        "pvc insulated cables": "electrical-cables-1",
        "upvc pipes": "water-pipes-1",
    }
    for text, expected in other.items():
        assert_resolves(products, text, expected)

    pipe, _ = resolve_canonical_product(profile("PVC water pipe"), "PVC water pipe", products)
    assert pipe and pipe.get("productId") == "water-pipes-1"
    assert pipe.get("productId") != "electrical-cables-1"

    pump, _ = resolve_canonical_product(profile("industrial water pump"), "industrial water pump", products)
    assert pump and pump.get("productId") == "pumps-mechanical-1"
    assert pump.get("productId") not in {"water-pipes-1", "water-storage-1"}

    print("CANONICAL PRODUCT RESOLUTION TESTS: PASS")
    print("Fire extinguisher aliases/plurals -> fire-safety-1: PASS")
    print("Fire alarm/sprinkler/fire door negative cases: PASS")
    print("Fire extinguisher -> IS-15683-2018: PASS")
    print("Certification/QCO/version lookup join: PASS")
    print("Other demo products: PASS")
    print("PVC water pipe != electrical cable: PASS")


if __name__ == "__main__":
    main()
