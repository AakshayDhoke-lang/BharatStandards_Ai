from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .demo_engine import recommend_demo_standards, resolve_canonical_product
from .document_processing import parse_document_bytes
from .coverage import evaluate_standard_coverage
from .bis_intelligence_service import get_bis_intelligence, verify_model_candidates
from .nvidia_service import (
    extract_requirement_profile,
    extract_standard_candidate,
    get_base_url,
    get_provider,
    is_vercel_runtime,
    list_lm_studio_models,
    set_provider,
    test_ai_connection,
)
from .firebase_service import firebase_admin_configured, firestore_health
from .standards_repository import build_knowledge_evidence_bundle, list_matcher_cases, load_dataset_knowledge

load_dotenv()
app = FastAPI(title="BharatStandards AI API", version="0.4.0")
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://bharatstandards-ai.web.app",
    "https://bharatstandards-ai.firebaseapp.com",
]
extra_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
allowed_origins = list(dict.fromkeys(default_origins + extra_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    provider = get_provider()
    return {
        "status": "ok",
        "service": "bharatstandards-ai-api",
        "documentParser": "lightweight",
        "parsers": ["PyMuPDF", "python-docx", "openpyxl", "python-pptx", "native text/csv/html"],
        "aiProvider": provider,
        "aiBaseUrl": get_base_url(provider),
        "nvidiaConfigured": bool(os.getenv("NVIDIA_API_KEY")),
        "lmStudioBaseUrl": get_base_url("lmstudio"),
        "dataMode": "DEMO" if os.getenv("DEMO_MODE", "false").lower() == "true" else "REAL",
        "runtime": "vercel" if is_vercel_runtime() else "local",
        "firestoreAdminConfigured": firebase_admin_configured(),
    }




@app.get("/api/firestore/health")
def firestore_connection_health():
    result = firestore_health()
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result)
    return result


@app.get("/api/ai/test")
async def ai_test():
    try:
        return await test_ai_connection()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/ai/lmstudio/models")
async def lmstudio_models():
    try:
        models = await list_lm_studio_models()
        return {"ok": True, "baseUrl": get_base_url("lmstudio"), "models": models, "activeModel": models[0]}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class ProviderSelection(BaseModel):
    provider: str


@app.get("/api/ai/provider")
def ai_provider():
    return {"provider": get_provider(), "baseUrl": get_base_url()}


@app.post("/api/ai/provider")
def ai_provider_update(payload: ProviderSelection):
    try:
        provider = set_provider(payload.provider)
        return {"ok": True, "provider": provider, "baseUrl": get_base_url(provider)}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/documents/parse")
async def parse_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file name is required.")
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Maximum upload size is 50 MB.")
    try:
        return parse_document_bytes(file.filename, content)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {type(exc).__name__}: {exc}") from exc




class StandardCandidateText(BaseModel):
    text: str
    source_name: str | None = None


@app.post("/api/ingestion/extract-standard")
async def ingestion_extract_standard(payload: StandardCandidateText):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Extracted standards document text is empty.")
    try:
        candidate, ai_meta = await extract_standard_candidate(payload.text, payload.source_name)
        return {"candidate": candidate, "provider": ai_meta["provider"], "model": ai_meta["model"], "latencyMs": ai_meta["latencyMs"]}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

class RequirementText(BaseModel):
    text: str
    source_name: str | None = None
    language: str = "en"
    demo_mode: bool | None = None
    input_type: str = "TEXT"


@app.post("/api/ai/requirement-profile")
async def requirement_profile(payload: RequirementText):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")
    try:
        profile, ai_meta = await extract_requirement_profile(payload.text, payload.language)
        return {
            "requirementProfile": profile,
            "provider": ai_meta["provider"],
            "model": ai_meta["model"],
            "inputCharacters": len(payload.text),
            "sourceName": payload.source_name,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc



@app.get("/api/ml/health")
def bis_model_health():
    return get_bis_intelligence().health()


@app.post("/api/ml/recommend-standard")
def bis_model_recommend(profile: dict):
    # Direct custom-model test endpoint. It never calls NVIDIA or LM Studio.
    return get_bis_intelligence().recommend_standard(profile)


@app.post("/api/analysis/run")
async def run_analysis(payload: RequirementText):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Extracted procurement text is empty.")
    try:
        profile, ai_meta = await extract_requirement_profile(text, payload.language)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    demo_mode = payload.demo_mode if payload.demo_mode is not None else os.getenv("DEMO_MODE", "false").lower() == "true"
    dataset_name = "demo" if demo_mode else "real"
    shared_cases: list[dict] = []
    knowledge: dict[str, list[dict]] = {}
    dataset_error: str | None = None
    try:
        knowledge = load_dataset_knowledge(dataset_name)
        shared_cases = list_matcher_cases(dataset_name, knowledge)
    except Exception as exc:
        # Analysis remains available during a transient Firestore outage in DEMO only.
        # REAL mode never falls back to demo knowledge.
        shared_cases = []
        knowledge = {}
        dataset_error = str(exc)

    # Runtime analysis is Firestore-authoritative in both DEMO and REAL. Built-in DEMO_CASES
    # remain available to unit tests/development utilities, but are never a silent production
    # fallback when the selected Firestore dataset is empty or unavailable.
    active_cases = shared_cases
    recommendations, candidate_diagnostics, canonical_product_family = (
        recommend_demo_standards(profile, text, active_cases) if active_cases else ([], [], None)
    )

    active_products = knowledge.get("products", []) if shared_cases else []
    canonical_product, product_resolution = resolve_canonical_product(profile, text, active_products)

    # BIS Intelligence runs after NLP extraction. Shadow mode preserves the legacy recommendation
    # while logging/returning the custom model comparison. Cutover is feature-flagged and still
    # requires canonical-product + Firestore verification before any custom candidate can win.
    bis_enabled = os.getenv("BIS_MODEL_ENABLED", "false").lower() == "true"
    bis_shadow = os.getenv("BIS_MODEL_SHADOW_MODE", "true").lower() == "true"
    bis_raw = get_bis_intelligence().recommend_standard(profile) if (bis_enabled or bis_shadow) else {"decision": "MODEL_UNAVAILABLE", "candidates": [], "primaryCandidate": None, "model": {"name": "BIS Intelligence", "version": "disabled"}}
    bis_verified = verify_model_candidates(bis_raw, canonical_product, knowledge.get("standards", [])) if shared_cases else {"decision": bis_raw.get("decision"), "verifiedCandidates": [], "rejectedCandidates": [], "primaryCandidate": None}
    legacy_primary = recommendations[0] if recommendations else None
    custom_primary = bis_verified.get("primaryCandidate")
    custom_standard_id = str((custom_primary or {}).get("standardId") or "")
    custom_case = next((c for c in active_cases if str((c.get("standard") or {}).get("standardId") or c.get("standardId") or "") == custom_standard_id), None)
    if bis_enabled and bis_verified.get("decision") == "MATCH" and custom_case:
        # Reuse the existing matcher result object shape; do not let the ML service fabricate metadata.
        custom_recs, custom_diags, custom_family = recommend_demo_standards(profile, text, [custom_case])
        if custom_recs:
            recommendations, candidate_diagnostics, canonical_product_family = custom_recs, custom_diags, custom_family
    primary = recommendations[0] if recommendations else None
    legacy_id = str((legacy_primary or {}).get("standardId") or "")
    final_id = str((primary or {}).get("standardId") or "")
    custom_id = custom_standard_id
    bis_intelligence = {
        "modelName": (bis_raw.get("model") or {}).get("name", "BIS Intelligence"),
        "modelVersion": (bis_raw.get("model") or {}).get("version", "untrained"),
        "predictedDomain": (bis_raw.get("domain") or {}).get("predicted"),
        "domainScore": (bis_raw.get("domain") or {}).get("score"),
        "decision": bis_verified.get("decision") or bis_raw.get("decision"),
        "primaryCandidate": custom_primary,
        "candidates": bis_raw.get("candidates") or [],
        "verifiedCandidates": bis_verified.get("verifiedCandidates") or [],
        "rejectedCandidates": bis_verified.get("rejectedCandidates") or [],
        "legacyAgreement": bool(custom_id and legacy_id and custom_id == legacy_id),
        "shadowMode": bool(bis_shadow and not bis_enabled),
        "enabled": bis_enabled,
        "embeddingModel": bis_raw.get("embeddingModel"),
        "trainingDatasetVersion": bis_raw.get("trainingDatasetVersion"),
        "finalStandardId": final_id or None,
    }

    # Build one authoritative evidence snapshot from the active dataset that was already loaded
    # for matching. Coverage/result/save/PDF all consume this same snapshot; no second Firestore
    # lookup or previous-analysis fallback is used.
    if shared_cases:
        knowledge_bundle = build_knowledge_evidence_bundle(
            dataset=dataset_name, knowledge=knowledge, canonical_product=canonical_product,
            primary_standard=primary, matcher_cases=active_cases,
        )
    else:
        knowledge_bundle = {
            "datasetMode": dataset_name.upper(), "canonicalProduct": canonical_product, "primaryStandard": primary,
            "primaryStandardRecord": None, "relationships": [], "certifications": [], "qcos": [],
            "version": None, "versionRecords": [], "amendments": [],
            "provenance": {"datasetMode": dataset_name.upper(), "source": "FIRESTORE_EMPTY_OR_UNAVAILABLE",
                "productId": None, "productFamily": canonical_product_family, "primaryStandardId": None,
                "relationshipIds": [], "certificationIds": [], "qcoIds": [], "versionRecordId": None,
                "amendmentIds": [], "sourceIds": []},
        }

    expanded = {
        "alliedStandards": list(knowledge_bundle.get("relationships") or []),
        "versionChecks": list(knowledge_bundle.get("versionRecords") or ([knowledge_bundle.get("version")] if knowledge_bundle.get("version") else [])),
        "certifications": list(knowledge_bundle.get("certifications") or []),
        "qcos": list(knowledge_bundle.get("qcos") or []),
    }
    analysis_id = f"ANL-{uuid.uuid4().hex[:8].upper()}"
    input_id = f"INP-{uuid.uuid4().hex[:8].upper()}"

    # Evidence is deliberately scoped to this request only. No prior analysis state is consulted.
    evidence = [{
        "analysisId": analysis_id,
        "inputId": input_id,
        "sourceType": "Uploaded tender" if payload.input_type.upper() == "FILE" else "User-entered description",
        "text": text[:1200],
        "requirementKey": "current_input",
    }]

    # Coverage is deterministic and consumes the same authoritative evidence bundle used by
    # the rest of the result. Search aliases/keywords remain retrieval-only evidence.
    coverage = evaluate_standard_coverage(requirement_profile=profile, knowledge_bundle=knowledge_bundle)

    warnings: list[dict[str, str]] = []
    if not recommendations:
        warnings.append({
            "code": "NO_COMPATIBLE_DEMO_STANDARD" if demo_mode else "REAL_DATASET_NOT_CONFIGURED",
            "severity": "WARNING",
            "message": "No product-compatible standard exists in the active demo dataset." if demo_mode else "DEMO mode is disabled and no verified REAL dataset is configured yet.",
        })
    if primary and not expanded["alliedStandards"]:
        warnings.append({"code": "NO_ALLIED_STANDARD_RECORD", "severity": "WARNING", "message": "No verified allied standards are available for this standard in the current knowledge base."})
    if primary and not expanded["certifications"]:
        warnings.append({"code": "NO_CERTIFICATION_RECORD", "severity": "WARNING", "message": "No verified certification/QCO record was found for the current product in the active knowledge base."})

    certification_requested = bool((profile.get("certification") or {}).get("requested"))
    certification_summary = {
        "tenderRequestsCertificationEvidence": certification_requested,
        "certificationMandatory": expanded["certifications"][0].get("mandatory") if expanded["certifications"] else None,
        "status": expanded["certifications"][0].get("status", "NEEDS_REVIEW") if expanded["certifications"] else "NEEDS_REVIEW",
    }

    return {
        "analysisId": analysis_id,
        "inputId": input_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sourceName": payload.source_name,
        "provider": ai_meta["provider"],
        "model": ai_meta["model"],
        "dataMode": "DEMO" if demo_mode else "REAL",
        "input": {"type": payload.input_type.upper(), "inputId": input_id},
        "requirementProfile": profile,
        "canonicalProductFamily": canonical_product_family,
        "canonicalProduct": {
            "productId": (canonical_product or {}).get("productId") or (canonical_product or {}).get("documentId"),
            "productName": (canonical_product or {}).get("productName"),
            "productFamily": (canonical_product or {}).get("productFamily") or canonical_product_family,
            "primaryStandardId": (canonical_product or {}).get("primaryStandardId"),
            "linkedStandards": list((canonical_product or {}).get("linkedStandards") or []),
        } if canonical_product else None,
        "productResolution": product_resolution,
        "datasetDiagnostics": {
            "dataset": dataset_name.upper(),
            "source": "FIRESTORE" if shared_cases else "FIRESTORE_EMPTY_OR_UNAVAILABLE",
            "productsLoaded": len(knowledge.get("products", [])),
            "standardsLoaded": len(knowledge.get("standards", [])),
            "certificationsLoaded": len(knowledge.get("certifications", [])),
            "qcosLoaded": len(knowledge.get("qcos", [])),
            "versionsLoaded": len(knowledge.get("amendments", [])),
            "productId": (knowledge_bundle.get("provenance") or {}).get("productId"),
            "productFamily": (knowledge_bundle.get("provenance") or {}).get("productFamily"),
            "primaryStandardId": (knowledge_bundle.get("provenance") or {}).get("primaryStandardId"),
            "relationshipIds": (knowledge_bundle.get("provenance") or {}).get("relationshipIds") or [],
            "certificationIds": (knowledge_bundle.get("provenance") or {}).get("certificationIds") or [],
            "qcoIds": (knowledge_bundle.get("provenance") or {}).get("qcoIds") or [],
            "versionRecordId": (knowledge_bundle.get("provenance") or {}).get("versionRecordId"),
            "amendmentIds": (knowledge_bundle.get("provenance") or {}).get("amendmentIds") or [],
            "sourceIds": (knowledge_bundle.get("provenance") or {}).get("sourceIds") or [],
            "error": dataset_error,
        },
        "knowledgeEvidenceProvenance": knowledge_bundle.get("provenance") or {},
        "candidateDiagnostics": candidate_diagnostics,
        "bisIntelligence": bis_intelligence,
        "bisModelVersion": bis_intelligence.get("modelVersion"),
        "embeddingModel": bis_intelligence.get("embeddingModel"),
        "trainingDatasetVersion": bis_intelligence.get("trainingDatasetVersion"),
        "modelDecision": bis_intelligence.get("decision"),
        "modelTopCandidates": bis_intelligence.get("candidates"),
        "candidateStandards": recommendations,
        "recommendations": recommendations,
        "primaryStandard": primary,
        "alliedStandards": expanded["alliedStandards"],
        "versionChecks": expanded["versionChecks"],
        "certifications": expanded["certifications"],
        "qcos": expanded["qcos"],
        "certificationSummary": certification_summary,
        "coverage": coverage,
        "missingRequirements": [],
        "evidence": evidence,
        "warnings": warnings,
        "confidence": {"overall": primary.get("confidence") if primary else None},
        "status": "DEMO" if demo_mode and primary else "NEEDS_REVIEW",
        "pipeline": [
            {"stage": "INPUT_TEXT", "status": "PASS", "characters": len(text)},
            {"stage": "AI_NLP_EXTRACTION", "status": "PASS", "provider": ai_meta["provider"], "model": ai_meta["model"], "latencyMs": ai_meta["latencyMs"]},
            {"stage": "BIS_DOMAIN_CLASSIFIER", "status": "PASS" if bis_intelligence.get("predictedDomain") else ("SKIPPED" if not (bis_enabled or bis_shadow) else bis_intelligence.get("decision")), "model": bis_intelligence.get("modelVersion")},
            {"stage": "IS_CANDIDATE_RETRIEVAL", "status": "PASS" if bis_intelligence.get("candidates") else bis_intelligence.get("decision"), "candidates": len(bis_intelligence.get("candidates") or [])},
            {"stage": "IS_RANKER", "status": bis_intelligence.get("decision"), "candidates": len(bis_intelligence.get("candidates") or [])},
            {"stage": "CANONICAL_PRODUCT_VERIFICATION", "status": "PASS" if canonical_product else "NO_MATCH", "productFamily": canonical_product_family},
            {"stage": "FIRESTORE_STANDARD_VERIFICATION", "status": "PASS" if primary else "NO_MATCH", "candidates": len(recommendations)},
            {"stage": "EVIDENCE_ENRICHMENT", "status": "PASS" if knowledge_bundle.get("primaryStandard") else ("PASS" if primary else "NO_MATCH")},
            {"stage": "STANDARD_COVERAGE_EVALUATION", "status": "PASS" if coverage.get("evaluated") else "NOT_EVALUATED", "requirements": len(coverage.get("requirements") or [])},
        ],
    }
