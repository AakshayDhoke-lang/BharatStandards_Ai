import { useEffect, useState } from "react";
import {
  addDoc, collection, deleteDoc, doc, getDoc, onSnapshot,
  serverTimestamp, setDoc, updateDoc, type DocumentData,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import { DATA_MODE } from "@/lib/demo-mode";

export type DatasetMode = "DEMO" | "REAL";
export type UserRole = "USER" | "CONTRIBUTOR" | "REVIEWER" | "ADMIN";
export type VerificationStatus = "PENDING" | "NEEDS_REVIEW" | "NEEDS_CORRECTION" | "VERIFIED" | "REJECTED" | "FAILED";

export const datasetMode = DATA_MODE as DatasetMode;
export const datasetDocId = datasetMode.toLowerCase();
export const datasetCollection = (name: string) => collection(db, "datasets", datasetDocId, name);

export interface SharedRecord extends DocumentData { id: string }

export function useSharedRecords<T extends SharedRecord = SharedRecord>(name: string, sortField = "updatedAt") {
  const [records, setRecords] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true); setError("");
    return onSnapshot(datasetCollection(name), (snapshot) => {
      const rows = snapshot.docs.map(d => ({ id: d.id, ...d.data() } as T));
      rows.sort((a: any, b: any) => {
        const av = a?.[sortField]?.seconds ?? a?.[sortField]?.toMillis?.() ?? 0;
        const bv = b?.[sortField]?.seconds ?? b?.[sortField]?.toMillis?.() ?? 0;
        return Number(bv) - Number(av);
      });
      setRecords(rows); setLoading(false);
    }, (err) => { setError(err.message); setLoading(false); });
  }, [name, sortField]);
  return { records, loading, error };
}


export function actor(user: { uid: string; displayName?: string | null; email?: string | null }) {
  return { userId: user.uid, userName: user.displayName || user.email || "Authenticated user" };
}

export async function writeAudit(user: { uid: string; displayName?: string | null; email?: string | null }, action: string, entityType: string, entityId: string, metadata: Record<string, unknown> = {}) {
  const a = actor(user);
  await addDoc(datasetCollection("auditLogs"), {
    action, entityType, entityId, dataset: datasetMode, datasetMode,
    userId: a.userId, userName: a.userName, timestamp: serverTimestamp(), metadata,
  });
}

export async function createSharedRecord(name: string, data: Record<string, unknown>, user: { uid: string; displayName?: string | null; email?: string | null }, action = "RECORD_CREATED") {
  const a = actor(user);
  const ref = await addDoc(datasetCollection(name), {
    ...data, datasetMode, createdBy: a.userId, createdByName: a.userName,
    createdAt: serverTimestamp(), updatedBy: a.userId, updatedByName: a.userName, updatedAt: serverTimestamp(),
  });
  await writeAudit(user, action, name.toUpperCase(), ref.id, { category: data.category || null });
  return ref.id;
}

export async function updateSharedRecord(name: string, id: string, data: Record<string, unknown>, user: { uid: string; displayName?: string | null; email?: string | null }, action = "RECORD_UPDATED") {
  const a = actor(user);
  await updateDoc(doc(db, "datasets", datasetDocId, name, id), {
    ...data, updatedBy: a.userId, updatedByName: a.userName, updatedAt: serverTimestamp(),
  });
  await writeAudit(user, action, name.toUpperCase(), id, { category: data.category || null });
}

export async function removeSharedRecord(name: string, id: string, user: { uid: string; displayName?: string | null; email?: string | null }, action = "RECORD_DELETED") {
  await deleteDoc(doc(db, "datasets", datasetDocId, name, id));
  await writeAudit(user, action, name.toUpperCase(), id);
}

export async function ensureUserProfile(user: { uid: string; displayName?: string | null; email?: string | null }) {
  const ref = doc(db, "users", user.uid);
  const snap = await getDoc(ref);
  if (!snap.exists()) {
    await setDoc(ref, { uid: user.uid, displayName: user.displayName || "", email: user.email || "", role: "USER", createdAt: serverTimestamp(), updatedAt: serverTimestamp() });
  } else {
    await setDoc(ref, { displayName: user.displayName || "", email: user.email || "", updatedAt: serverTimestamp() }, { merge: true });
  }
}
