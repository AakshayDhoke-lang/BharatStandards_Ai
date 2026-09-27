from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from .firebase_service import firebase_admin_configured, get_firestore_client

DATASET_COLLECTIONS = (
    "categories",
    "products",
    "standards",
    "relationships",
    "certifications",
    "qcos",
    "amendments",
    "sources",
)


def list_dataset_records(dataset: str, collection_name: str) -> list[dict[str, Any]]:
    """Read one shared knowledge collection from the selected dataset."""
    if not firebase_admin_configured():
        return []
    db = get_firestore_client()
    rows: list[dict[str, Any]] = []
    for snap in db.collection("datasets").document(dataset.lower()).collection(collection_name).stream():
        data = snap.to_dict() or {}
        data.setdefault("documentId", snap.id)
        rows.append(data)
    return rows


def load_dataset_knowledge(dataset: str) -> dict[str, list[dict[str, Any]]]:
    """Load the collections needed by deterministic recommendation in one consistent dataset.

    DEMO and REAL use the exact same collection names.  No REAL -> DEMO fallback happens here.
    """
    return {name: list_dataset_records(dataset, name) for name in DATASET_COLLECTIONS}


def _family(value: Any) -> str:
    text = str(value or "").upper().strip().replace("&", " AND ")
    return re.sub(r"[^A-Z0-9]+", "_", text).strip("_")


def _standard_id(row: dict[str, Any]) -> str:
    identity = row.get("identity") if isinstance(row.get("identity"), dict) else {}
    return str(row.get("standardId") or identity.get("designation") or row.get("documentId") or "")


def _relationship_for_standard(row: dict[str, Any], standard_id: str) -> bool:
    source_id = row.get("fromStandardId") or row.get("sourceStandardId") or row.get("standardId")
    return str(source_id or "") == standard_id


def _relationship_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "relationshipId": row.get("relationshipId") or row.get("documentId"),
        "sourceId": row.get("sourceId"),
        "verificationStatus": row.get("verificationStatus"),
        "datasetMode": row.get("datasetMode") or row.get("dataMode"),
        "standard": row.get("toStandard") or row.get("targetStandard") or row.get("targetStandardId") or "—",
        "standardId": row.get("toStandardId") or row.get("targetStandardId"),
        "title": row.get("toTitle") or row.get("targetTitle") or row.get("title") or "Related standard",
        "relationship": row.get("relationshipType") or row.get("relationship") or "RELATED",
        "applicability": row.get("applicability") or "Applicable",
        "mandatory": row.get("mandatory") if "mandatory" in row else row.get("mandatoryForCompliance", "Needs Review"),
        "reason": row.get("reason") or "Shared relationship record",
        "status": row.get("status") or row.get("verificationStatus") or "UNKNOWN",
    }


def build_matcher_cases(knowledge: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Join shared product/standard/regulatory records into matcher cases.

    Standards remain the source of standard identity. Products provide canonical product identity,
    aliases and primary/linked-standard mappings. Regulatory/version/relationship records are
    looked up from their authoritative shared collections instead of requiring them to be embedded
    in the standard document.
    """
    standards = knowledge.get("standards", [])
    products = knowledge.get("products", [])
    relationships = knowledge.get("relationships", [])
    certifications = knowledge.get("certifications", [])
    qcos = knowledge.get("qcos", [])
    amendments = knowledge.get("amendments", [])

    products_by_standard: dict[str, list[dict[str, Any]]] = defaultdict(list)
    products_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for product in products:
        product_family = _family(product.get("productFamily"))
        if product_family:
            products_by_family[product_family].append(product)
        linked = list(product.get("linkedStandards") or [])
        primary = product.get("primaryStandardId")
        if primary and primary not in linked:
            linked.append(primary)
        for standard_id in linked:
            if standard_id:
                products_by_standard[str(standard_id)].append(product)

    cases: list[dict[str, Any]] = []
    for row in standards:
        classification = row.get("classification") if isinstance(row.get("classification"), dict) else {}
        search = row.get("search") if isinstance(row.get("search"), dict) else {}
        scope = row.get("scope") if isinstance(row.get("scope"), dict) else {}
        standard_id = _standard_id(row)
        if not standard_id:
            continue

        product_group = row.get("productFamily") or classification.get("productGroup")
        product_family = _family(product_group)
        matched_products = products_by_standard.get(standard_id, []) or products_by_family.get(product_family, [])
        product = matched_products[0] if matched_products else None
        if not product_family and product:
            product_family = _family(product.get("productFamily"))
        if not product_family:
            # A standard without a canonical product identity is intentionally not eligible
            # for deterministic primary-product matching.
            continue

        standard = row.get("standard") if isinstance(row.get("standard"), dict) else {
            "standardId": standard_id,
            "isNumber": row.get("isNumber") or row.get("identity", {}).get("designation") or standard_id,
            "title": row.get("title") or "Untitled standard",
            "category": row.get("category") or classification.get("category") or "Unclassified",
            "status": row.get("status", {}).get("state") if isinstance(row.get("status"), dict) else row.get("status", "UNKNOWN"),
            "confidenceBase": row.get("confidenceBase", 75),
            "evidenceTerms": row.get("evidenceTerms") or search.get("keywords") or [],
        }

        identity_aliases: list[str] = []
        for source in (
            row.get("identityAliases") or [],
            search.get("aliases") or [],
            scope.get("includedProducts") or [],
            (product or {}).get("aliases") or [],
            [(product or {}).get("productName")] if product else [],
        ):
            for value in source:
                if value and str(value) not in identity_aliases:
                    identity_aliases.append(str(value))

        categories = [x for x in (row.get("categories") or []) if x]
        if not categories:
            categories = [row.get("category") or classification.get("category") or ""]
        if product and product.get("category") and product.get("category") not in categories:
            categories.append(product.get("category"))

        applications = list(row.get("applications") or scope.get("applications") or [])
        if product:
            for app in product.get("applications") or []:
                if app not in applications:
                    applications.append(app)

        standalone_relationships = [_relationship_view(r) for r in relationships if _relationship_for_standard(r, standard_id)]
        relation_records = standalone_relationships or list(row.get("relationships") or [])

        cert_records = [c for c in certifications if str(c.get("standardId") or "") == standard_id]
        if product:
            product_id = str(product.get("productId") or product.get("documentId") or "")
            cert_records.extend(c for c in certifications if product_id and str(c.get("productId") or "") == product_id and c not in cert_records)
        if not cert_records:
            cert_records = list(row.get("certifications") or [])

        qco_records = [q for q in qcos if standard_id in [str(x) for x in (q.get("standardIds") or [])] or str(q.get("standardId") or "") == standard_id]
        if product:
            product_id = str(product.get("productId") or product.get("documentId") or "")
            qco_records.extend(q for q in qcos if product_id and product_id in [str(x) for x in (q.get("productIds") or [])] and q not in qco_records)
        if not qco_records:
            qco_records = list(row.get("qcos") or [])

        version_records = [v for v in amendments if str(v.get("standardId") or "") == standard_id]
        version = dict(version_records[0]) if version_records else dict(row.get("version") or {})

        cases.append({
            "caseId": row.get("caseId") or row.get("documentId") or standard_id,
            "dataMode": row.get("dataMode") or row.get("datasetMode") or "DEMO",
            "productFamily": product_family,
            "product": product,
            "productId": (product or {}).get("productId") or (product or {}).get("documentId"),
            "productName": (product or {}).get("productName"),
            "primaryStandardId": (product or {}).get("primaryStandardId"),
            "linkedStandards": list((product or {}).get("linkedStandards") or []),
            "identityAliases": identity_aliases or [str(product_group)],
            "categories": [x for x in categories if x],
            "subcategories": [x for x in (row.get("subcategories") or [classification.get("subcategory") or ""]) if x],
            "applications": applications,
            "materials": row.get("materials") or (product or {}).get("materials") or [],
            "standard": standard,
            "standardRecord": row,
            "relationships": relation_records,
            "version": version,
            "certifications": cert_records,
            "qcos": qco_records,
        })
    return cases



def build_knowledge_evidence_bundle(*, dataset: str, knowledge: dict[str, list[dict[str, Any]]],
                                    canonical_product: dict[str, Any] | None,
                                    primary_standard: dict[str, Any] | None,
                                    matcher_cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build one authoritative evidence snapshot from the already-loaded active dataset.

    No Firestore reads happen here.  The function only selects records from ``knowledge`` that
    were loaded for the current DEMO/REAL dataset, so recommendation, coverage, UI, save and PDF
    can all refer to one consistent snapshot.
    """
    sid = str((primary_standard or {}).get("standardId") or "")
    pid = str((canonical_product or {}).get("productId") or (canonical_product or {}).get("documentId") or "")

    primary_case = next((
        case for case in (matcher_cases or [])
        if sid and str((case.get("standard") or {}).get("standardId") or "") == sid
    ), None)

    standard_record = (primary_case or {}).get("standardRecord")
    if not isinstance(standard_record, dict) and sid:
        standard_record = next((r for r in knowledge.get("standards", []) if _standard_id(r) == sid), None)

    product_record = canonical_product if isinstance(canonical_product, dict) else None
    if pid and knowledge.get("products"):
        product_record = next((
            r for r in knowledge.get("products", [])
            if str(r.get("productId") or r.get("documentId") or "") == pid
        ), product_record)

    relationship_records = [r for r in knowledge.get("relationships", []) if sid and _relationship_for_standard(r, sid)]
    relationships = [_relationship_view(r) for r in relationship_records]
    if not relationships and isinstance(standard_record, dict):
        relationships = list(standard_record.get("relationships") or [])

    certifications = [
        c for c in knowledge.get("certifications", [])
        if (sid and str(c.get("standardId") or "") == sid)
        or (pid and str(c.get("productId") or "") == pid)
    ]
    if not certifications and isinstance(standard_record, dict):
        certifications = list(standard_record.get("certifications") or [])

    qcos = [
        q for q in knowledge.get("qcos", [])
        if (sid and (str(q.get("standardId") or "") == sid or sid in [str(x) for x in (q.get("standardIds") or [])]))
        or (pid and (str(q.get("productId") or "") == pid or pid in [str(x) for x in (q.get("productIds") or [])]))
    ]
    if not qcos and isinstance(standard_record, dict):
        qcos = list(standard_record.get("qcos") or [])

    version_records = [v for v in knowledge.get("amendments", []) if sid and str(v.get("standardId") or "") == sid]
    version = next((v for v in version_records if str(v.get("recordType") or "").upper() == "VERSION_STATUS"), None)
    if version is None and version_records:
        version = version_records[0]
    if version is None and isinstance(standard_record, dict) and isinstance(standard_record.get("version"), dict):
        version = dict(standard_record.get("version") or {})

    amendment_records = [
        v for v in version_records
        if str(v.get("recordType") or "").upper() not in {"", "VERSION_STATUS"}
    ]
    if not amendment_records and isinstance(version, dict) and isinstance(version.get("amendments"), list):
        amendment_records = list(version.get("amendments") or [])

    source_ids: list[str] = []
    for record in [product_record, standard_record, *relationship_records, *certifications, *qcos, *(version_records or [])]:
        if not isinstance(record, dict):
            continue
        provenance = record.get("provenance") if isinstance(record.get("provenance"), dict) else {}
        source_id = record.get("sourceId") or provenance.get("sourceId")
        if source_id and str(source_id) not in source_ids:
            source_ids.append(str(source_id))

    provenance = {
        "datasetMode": dataset.upper(),
        "productId": pid or None,
        "productFamily": (product_record or {}).get("productFamily") if isinstance(product_record, dict) else None,
        "primaryStandardId": sid or None,
        "relationshipIds": [str(r.get("relationshipId") or r.get("documentId")) for r in relationship_records if r.get("relationshipId") or r.get("documentId")],
        "certificationIds": [str(c.get("certificationId") or c.get("documentId")) for c in certifications if c.get("certificationId") or c.get("documentId")],
        "qcoIds": [str(q.get("qcoId") or q.get("documentId")) for q in qcos if q.get("qcoId") or q.get("documentId")],
        "versionRecordId": (version or {}).get("versionRecordId") or (version or {}).get("documentId") if isinstance(version, dict) else None,
        "amendmentIds": [str(a.get("amendmentId") or a.get("documentId")) for a in amendment_records if isinstance(a, dict) and (a.get("amendmentId") or a.get("documentId"))],
        "sourceIds": source_ids,
    }

    return {
        "datasetMode": dataset.upper(),
        "canonicalProduct": product_record,
        "primaryStandard": primary_standard,
        "primaryStandardRecord": standard_record,
        "relationships": relationships,
        "certifications": certifications,
        "qcos": qcos,
        "version": version,
        "versionRecords": version_records,
        "amendments": amendment_records,
        "provenance": provenance,
    }

def list_matcher_cases(dataset: str, knowledge: dict[str, list[dict[str, Any]]] | None = None) -> list[dict[str, Any]]:
    return build_matcher_cases(knowledge or load_dataset_knowledge(dataset))
