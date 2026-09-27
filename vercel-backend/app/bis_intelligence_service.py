from __future__ import annotations

import json
import os
import platform
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "bis_intelligence_v2"
DEFAULT_TOP_K = 20


def _norm(value: Any) -> str:
    text = str(value or "").lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten(v) for v in value)
    return str(value or "")


def build_model_query(profile: dict[str, Any]) -> str:
    product = profile.get("product") or {}
    application = profile.get("application") or {}
    lines = [
        f"Product: {product.get('name','')}",
        f"Category: {product.get('category','')}",
        f"Subcategory: {product.get('subcategory','')}",
        f"Application: {application.get('useCase','')}",
        f"Environment: {application.get('environment','')}",
        f"Materials: {_flatten(profile.get('materials') or [])}",
        f"Dimensions: {_flatten(profile.get('dimensions') or {})}",
        f"Technical: {_flatten(profile.get('technicalProperties') or {})}",
        f"Performance: {_flatten(profile.get('performance') or {})}",
        f"Testing: {_flatten(profile.get('testing') or {})}",
        f"Safety: {_flatten(profile.get('safety') or {})}",
    ]
    return "\n".join(line for line in lines if line.split(":",1)[1].strip())


def _standard_id(row: dict[str, Any]) -> str:
    return str(row.get("standardId") or row.get("id") or row.get("documentId") or row.get("standard_number") or "")


def _is_number(row: dict[str, Any]) -> str:
    ident = row.get("identity") if isinstance(row.get("identity"), dict) else {}
    return str(row.get("isNumber") or row.get("standard_number") or ident.get("designation") or _standard_id(row))


def _family(row: dict[str, Any]) -> str:
    return _norm(row.get("productFamily") or row.get("product_family") or "").replace(" ", "_").upper()


def _token_overlap(a: str, b: str) -> float:
    aa=set(_norm(a).split()); bb=set(_norm(b).split())
    if not aa or not bb: return 0.0
    return len(aa & bb) / max(1, len(aa | bb))


class BISIntelligence:
    def __init__(self, model_dir: Path = MODEL_DIR):
        self.model_dir=model_dir
        self.available=False
        self.error: str|None=None
        self.metadata: dict[str, Any]={}
        self.index: list[dict[str, Any]]=[]
        self.embeddings=None
        self.category_classifier=None
        self.label_encoder: list[str]=[]
        self.ranker=None
        self.embedding_model=None
        self._load()

    def _load(self) -> None:
        required=["model_metadata.json","standard_index.json","retrieval_vectorizer.joblib","standard_matrix.joblib","category_classifier.joblib","ranker.joblib"]
        missing=[name for name in required if not (self.model_dir/name).exists()]
        if missing:
            self.error="Missing trained BIS Intelligence artifacts: "+", ".join(missing); return
        try:
            import joblib
            self.metadata=json.loads((self.model_dir/"model_metadata.json").read_text(encoding="utf-8"))
            self.index=json.loads((self.model_dir/"standard_index.json").read_text(encoding="utf-8"))
            self.vectorizer=joblib.load(self.model_dir/"retrieval_vectorizer.joblib")
            self.standard_matrix=joblib.load(self.model_dir/"standard_matrix.joblib")
            self.category_classifier=joblib.load(self.model_dir/"category_classifier.joblib")
            self.ranker=joblib.load(self.model_dir/"ranker.joblib")
            if len(self.index)!=self.standard_matrix.shape[0]: raise RuntimeError("standard index and matrix lengths differ")
            self.available=True
        except Exception as exc:
            self.error=f"BIS Intelligence artifact load failed: {exc}"; self.available=False

    def health(self) -> dict[str, Any]:
        return {
            "ok": self.available,
            "model": str(self.metadata.get("modelName") or "BIS Intelligence"),
            "version": str(self.metadata.get("modelVersion") or "untrained"),
            "python": platform.python_version(),
            "standardsIndexed": len(self.index),
            "embeddingModel": self.metadata.get("embeddingModel"),
            "trainingDatasetVersion": self.metadata.get("trainingDatasetVersion"),
            "error": self.error,
        }

    def _encode(self, text: str):
        if not self.available: raise RuntimeError(self.error or "BIS Intelligence model unavailable")
        return self.vectorizer.transform([text])

    def classify_domain(self, profile: dict[str, Any]) -> dict[str, Any]:
        if not self.available: return {"predicted":None,"score":None,"topCategories":[]}
        import numpy as np
        vec=self._encode(build_model_query(profile)); pred=str(self.category_classifier.predict(vec)[0]); top=[];score=None
        if hasattr(self.category_classifier,"predict_proba"):
            vals=np.asarray(self.category_classifier.predict_proba(vec))[0]; classes=[str(x) for x in self.category_classifier.classes_]; order=np.argsort(vals)[::-1]
            top=[{"category":classes[int(i)],"score":float(vals[int(i)])} for i in order[:3]]; score=top[0]["score"] if top else None
        return {"predicted":pred,"score":score,"topCategories":top}

    def retrieve_candidates(self, profile: dict[str, Any], top_k: int=DEFAULT_TOP_K) -> list[dict[str, Any]]:
        if not self.available: return []
        import numpy as np
        from sklearn.metrics.pairwise import linear_kernel
        q=self._encode(build_model_query(profile)); scores=linear_kernel(q,self.standard_matrix).ravel(); order=np.argsort(scores)[::-1]
        # Collapse duplicate revisions of the same base IS identity. The ML layer ranks
        # standard identity; Firestore remains authoritative for the active revision.
        groups={}
        for i in order:
            row=self.index[int(i)]; base=str(row.get("base_standard") or row.get("standard_number") or "")
            g=groups.setdefault(base,{"bestScore":float(scores[int(i)]),"members":[]}); g["members"].append(int(i)); g["bestScore"]=max(g["bestScore"],float(scores[int(i)]))
        ordered=sorted(groups.items(),key=lambda kv:kv[1]["bestScore"],reverse=True)[:max(1,int(top_k))]; out=[]
        for rank,(base,g) in enumerate(ordered,1):
            # Representative only; deterministic Firestore verification resolves legal/latest truth.
            i=max(g["members"],key=lambda j:int(self.index[j].get("version_year") or 0)); row=dict(self.index[i]); row.update({"standardId":row.get("standard_number"),"isNumber":row.get("standard_number"),"retrievalScore":float(g["bestScore"]),"rank":rank,"baseStandard":base}); out.append(row)
        return out

    def rank_candidates(self, profile: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        import numpy as np
        query=build_model_query(profile); domain=self.classify_domain(profile).get("predicted") or ""; ranked=[]
        for row in candidates:
            semantic=float(row.get("retrievalScore") or 0.0); title_overlap=_token_overlap(query,str(row.get("clean_title") or row.get("title") or "")); scope_overlap=_token_overlap(query,str(row.get("scope_abstract") or "")); alias_overlap=_token_overlap(query,str(row.get("aliases") or "")); category=float(_norm(domain)==_norm(row.get("category"))); active=1.0 if str(row.get("is_active",True)).lower() not in {"false","0","inactive"} else 0.0
            features=np.array([[semantic,title_overlap,scope_overlap,alias_overlap,category,active]],dtype=float); prob=float(self.ranker.predict_proba(features)[0][-1]); retrieval_norm=min(1.0,max(0.0,semantic/1.2)); confidence=0.60*prob+0.40*retrieval_norm
            item=dict(row); item["rankingScore"]=prob; item["decisionConfidence"]=confidence; item["matchedSignals"]=[k for k,v in {"RETRIEVAL":semantic,"TITLE":title_overlap,"SCOPE":scope_overlap,"ALIAS":alias_overlap,"DOMAIN":category,"ACTIVE":active}.items() if v>0.12]; ranked.append(item)
        ranked.sort(key=lambda x:(x.get("decisionConfidence",0),x.get("rankingScore",0),x.get("retrievalScore",0)),reverse=True)
        for i,row in enumerate(ranked,1): row["rank"]=i
        return ranked

    def recommend_standard(self, profile: dict[str, Any], top_k: int=DEFAULT_TOP_K) -> dict[str, Any]:
        if not self.available:
            return {"model":{"name":"BIS Intelligence Advanced","version":"untrained"},"domain":{"predicted":None,"score":None,"topCategories":[]},"candidates":[],"decision":"MODEL_UNAVAILABLE","primaryCandidate":None,"error":self.error}
        domain=self.classify_domain(profile); ranked=self.rank_candidates(profile,self.retrieve_candidates(profile,top_k)); th=self.metadata.get("thresholds") or {}; floor=float(th.get("retrievalFloor",.12)); margin=.06
        top1=float(ranked[0].get("decisionConfidence",0)) if ranked else 0.; ret=float(ranked[0].get("retrievalScore",0)) if ranked else 0.; top2=float(ranked[1].get("decisionConfidence",0)) if len(ranked)>1 else 0.
        if not ranked or ret<floor or top1<.40: decision="NO_MATCH"
        elif len(ranked)>1 and top1-top2<margin: decision="NEEDS_REVIEW"
        else: decision="MATCH"
        return {"model":{"name":str(self.metadata.get("modelName") or "BIS Intelligence Advanced"),"version":str(self.metadata.get("modelVersion") or "2.0.0")},"domain":domain,"candidates":ranked[:5],"decision":decision,"primaryCandidate":ranked[0] if ranked else None,"embeddingModel":self.metadata.get("runtime"),"trainingDatasetVersion":self.metadata.get("trainingDatasetVersion")}


@lru_cache(maxsize=1)
def get_bis_intelligence() -> BISIntelligence:
    return BISIntelligence()


def _designation_variants(value: Any) -> set[str]:
    n=_norm(value)
    compact=re.sub(r"\bpart\b","p",n)
    return {n, compact, re.sub(r"\s+","",n)}


def verify_model_candidates(model_result: dict[str, Any], canonical_product: dict[str, Any]|None, active_standards: list[dict[str, Any]]) -> dict[str, Any]:
    by_id={_standard_id(s):s for s in active_standards if _standard_id(s)}
    verified=[]; rejected=[]
    product_family=_family(canonical_product or {})
    primary_id=str((canonical_product or {}).get("primaryStandardId") or "")
    linked={str(x) for x in ((canonical_product or {}).get("linkedStandards") or [])}
    for candidate in model_result.get("candidates") or []:
        cid=str(candidate.get("standardId") or candidate.get("id") or "")
        cis=_is_number(candidate)
        record=by_id.get(cid)
        if record is None:
            cv=_designation_variants(cis)
            for row in active_standards:
                if cv & _designation_variants(_is_number(row)):
                    record=row; cid=_standard_id(row); break
        if record is None:
            rejected.append({"candidate":candidate,"reason":"MODEL_STANDARD_NOT_IN_ACTIVE_DATASET"}); continue
        sf=_family(record)
        linked_ok=cid==primary_id or cid in linked
        family_ok=bool(product_family and sf and product_family==sf)
        if product_family and sf and not family_ok and not linked_ok:
            rejected.append({"candidate":candidate,"standardId":cid,"reason":"PRODUCT_FAMILY_MISMATCH"}); continue
        item=dict(candidate); item["standardId"]=cid; item["firestoreRecord"]=record; item["verification"]={"firestoreRecord":"PASS","productFamily":"PASS" if (family_ok or linked_ok) else "UNRESOLVED"}
        verified.append(item)
    decision=model_result.get("decision")
    if decision=="MODEL_UNAVAILABLE": final="MODEL_UNAVAILABLE"
    elif not verified: final="NO_MATCH" if decision=="NO_MATCH" else "NEEDS_REVIEW"
    elif decision=="MATCH": final="MATCH"
    else: final="NEEDS_REVIEW"
    return {"decision":final,"verifiedCandidates":verified,"rejectedCandidates":rejected,"primaryCandidate":verified[0] if verified else None}
