from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

STATUSES = {"COVERED", "PARTIAL", "NOT_COVERED", "UNKNOWN", "NOT_APPLICABLE"}


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = text.replace("≥", ">=").replace("≤", "<=").replace("≈", "~")
    text = re.sub(r"[^a-z0-9.%/+<>=~-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _values(value: Any) -> list[str]:
    out: list[str] = []
    if value in (None, "", [], {}):
        return out
    if isinstance(value, dict):
        for key, item in value.items():
            if item not in (None, "", False, [], {}):
                vals = _values(item)
                out.extend(vals or [f"{key}: {item}"])
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            out.extend(_values(item))
    elif isinstance(value, bool):
        if value:
            out.append("Required")
    else:
        out.append(str(value))
    return list(dict.fromkeys(x for x in out if x.strip()))


def _tokens(value: Any) -> set[str]:
    stop = {"the", "and", "for", "with", "shall", "required", "requirement", "requirements", "applicable"}
    return {x for x in _norm(value).split() if len(x) > 1 and x not in stop}


def _concept_match(needle: str, haystack: str) -> bool:
    a, b = _norm(needle), _norm(haystack)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    at, bt = _tokens(a), _tokens(b)
    return bool(at) and len(at & bt) / len(at) >= 0.6


_UNIT_SCALE: dict[str, tuple[float, str]] = {
    "mm": (0.001, "m"), "millimeter": (0.001, "m"), "millimeters": (0.001, "m"),
    "cm": (0.01, "m"), "centimeter": (0.01, "m"), "centimeters": (0.01, "m"),
    "m": (1.0, "m"), "meter": (1.0, "m"), "meters": (1.0, "m"),
    "kv": (1000.0, "v"), "kilovolt": (1000.0, "v"), "kilovolts": (1000.0, "v"),
    "v": (1.0, "v"), "volt": (1.0, "v"), "volts": (1.0, "v"),
    "khz": (1000.0, "hz"), "hz": (1.0, "hz"), "hertz": (1.0, "hz"),
    "kw": (1000.0, "w"), "w": (1.0, "w"), "watt": (1.0, "w"), "watts": (1.0, "w"),
    "ma": (0.001, "a"), "a": (1.0, "a"), "amp": (1.0, "a"), "amps": (1.0, "a"),
    "mpa": (1_000_000.0, "pa"), "kpa": (1000.0, "pa"), "pa": (1.0, "pa"),
    "bar": (100_000.0, "pa"),
}


def _quantity(value: Any, fallback_unit: str = "") -> tuple[float, str] | None:
    text = _norm(value)
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*([a-z]+)?\b", text)
    if not m:
        return None
    number = float(m.group(1))
    unit = (m.group(2) or fallback_unit or "").lower()
    if unit not in _UNIT_SCALE:
        return None
    factor, base = _UNIT_SCALE[unit]
    return number * factor, base


def _operator(value: Any) -> str:
    text = _norm(value)
    if ">=" in text or "minimum" in text or "at least" in text or "not less than" in text:
        return ">="
    if "<=" in text or "maximum" in text or "at most" in text or "not more than" in text:
        return "<="
    if re.search(r"(^|\s)>($|\s)", text):
        return ">"
    if re.search(r"(^|\s)<($|\s)", text):
        return "<"
    if "approximately" in text or "approx" in text or "~" in text or "nominal" in text:
        return "~"
    return "="


def _structured_range(attribute: Any) -> tuple[float | None, float | None, str | None, str]:
    if not isinstance(attribute, dict):
        q = _quantity(attribute)
        return (q[0], q[0], q[1], "=") if q else (None, None, None, "")
    unit = str(attribute.get("unit") or "")
    exact = _quantity(attribute.get("value"), unit) if attribute.get("value") is not None else None
    minimum = _quantity(attribute.get("min") if attribute.get("min") is not None else attribute.get("minimum"), unit)
    maximum = _quantity(attribute.get("max") if attribute.get("max") is not None else attribute.get("maximum"), unit)
    if exact:
        return exact[0], exact[0], exact[1], str(attribute.get("operator") or "=")
    base = (minimum or maximum)
    return (minimum[0] if minimum else None, maximum[0] if maximum else None, base[1] if base else None, str(attribute.get("operator") or "range"))


def _numeric_match(requirement: str, attribute: Any) -> bool:
    rq = _quantity(requirement)
    if not rq:
        return False
    low, high, base, _ = _structured_range(attribute)
    if base != rq[1] or (low is None and high is None):
        return False
    op = _operator(requirement)
    value = rq[0]
    eps = max(1e-9, abs(value) * 1e-6)
    if op == "=":
        return (low is None or value + eps >= low) and (high is None or value - eps <= high)
    if op == ">=":
        # Tender asks the product/standard to support at least this value. A structured exact/max
        # value can establish it only when the KB boundary reaches the requested threshold.
        bound = high if high is not None else low
        return bound is not None and bound + eps >= value
    if op == ">":
        bound = high if high is not None else low
        return bound is not None and bound > value + eps
    if op == "<=":
        bound = low if low is not None else high
        return bound is not None and bound - eps <= value
    if op == "<":
        bound = low if low is not None else high
        return bound is not None and bound < value - eps
    if op == "~":
        center = low if low == high else ((low or value) + (high or value)) / 2
        return math.isclose(center, value, rel_tol=0.02, abs_tol=eps)
    return False


def _technical_support(items: list[str], technical: dict[str, Any]) -> tuple[int, list[str]]:
    matched: list[str] = []
    candidates: list[tuple[str, Any]] = list(technical.items())
    for item in items:
        for key, value in candidates:
            rendered = f"{key}: {value}"
            # Require attribute-name/concept compatibility before a numeric value can establish
            # coverage, preventing an unrelated 230 value from satisfying a voltage requirement.
            concept_ok = _concept_match(item, key) or bool(_tokens(item) & _tokens(key))
            if _concept_match(item, rendered) or (concept_ok and _numeric_match(item, value)):
                matched.append(rendered)
                break
    return len(matched), list(dict.fromkeys(matched))


def _support(items: list[str], evidence: list[str]) -> tuple[int, list[str]]:
    matched: list[str] = []
    for item in items:
        for candidate in evidence:
            if _concept_match(item, candidate):
                matched.append(candidate)
                break
    return len(matched), list(dict.fromkeys(matched))


def _id(record: Any, *keys: str) -> str | None:
    if not isinstance(record, dict):
        return None
    for key in keys:
        if record.get(key):
            return str(record[key])
    return None


def _row(key: str, tender: list[str], status: str, evidence: list[str], evidence_type: str,
         source_record_ids: list[str], source_standard_ids: list[str] | None = None) -> dict[str, Any]:
    assert status in STATUSES
    record_ids = list(dict.fromkeys(x for x in source_record_ids if x))
    standard_ids = list(dict.fromkeys(x for x in (source_standard_ids or []) if x))
    return {
        "key": key,
        "label": re.sub(r"(?<!^)(?=[A-Z])", " ", key).replace("_", " ").title(),
        "tenderRequirement": "; ".join(tender) if tender else "Not specified",
        "tenderPresence": "PRESENT" if tender else "NOT_PRESENT",
        "status": status,
        "evidence": evidence,
        "standardEvidence": evidence,
        "evidenceType": evidence_type,
        "sourceRecordIds": record_ids,
        # Retained for compatibility with existing saved analyses/UI code.
        "sourceStandardIds": standard_ids,
    }


def evaluate_standard_coverage(*, requirement_profile: dict[str, Any], knowledge_bundle: dict[str, Any]) -> dict[str, Any]:
    """Compare the extracted requirement profile against one active-dataset evidence bundle.

    Retrieval/search fields are intentionally excluded from normative coverage decisions.
    """
    primary_standard = knowledge_bundle.get("primaryStandard") or None
    if not primary_standard:
        return {
            "evaluated": False,
            "summary": {k: 0 for k in ("covered", "partial", "notCovered", "unknown", "notApplicable")},
            "requirements": [],
            "provenance": knowledge_bundle.get("provenance") or {},
        }

    profile = requirement_profile or {}
    canonical_product = knowledge_bundle.get("canonicalProduct") or None
    standard = knowledge_bundle.get("primaryStandardRecord") or {}
    relationships = list(knowledge_bundle.get("relationships") or [])
    certifications = list(knowledge_bundle.get("certifications") or [])
    qcos = list(knowledge_bundle.get("qcos") or [])
    sid = str(primary_standard.get("standardId") or standard.get("standardId") or "")
    std_doc_id = _id(standard, "documentId", "standardId") or sid
    pid = _id(canonical_product, "productId", "documentId")
    scope = standard.get("scope") if isinstance(standard.get("scope"), dict) else {}
    technical = standard.get("technicalAttributes") if isinstance(standard.get("technicalAttributes"), dict) else {}
    requirements_covered = _values(standard.get("requirementsCovered"))
    testing_requirements = _values(standard.get("testingRequirements"))
    standard_apps = _values(scope.get("applications")) + _values(standard.get("applications")) + _values((canonical_product or {}).get("applications"))
    rows: list[dict[str, Any]] = []

    product_req = _values((profile.get("product") or {}).get("name"))
    if product_req:
        mapped = bool(canonical_product and (str(canonical_product.get("primaryStandardId") or "") == sid or sid in [str(x) for x in canonical_product.get("linkedStandards") or []]))
        family_match = bool(canonical_product and standard and _norm(canonical_product.get("productFamily")) == _norm(standard.get("productFamily") or (standard.get("classification") or {}).get("productGroup")))
        included = _values(scope.get("includedProducts"))
        excluded = _values(scope.get("excludedProducts"))
        sources = [x for x in (pid, std_doc_id) if x]
        if any(_concept_match(product_req[0], x) for x in excluded):
            rows.append(_row("product", product_req, "NOT_COVERED", [f"Product is explicitly excluded from {primary_standard.get('isNumber', sid)} scope."], "SCOPE_EXCLUSION", sources, [sid]))
        elif mapped:
            rows.append(_row("product", product_req, "COVERED", [f"Canonical product {(canonical_product or {}).get('productName') or product_req[0]} explicitly maps to {primary_standard.get('isNumber', sid)}."], "CANONICAL_PRODUCT_MAPPING", sources, [sid]))
        elif family_match:
            rows.append(_row("product", product_req, "COVERED", [f"Canonical product and selected standard share product family {(canonical_product or {}).get('productFamily')}."], "PRODUCT_FAMILY_MAPPING", sources, [sid]))
        elif any(_concept_match(product_req[0], x) for x in included):
            rows.append(_row("product", product_req, "COVERED", [f"Standard scope includes product: {x}" for x in included if _concept_match(product_req[0], x)][:3], "STANDARD_SCOPE", [std_doc_id], [sid]))
        else:
            rows.append(_row("product", product_req, "UNKNOWN", ["No structured normative product-scope mapping establishes coverage."], "MISSING_NORMATIVE_EVIDENCE", [std_doc_id], [sid]))

    app_req = _values((profile.get("application") or {}).get("useCase")) + _values((profile.get("application") or {}).get("environment"))
    if app_req:
        count, matches = _support(app_req, standard_apps)
        status = "COVERED" if count == len(app_req) else "PARTIAL" if count else "UNKNOWN"
        ev = [f"Structured application/scope evidence: {x}" for x in matches] or ["No structured application/scope evidence matches the tender context."]
        rows.append(_row("application", app_req, status, ev, "APPLICATION_SCOPE", [x for x in (pid, std_doc_id) if x], [sid]))

    materials = _values(profile.get("materials"))
    if materials:
        material_evidence = _values(standard.get("materials"))
        count, matches = _support(materials, material_evidence)
        status = "COVERED" if count == len(materials) and count else "PARTIAL" if count else "UNKNOWN"
        rows.append(_row("materials", materials, status, [f"Structured material evidence: {x}" for x in matches] or ["No structured normative material evidence is available."], "STRUCTURED_MATERIAL", [std_doc_id], [sid]))

    for key in ("dimensions", "technicalProperties"):
        req = _values(profile.get(key))
        if req:
            count, matches = _technical_support(req, technical)
            status = "COVERED" if count == len(req) and count else "PARTIAL" if count else "UNKNOWN"
            rows.append(_row(key, req, status, [f"Structured technical attribute: {x}" for x in matches] or ["Tender value may aid retrieval, but no structured normative technical attribute establishes coverage in the active knowledge record."], "TECHNICAL_ATTRIBUTE" if matches else "RETRIEVAL_ONLY_NOT_NORMATIVE", [std_doc_id], [sid]))

    performance = _values(profile.get("performance"))
    if performance:
        perf_evidence = requirements_covered + testing_requirements
        count, matches = _support(performance, perf_evidence)
        status = "COVERED" if count == len(performance) and count else "PARTIAL" if count else "UNKNOWN"
        rows.append(_row("performance", performance, status, [f"Structured requirement: {x}" for x in matches] or ["No structured performance requirement establishes coverage."], "REQUIREMENTS_COVERED", [std_doc_id], [sid]))

    safety = _values(profile.get("safety"))
    if safety:
        safety_rels = [r for r in relationships if str(r.get("relationship") or r.get("relationshipType") or "").upper() == "SAFETY" and str(r.get("applicability") or "Applicable").lower() not in {"not applicable", "excluded"}]
        if safety_rels:
            ev = [f"Applicable SAFETY relationship found: {r.get('standard') or r.get('toStandard') or r.get('toStandardId')} — {r.get('reason') or r.get('title') or 'safety requirements'}." for r in safety_rels]
            rel_ids = [_id(r, "relationshipId", "documentId") for r in safety_rels]
            related_sids = [str(r.get("standardId") or r.get("toStandardId") or r.get("standard") or r.get("toStandard") or "") for r in safety_rels]
            rows.append(_row("safety", safety, "PARTIAL", ev, "VERIFIED_RELATIONSHIP", [x for x in rel_ids if x], [sid] + related_sids))
        else:
            rows.append(_row("safety", safety, "UNKNOWN", ["No applicable structured SAFETY relationship or safety requirement was found."], "MISSING_NORMATIVE_EVIDENCE", [std_doc_id], [sid]))

    testing = _values(profile.get("testing"))
    if testing:
        test_rels = [r for r in relationships if str(r.get("relationship") or r.get("relationshipType") or "").upper() == "TEST_METHOD" and str(r.get("applicability") or "Applicable").lower() not in {"not applicable", "excluded"}]
        rel_evidence = [str(r.get("reason") or r.get("title") or r.get("toTitle") or "") for r in test_rels]
        count, matches = _support(testing, testing_requirements + requirements_covered + rel_evidence)
        status = "COVERED" if count == len(testing) and count else "PARTIAL" if count or test_rels else "UNKNOWN"
        ev = [f"Structured testing evidence: {x}" for x in matches]
        ev += [f"TEST_METHOD relationship: {r.get('standard') or r.get('toStandard') or r.get('toStandardId')} — {r.get('reason') or r.get('title') or 'test method'}." for r in test_rels]
        rel_ids = [_id(r, "relationshipId", "documentId") for r in test_rels]
        rows.append(_row("testing", testing, status, ev or ["No structured testing requirement or TEST_METHOD relationship establishes coverage."], "TESTING_REQUIREMENT", [std_doc_id] + [x for x in rel_ids if x], [sid]))

    cert = profile.get("certification") or {}
    cert_req = _values(cert.get("details")) if isinstance(cert, dict) else []
    cert_requested = bool(cert.get("requested")) if isinstance(cert, dict) else bool(cert_req)
    if cert_requested:
        verified = [c for c in certifications if c.get("sourceVerified") is True or "VERIFIED" in str(c.get("verificationStatus") or c.get("status") or "").upper()]
        record = verified[0] if verified else (certifications[0] if certifications else None)
        if record:
            mandatory = record.get("mandatory")
            complete = bool(record.get("type") and record.get("scheme") and mandatory in (True, False))
            status = "COVERED" if complete and record in verified else "PARTIAL"
            mandatory_text = "Mandatory" if mandatory is True else "Not Mandatory" if mandatory is False else "Mandatory status not established"
            ev = [f"{record.get('type') or 'Certification'}; {record.get('scheme') or 'scheme not recorded'}; {mandatory_text}; status {record.get('status') or 'not recorded'}." ]
            verified_qcos = [q for q in qcos if q.get("sourceVerified") is True or "VERIFIED" in str(q.get("verificationStatus") or q.get("status") or "").upper()]
            if verified_qcos:
                ev.extend(f"QCO record: {q.get('name') or q.get('qcoId')}; status {q.get('status') or 'not recorded'}; effective date {q.get('effectiveDate') or 'not recorded'}." for q in verified_qcos)
            record_ids = [_id(record, "certificationId", "documentId")] + [_id(q, "qcoId", "documentId") for q in verified_qcos]
            rows.append(_row("certification", cert_req or ["Certification applicability requested"], status, ev, "CERTIFICATION_RECORD", [x for x in record_ids if x], [sid]))
        else:
            rows.append(_row("certification", cert_req or ["Certification applicability requested"], "UNKNOWN", ["No certification record establishes applicability in the active knowledge base."], "MISSING_NORMATIVE_EVIDENCE", [], [sid]))

    summary = {"covered": 0, "partial": 0, "notCovered": 0, "unknown": 0, "notApplicable": 0}
    keymap = {"COVERED": "covered", "PARTIAL": "partial", "NOT_COVERED": "notCovered", "UNKNOWN": "unknown", "NOT_APPLICABLE": "notApplicable"}
    for row in rows:
        summary[keymap[row["status"]]] += 1
    return {
        "evaluated": True,
        "summary": summary,
        "requirements": rows,
        "provenance": knowledge_bundle.get("provenance") or {},
    }
