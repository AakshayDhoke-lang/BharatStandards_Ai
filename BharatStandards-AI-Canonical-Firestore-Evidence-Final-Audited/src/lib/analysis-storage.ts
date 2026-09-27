import { collection, deleteDoc, doc, getDocs, setDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import type { AnalysisResult } from "@/lib/api";

export interface SavedAnalysisRecord {
  analysisId: string;
  userId: string;
  createdAt: string;
  savedAt: string;
  sourceName: string;
  product: string;
  primaryStandard: string;
  confidence: number | null;
  status: string;
  dataMode: "DEMO" | "REAL";
  analysis: AnalysisResult;
}

function storageKey(userId: string) {
  return `bsai.savedAnalyses.${userId}`;
}

function cleanForFirestore<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function toRecord(userId: string, analysis: AnalysisResult): SavedAnalysisRecord {
  const profile = analysis.requirementProfile ?? {};
  const product = (profile as any)?.product?.name || "Unspecified product";
  const primary = (analysis.primaryStandard ?? analysis.recommendations?.[0]) as any;
  const confidenceValue = primary?.confidence ?? analysis.confidence?.overall;
  return {
    analysisId: analysis.analysisId,
    userId,
    createdAt: analysis.createdAt,
    savedAt: new Date().toISOString(),
    sourceName: analysis.sourceName || "User-entered description",
    product,
    primaryStandard: primary?.isNumber || "No compatible standard",
    confidence: Number.isFinite(Number(confidenceValue)) ? Number(confidenceValue) : null,
    status: analysis.status || (primary ? "COMPLETED" : "NEEDS_REVIEW"),
    dataMode: analysis.dataMode,
    analysis: cleanForFirestore(analysis),
  };
}

function readLocal(userId: string): SavedAnalysisRecord[] {
  try {
    const raw = localStorage.getItem(storageKey(userId));
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeLocal(userId: string, records: SavedAnalysisRecord[]) {
  localStorage.setItem(storageKey(userId), JSON.stringify(records));
}

function readLegacy(userId: string): SavedAnalysisRecord[] {
  const records: SavedAnalysisRecord[] = [];
  try {
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i);
      if (!key?.startsWith("bsai.analysis.")) continue;
      const raw = localStorage.getItem(key);
      if (!raw) continue;
      try {
        const analysis = JSON.parse(raw) as AnalysisResult;
        if (analysis?.analysisId) records.push(toRecord(userId, analysis));
      } catch { /* ignore corrupt legacy entries */ }
    }
  } catch { /* storage unavailable */ }
  return records;
}

export async function saveAnalysisForUser(userId: string, analysis: AnalysisResult) {
  const record = toRecord(userId, analysis);

  // Keep an immediate local copy so History works even during temporary Firestore outages.
  const local = readLocal(userId).filter((item) => item.analysisId !== record.analysisId);
  writeLocal(userId, [record, ...local]);

  try {
    await setDoc(doc(db, "users", userId, "analyses", record.analysisId), cleanForFirestore(record), { merge: true });
    return { record, storage: "firestore+local" as const };
  } catch (error) {
    console.warn("Firestore analysis save failed; local fallback retained.", error);
    return { record, storage: "local" as const };
  }
}

export async function listAnalysesForUser(userId: string): Promise<SavedAnalysisRecord[]> {
  const localMap = new Map<string, SavedAnalysisRecord>();
  [...readLegacy(userId), ...readLocal(userId)].forEach((item) => localMap.set(item.analysisId, item));
  const local = [...localMap.values()];
  if (local.length) writeLocal(userId, local);
  try {
    const snap = await getDocs(collection(db, "users", userId, "analyses"));
    const remote = snap.docs.map((d) => d.data() as SavedAnalysisRecord);
    const merged = new Map<string, SavedAnalysisRecord>();
    [...local, ...remote].forEach((item) => {
      const existing = merged.get(item.analysisId);
      if (!existing || new Date(item.savedAt).getTime() >= new Date(existing.savedAt).getTime()) merged.set(item.analysisId, item);
    });
    const records = [...merged.values()].sort((a, b) => new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime());
    writeLocal(userId, records);
    return records;
  } catch (error) {
    console.warn("Firestore analysis history unavailable; using local fallback.", error);
    return local.sort((a, b) => new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime());
  }
}

export async function deleteAnalysisForUser(userId: string, analysisId: string) {
  writeLocal(userId, readLocal(userId).filter((item) => item.analysisId !== analysisId));
  localStorage.removeItem(`bsai.analysis.${analysisId}`);
  try {
    await deleteDoc(doc(db, "users", userId, "analyses", analysisId));
  } catch (error) {
    console.warn("Firestore analysis delete failed; local copy was removed.", error);
  }
}
