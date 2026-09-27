from __future__ import annotations

import re
from typing import Any

# DEMO records are deliberately small and explicit. A standard can only be
# recommended when the current procurement case resolves to the same canonical
# product family. Shared materials (PVC, steel, copper, etc.) never establish
# product identity.
DEMO_CASES: list[dict[str, Any]] = [
    {
        "caseId": "ceilingFan",
        "productFamily": "CEILING_FAN",
        "identityAliases": ["ceiling fan", "ceiling fans", "electric ceiling fan", "fan"],
        "categories": ["electrical appliances", "fans", "fan"],
        "subcategories": ["ceiling fan", "fans"],
        "applications": ["air circulation", "indoor", "classroom", "school"],
        "materials": [],
        "standard": {
            "standardId": "IS-374-2019",
            "isNumber": "IS 374 : 2019",
            "title": "Electric ceiling type fans and regulators — Specification",
            "category": "Electrical Appliances",
            "status": "ACTIVE",
            "confidenceBase": 82,
            "evidenceTerms": ["ceiling fan", "fan", "air circulation", "1200 mm", "230 v", "50 hz"],
        },
        "relationships": [
            {"standard": "IS 302-2-80 : 2017", "title": "Safety of household electrical appliances — Particular requirements for fans", "relationship": "SAFETY", "applicability": "Applicable", "mandatory": "Needs Review", "reason": "Electrical safety requirements", "status": "ACTIVE"},
            {"standard": "IS 6873 : 2019", "title": "Limits and methods of measurement of radio disturbance", "relationship": "TEST_METHOD", "applicability": "Applicable", "mandatory": "No", "reason": "EMC testing where applicable", "status": "ACTIVE"},
        ],
        "version": {"currentVersion": "IS 374 : 2019", "status": "Latest", "reaffirmed": "2024", "supersedes": None, "supersededBy": None, "amendments": []},
        # Demo regulatory records marked Needs Review cannot establish legal mandatory status.
        "certifications": [{"type": "BIS Product Certification", "mandatory": None, "scheme": "Scheme-I", "status": "Needs Review", "sourceVerified": False}],
        "qcos": [{"name": "Electric Fans (Quality Control) Order, 2024", "status": "Needs Review", "effectiveDate": "05 Mar 2025", "sourceVerified": False}],
    },
    {
        "caseId": "structuralSteel",
        "productFamily": "STRUCTURAL_STEEL_PLATE",
        "identityAliases": ["structural steel", "steel plate", "steel plates", "structural steel plate", "structural steel plates", "hot rolled steel"],
        "categories": ["materials & structural", "structural steel", "steel"],
        "subcategories": ["steel plate", "structural steel plate"],
        "applications": ["structural", "bridge", "fabrication"],
        "materials": ["steel", "hot rolled steel"],
        "standard": {
            "standardId": "IS-2062-2011",
            "isNumber": "IS 2062 : 2011",
            "title": "Hot rolled medium and high tensile structural steel",
            "category": "Materials & Structural",
            "status": "ACTIVE",
            "confidenceBase": 84,
            "evidenceTerms": ["structural steel", "steel plate", "steel plates", "hot rolled", "250 mpa", "yield strength", "weldability"],
        },
        "relationships": [
            {"standard": "IS 1608 (Part 1) : 2022", "title": "Metallic materials — Tensile testing", "relationship": "TEST_METHOD", "applicability": "Applicable", "mandatory": "No", "reason": "Tensile property verification", "status": "ACTIVE"},
            {"standard": "IS 228 (Series)", "title": "Methods of chemical analysis of steels", "relationship": "TEST_METHOD", "applicability": "Applicable", "mandatory": "No", "reason": "Chemical composition verification", "status": "ACTIVE"},
        ],
        "version": {"currentVersion": "IS 2062 : 2011", "status": "Needs Review", "reaffirmed": None, "supersedes": None, "supersededBy": None, "amendments": ["Amendment No. 2 — demo registry"]},
        "certifications": [{"type": "BIS Product Certification", "mandatory": None, "scheme": "Scheme-I", "status": "Needs Review", "sourceVerified": False}],
        "qcos": [],
    },
    {
        "caseId": "electricalCable",
        "productFamily": "ELECTRICAL_CABLE",
        "identityAliases": ["pvc insulated cable", "pvc insulated cables", "electrical cable", "electrical cables", "electric cable", "cable", "cables", "building wire"],
        "categories": ["electrical", "electrical cable", "cables"],
        "subcategories": ["pvc insulated cable", "cable"],
        "applications": ["wiring", "electrical installation"],
        "materials": ["pvc", "copper", "aluminium"],
        "standard": {
            "standardId": "IS-694-2010",
            "isNumber": "IS 694 : 2010",
            "title": "PVC insulated cables for working voltages up to and including 1100 V",
            "category": "Electrical",
            "status": "REVISED",
            "confidenceBase": 84,
            "evidenceTerms": ["pvc insulated", "electrical cable", "cable", "cables", "1100 v", "conductor", "insulation"],
        },
        "relationships": [
            {"standard": "IS 10810 (Series)", "title": "Methods of test for cables", "relationship": "TEST_METHOD", "applicability": "Applicable", "mandatory": "No", "reason": "Cable testing methods", "status": "Needs Review"},
        ],
        "version": {"currentVersion": "IS 694 : 2010", "status": "Needs Review", "reaffirmed": None, "supersedes": None, "supersededBy": None, "amendments": []},
        "certifications": [{"type": "BIS Product Certification", "mandatory": None, "scheme": "Scheme-I", "status": "Needs Review", "sourceVerified": False}],
        "qcos": [],
    },
    {
        "caseId": "waterTank",
        "productFamily": "WATER_TANK",
        "identityAliases": ["water storage tank", "water tank", "polyethylene water tank", "rotomoulded water tank", "rotational moulded water tank"],
        "categories": ["water storage", "plastic products", "civil engineering", "tank"],
        "subcategories": ["water tank", "polyethylene tank"],
        "applications": ["water storage", "potable water storage"],
        "materials": ["polyethylene", "plastic"],
        "standard": {
            "standardId": "IS-12701",
            "isNumber": "IS 12701",
            "title": "Rotational moulded polyethylene water storage tanks — Specification",
            "category": "Water Storage",
            "status": "NEEDS_REVIEW",
            "confidenceBase": 82,
            "evidenceTerms": ["water storage tank", "water tank", "polyethylene", "potable water", "capacity", "rotomoulded"],
        },
        "relationships": [],
        "version": {"currentVersion": "IS 12701", "status": "Needs Review", "reaffirmed": None, "supersedes": None, "supersededBy": None, "amendments": []},
        "certifications": [],
        "qcos": [],
    },
]

MATERIAL_TERMS = {"pvc", "steel", "copper", "plastic", "aluminium", "aluminum", "polyethylene"}
GENERIC_PRODUCT_TERMS = {
    "product", "equipment", "system", "item", "goods", "supply", "government", "office",
    "building", "industrial", "general", "type", "standard", "requirements", "requirement",
}


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_flatten(v) for v in value)
    return "" if value is None else str(value)


def _singularize_token(token: str) -> str:
    """Conservative English singularisation for procurement product identity.

    This intentionally avoids aggressive stemming.  It only removes common plural forms
    when doing so is unlikely to change the product concept.
    """
    irregular = {"buses": "bus", "gloves": "glove", "pipes": "pipe", "cables": "cable", "fans": "fan", "pumps": "pump", "modules": "module", "tanks": "tank", "extinguishers": "extinguisher", "helmets": "helmet", "plates": "plate", "bars": "bar", "lamps": "lamp", "wires": "wire"}
    if token in irregular:
        return irregular[token]
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("ses") and not token.endswith("sses"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def normalize_product_text(text: Any) -> str:
    """Normalize product identity consistently across AI output and Firestore aliases."""
    import unicodedata

    value = unicodedata.normalize("NFKC", str(text or "")).lower()
    value = value.replace("-", " ").replace("/", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    tokens = [_singularize_token(t) for t in value.split() if t]
    return " ".join(tokens).strip()


def _norm(text: Any) -> str:
    return normalize_product_text(text)


def _tokens(value: Any) -> set[str]:
    return {t for t in _norm(value).split() if t}


def _identity_tokens(value: Any) -> set[str]:
    return {t for t in _tokens(value) if t not in MATERIAL_TERMS and t not in GENERIC_PRODUCT_TERMS}


def _contains_phrase(text: str, phrase: str) -> bool:
    """Exact normalized token/phrase containment; never raw substring matching."""
    t = _norm(text)
    p = _norm(phrase)
    if not p:
        return False
    return re.search(rf"(?:^|\s){re.escape(p)}(?:$|\s)", t) is not None


def _profile_text(requirement_profile: dict[str, Any]) -> str:
    return _norm(_flatten(requirement_profile))


def _identity_text(requirement_profile: dict[str, Any], original_text: str) -> str:
    product = requirement_profile.get("product") or {}
    parts = [product.get("name", ""), product.get("subcategory", ""), product.get("category", ""), original_text]
    return _norm(" ".join(str(x or "") for x in parts))


def _case_products(cases: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for case in cases or []:
        product = case.get("product")
        if not isinstance(product, dict):
            continue
        product_id = str(product.get("productId") or product.get("documentId") or case.get("productId") or "")
        key = product_id or str(product.get("productFamily") or case.get("productFamily") or "")
        if key and key not in seen:
            seen.add(key)
            rows.append(product)
    return rows


def resolve_canonical_product(
    requirement_profile: dict[str, Any],
    original_text: str,
    products: list[dict[str, Any]] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Resolve AI product wording to one canonical database product using safe identity signals."""
    product_profile = requirement_profile.get("product") or {}
    extracted_name = _norm(product_profile.get("name", ""))
    extracted_subcategory = _norm(product_profile.get("subcategory", ""))
    full_identity = _identity_text(requirement_profile, original_text)
    full_tokens = _tokens(full_identity)

    ranked: list[tuple[int, dict[str, Any], list[str], str | None]] = []
    for product in products or []:
        aliases = [product.get("productName")] + list(product.get("aliases") or [])
        best = 0
        signals: list[str] = []
        matched_alias: str | None = None
        for raw_alias in aliases:
            if not raw_alias:
                continue
            alias = _norm(raw_alias)
            if not alias or alias in MATERIAL_TERMS:
                continue
            alias_tokens = _tokens(alias)
            alias_identity = _identity_tokens(alias)
            if extracted_name and extracted_name == alias:
                score = 120 if _norm(product.get("productName")) == alias else 116
                sig = "PRODUCT_NAME_MATCH" if score == 120 else "PRODUCT_ALIAS_MATCH"
            elif extracted_subcategory and extracted_subcategory == alias:
                score = 112
                sig = "SUBCATEGORY_MATCH"
            elif _contains_phrase(full_identity, alias):
                score = 108 if len(alias_tokens) > 1 else 94
                sig = "PRODUCT_ALIAS_MATCH"
            elif alias_identity:
                coverage = len(alias_identity & full_tokens) / max(1, len(alias_identity))
                # Require almost all distinctive alias tokens. This supports phrases such as
                # "portable emergency fire suppression extinguisher" without turning a shared
                # word like "fire" or "water" into product identity.
                if coverage >= 0.8:
                    score = 86 + min(10, len(alias_identity) * 2)
                    sig = "PRODUCT_ALIAS_MATCH"
                else:
                    continue
            else:
                continue
            if score > best:
                best = score
                signals = [sig]
                matched_alias = str(raw_alias)

        # Product-family text emitted by an upstream model can also identify a product,
        # but only when it exactly normalizes to a database family.
        emitted_family = product_profile.get("productFamily") or requirement_profile.get("canonicalProductFamily")
        db_family = str(product.get("productFamily") or "")
        if emitted_family and _norm(str(emitted_family).replace("_", " ")) == _norm(db_family.replace("_", " ")):
            if best < 118:
                best = 118
                signals = ["PRODUCT_FAMILY_MATCH"]
                matched_alias = db_family

        if best:
            ranked.append((best, product, signals, matched_alias))

    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked or ranked[0][0] < 90:
        return None, {
            "resolved": False,
            "normalizedInputProduct": extracted_name,
            "normalizedSubcategory": extracted_subcategory,
            "matchedAlias": None,
            "signals": [],
            "candidateCount": len(ranked),
        }

    score, product, signals, matched_alias = ranked[0]
    return product, {
        "resolved": True,
        "score": score,
        "normalizedInputProduct": extracted_name,
        "normalizedSubcategory": extracted_subcategory,
        "matchedAlias": matched_alias,
        "signals": signals,
        "productId": product.get("productId") or product.get("documentId"),
        "productName": product.get("productName"),
        "productFamily": product.get("productFamily"),
        "primaryStandardId": product.get("primaryStandardId"),
        "linkedStandards": list(product.get("linkedStandards") or []),
    }


def resolve_product_family(requirement_profile: dict[str, Any], original_text: str, cases: list[dict[str, Any]] | None = None) -> str | None:
    """Resolve to one canonical product family, preferring canonical Firestore products."""
    products = _case_products(cases)
    resolved, _ = resolve_canonical_product(requirement_profile, original_text, products)
    if resolved and resolved.get("productFamily"):
        return str(resolved["productFamily"])

    identity = _identity_text(requirement_profile, original_text)

    # Deterministic fallback identities retain safe behavior when DEMO Firestore is unavailable.
    pipe_identity = any(_contains_phrase(identity, p) for p in ["pipe", "pipes", "water pipe", "pvc pipe", "upvc pipe", "unplasticized pvc pipe"])
    pvc_context = any(_contains_phrase(identity, p) for p in ["pvc", "upvc", "unplasticized pvc", "potable water"])
    if pipe_identity and pvc_context:
        return "PVC_WATER_PIPE"

    fallback = [
        ("STRUCTURAL_STEEL_PLATE", ["structural steel plate", "steel plate", "structural steel"]),
        ("CEILING_FAN", ["ceiling fan", "electric ceiling fan"]),
        ("ELECTRICAL_CABLE", ["electrical cable", "electric cable", "pvc insulated cable", "building wire", "cable"]),
        ("WATER_TANK", ["water storage tank", "water tank", "polyethylene water tank", "rotomoulded water tank", "rotational moulded water tank"]),
    ]
    for family, aliases in fallback:
        if any(_contains_phrase(identity, alias) for alias in aliases):
            return family

    # Shared standard aliases can still resolve families if no product record was supplied.
    for case in cases or []:
        family = str(case.get("productFamily") or "").strip()
        for alias in case.get("identityAliases") or []:
            normalized = _norm(alias)
            if not normalized or normalized in MATERIAL_TERMS:
                continue
            alias_identity = _identity_tokens(normalized)
            if _contains_phrase(identity, normalized) or (alias_identity and len(alias_identity & _tokens(identity)) / len(alias_identity) >= 0.8):
                return family or None
    return None


def _matched_evidence(case: dict[str, Any], requirement_profile: dict[str, Any], original_text: str) -> list[dict[str, str]]:
    profile_text = _profile_text(requirement_profile)
    matches: list[dict[str, str]] = []
    seen: set[str] = set()
    for term in case["standard"].get("evidenceTerms", []):
        key = _norm(term)
        if not key or key in seen or key in MATERIAL_TERMS:
            continue
        if _contains_phrase(original_text, term):
            matches.append({"text": term, "source": "INPUT_TEXT"})
            seen.add(key)
        elif _contains_phrase(profile_text, term):
            matches.append({"text": term, "source": "REQUIREMENT_PROFILE"})
            seen.add(key)
    return matches


def _supporting_match(query: Any, options: list[str]) -> bool:
    query_tokens = _identity_tokens(query)
    if not query_tokens or not options:
        return False
    for option in options:
        opt_tokens = _identity_tokens(option)
        if not opt_tokens:
            continue
        if _contains_phrase(str(query), option) or _contains_phrase(option, str(query)):
            return True
        overlap = len(query_tokens & opt_tokens) / max(1, min(len(query_tokens), len(opt_tokens)))
        if overlap >= 0.6:
            return True
    return False


def recommend_demo_standards(
    requirement_profile: dict[str, Any], original_text: str, cases: list[dict[str, Any]] | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
    """Strict product-first retrieval with category/application as supporting evidence."""
    active_cases = cases if cases is not None else DEMO_CASES
    products = _case_products(active_cases)
    canonical_product, product_resolution = resolve_canonical_product(requirement_profile, original_text, products)
    family = str(canonical_product.get("productFamily")) if canonical_product and canonical_product.get("productFamily") else resolve_product_family(requirement_profile, original_text, active_cases)

    candidates: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    product = requirement_profile.get("product") or {}
    category_text = f"{product.get('category', '')} {product.get('subcategory', '')}"
    application_text = _flatten(requirement_profile.get("application") or {})

    for case in active_cases:
        standard = case["standard"]
        candidate_family = str(case.get("productFamily") or "")
        product_compatible = family is not None and family == candidate_family
        diagnostic: dict[str, Any] = {
            "standardId": standard["standardId"],
            "requirementProductFamily": family,
            "candidateProductFamily": candidate_family,
            "canonicalProductId": (canonical_product or {}).get("productId") or (canonical_product or {}).get("documentId"),
            "canonicalProductName": (canonical_product or {}).get("productName"),
            "matchedAlias": product_resolution.get("matchedAlias"),
            "productCompatible": product_compatible,
            "categoryCompatible": False,
            "scopeCompatible": False,
            "matchedTerms": [],
            "compatibilitySignals": [],
            "rejectedTerms": [],
            "rejectReason": None,
            "rawScore": None,
            "finalScore": None,
        }
        if not product_compatible:
            diagnostic["rejectReason"] = "PRODUCT_FAMILY_MISMATCH" if family else "PRODUCT_FAMILY_UNRESOLVED"
            diagnostics.append(diagnostic)
            continue

        category_compatible = _supporting_match(category_text, list(case.get("categories", [])) + list(case.get("subcategories", [])))
        application_compatible = _supporting_match(application_text, list(case.get("applications", [])))
        diagnostic["categoryCompatible"] = category_compatible
        diagnostic["scopeCompatible"] = application_compatible

        signals: list[str] = []
        if canonical_product:
            signals.append("CANONICAL_PRODUCT_MATCH")
            if product_resolution.get("matchedAlias"):
                signals.append("PRODUCT_ALIAS_MATCH")
        signals.append("PRODUCT_FAMILY_MATCH")
        if _supporting_match(product.get("subcategory", ""), list(case.get("subcategories", []))):
            signals.append("SUBCATEGORY_MATCH")
        if category_compatible:
            signals.append("CATEGORY_COMPATIBLE")
        if application_compatible:
            signals.append("APPLICATION_MATCH")
        if canonical_product and standard.get("standardId") in set([canonical_product.get("primaryStandardId")] + list(canonical_product.get("linkedStandards") or [])):
            signals.append("PRIMARY_STANDARD_LINK")

        # Category is deliberately NOT a hard exact-string rejection. Strong canonical
        # product identity + family equality wins over synonymous AI category wording.
        evidence = _matched_evidence(case, requirement_profile, original_text)
        if evidence:
            signals.append("TECHNICAL_TERM_MATCH")
        diagnostic["matchedTerms"] = [item["text"] for item in evidence]
        diagnostic["compatibilitySignals"] = list(dict.fromkeys(signals))

        base = int(standard.get("confidenceBase", 75))
        raw_score = base + min(9, len(evidence) * 3)
        raw_score += 5 if canonical_product else 0
        raw_score += 3 if category_compatible else 0
        raw_score += 3 if application_compatible else 0
        raw_score += 4 if "PRIMARY_STANDARD_LINK" in signals else 0
        score = min(97, raw_score)
        diagnostic["rawScore"] = raw_score
        diagnostic["finalScore"] = score
        diagnostics.append(diagnostic)

        candidates.append({
            "standardId": standard["standardId"],
            "isNumber": standard["isNumber"],
            "title": standard["title"],
            "category": standard["category"],
            "status": standard["status"],
            "confidence": score,
            "certification": case["certifications"][0].get("type", "Needs Review") if case.get("certifications") else "Needs Review",
            "matchedEvidence": evidence,
            "compatibilitySignals": list(dict.fromkeys(signals)),
            "dataMode": case.get("dataMode", "DEMO"),
            "caseId": case["caseId"],
            "productFamily": candidate_family,
            "canonicalProductId": (canonical_product or {}).get("productId") or (canonical_product or {}).get("documentId") or case.get("productId"),
            "canonicalProductName": (canonical_product or {}).get("productName") or case.get("productName"),
        })

    candidates.sort(key=lambda item: item["confidence"], reverse=True)
    return candidates[:5], diagnostics, family


def expand_demo_case(primary_standard_id: str | None, cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not primary_standard_id:
        return {"alliedStandards": [], "versionChecks": [], "certifications": [], "qcos": []}
    active_cases = cases if cases is not None else DEMO_CASES
    for case in active_cases:
        if case["standard"]["standardId"] == primary_standard_id:
            version = dict(case.get("version") or {})
            return {
                "alliedStandards": list(case.get("relationships") or []),
                "versionChecks": [version] if version else [],
                "certifications": list(case.get("certifications") or []),
                "qcos": list(case.get("qcos") or []),
            }
    return {"alliedStandards": [], "versionChecks": [], "certifications": [], "qcos": []}
