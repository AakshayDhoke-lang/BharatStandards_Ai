import { DEMO_MODE } from "@/lib/demo-mode";

const CONFIGURED_API_BASE = String(import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/$/, "");
const API_BASE = CONFIGURED_API_BASE || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");
const FRONTEND_ANALYSIS_TIMEOUT_MS = 130_000;

function requireApiBase(): string {
  if (API_BASE) return API_BASE;
  throw new Error(
    "Production API URL is not configured. Set VITE_API_BASE_URL to the deployed Vercel backend URL, rebuild, and redeploy Firebase Hosting."
  );
}

export interface ParsedDocument {
  fileName: string;
  fileType: string;
  processingEngine: string;
  status: string;
  markdown: string;
  fullText: string;
  textPreview: string;
  characterCount: number;
  sections: { heading: string; text: string }[];
  tables: unknown[];
  pages: { page: number; text: string }[];
  warnings: Array<string | Record<string, any>>;
}

export interface AnalysisResult {
  analysisId: string;
  inputId?: string;
  createdAt: string;
  sourceName?: string | null;
  provider?: "lmstudio" | "nvidia";
  model: string;
  dataMode: "DEMO" | "REAL";
  requirementProfile: Record<string, any>;
  input?: { type: "TEXT" | "FILE"; inputId: string };
  recommendations: Array<{
    standardId: string;
    isNumber: string;
    title: string;
    category: string;
    confidence: number;
    certification: string;
    matchedEvidence: Array<string | { text: string; source: "INPUT_TEXT" | "REQUIREMENT_PROFILE" }>;
    dataMode: string;
  }>;
  primaryStandard?: Record<string, any> | null;
  candidateStandards?: Array<Record<string, any>>;
  alliedStandards?: Array<Record<string, any>>;
  versionChecks?: Array<Record<string, any>>;
  certifications?: Array<Record<string, any>>;
  qcos?: Array<Record<string, any>>;
  coverage?: {
    evaluated: boolean;
    summary: { covered: number; partial: number; notCovered: number; unknown: number; notApplicable: number };
    requirements: Array<Record<string, any>>;
    provenance?: Record<string, any>;
  } | Array<Record<string, any>>;
  missingRequirements?: Array<Record<string, any>>;
  evidence?: Array<Record<string, any>>;
  confidence?: Record<string, any>;
  status?: string;
  canonicalProductFamily?: string | null;
  canonicalProduct?: { productId?: string | null; productName?: string | null; productFamily?: string | null; primaryStandardId?: string | null; linkedStandards?: string[] } | null;
  productResolution?: Record<string, any>;
  datasetDiagnostics?: Record<string, any>;
  knowledgeEvidenceProvenance?: Record<string, any>;
  candidateDiagnostics?: Array<Record<string, any>>;
  certificationSummary?: Record<string, any>;
  pipeline: Array<Record<string, any>>;
  warnings: Array<string | Record<string, any>>;
}

async function apiError(response: Response, fallback: string) {
  const body = await response.json().catch(() => ({}));
  return new Error(body.detail || fallback);
}

export async function parseDocument(file: File): Promise<ParsedDocument> {
  const form = new FormData();
  form.append("file", file);
  let response: Response;
  try {
    response = await fetch(`${requireApiBase()}/api/documents/parse`, { method: "POST", body: form });
  } catch {
    throw new Error(`Document Parser Offline. Could not reach ${API_BASE || "the configured production backend"}.`);
  }
  if (!response.ok) throw await apiError(response, `Document parser failed (${response.status})`);
  return response.json();
}

export async function runAnalysis(text: string, sourceName?: string, inputType: "TEXT" | "FILE" = "TEXT"): Promise<AnalysisResult> {
  let response: Response;
  try {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), FRONTEND_ANALYSIS_TIMEOUT_MS);
    try {
      response = await fetch(`${requireApiBase()}/api/analysis/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, source_name: sourceName || null, language: localStorage.getItem("bsai.language") || "en", demo_mode: DEMO_MODE, input_type: inputType }),
        signal: controller.signal,
      });
    } finally {
      window.clearTimeout(timeout);
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("AI analysis exceeded the browser safety limit after waiting for the backend timeout diagnostic.");
    }
    throw new Error(`AI backend offline or request failed. Could not complete the call through ${API_BASE || "the configured production backend"}.`);
  }
  if (!response.ok) throw await apiError(response, `Analysis failed (${response.status})`);
  return response.json();
}

export async function checkBackendHealth() {
  const response = await fetch(`${requireApiBase()}/api/health`);
  if (!response.ok) throw new Error("Backend unavailable");
  return response.json();
}


export async function checkFirestoreHealth() {
  const response = await fetch(`${requireApiBase()}/api/firestore/health`);
  if (!response.ok) throw await apiError(response, `Firestore backend unavailable (${response.status})`);
  return response.json();
}

export async function checkModelConnection() {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 50000);
  try {
    const response = await fetch(`${requireApiBase()}/api/ai/test`, { signal: controller.signal });
    if (!response.ok) throw await apiError(response, `Model unavailable (${response.status})`);
    return response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

export type AIProvider = "lmstudio" | "nvidia";

export async function getAIProvider(): Promise<{ provider: AIProvider; baseUrl: string }> {
  const response = await fetch(`${requireApiBase()}/api/ai/provider`);
  if (!response.ok) throw await apiError(response, `Could not read AI provider (${response.status})`);
  return response.json();
}

export async function setAIProvider(provider: AIProvider): Promise<{ ok: boolean; provider: AIProvider; baseUrl: string }> {
  const response = await fetch(`${requireApiBase()}/api/ai/provider`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider }),
  });
  if (!response.ok) throw await apiError(response, `Could not switch AI provider (${response.status})`);
  return response.json();
}

export async function getLMStudioModels(): Promise<{ ok: boolean; baseUrl: string; models: string[]; activeModel: string }> {
  const response = await fetch(`${requireApiBase()}/api/ai/lmstudio/models`);
  if (!response.ok) throw await apiError(response, `LM Studio unavailable (${response.status})`);
  return response.json();
}

export async function extractStandardCandidate(text: string, sourceName?: string): Promise<{ candidate: Record<string, any>; provider: string; model: string; latencyMs: number }> {
  const response = await fetch(`${requireApiBase()}/api/ingestion/extract-standard`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, source_name: sourceName || null }),
  });
  if (!response.ok) throw await apiError(response, `Standard metadata extraction failed (${response.status})`);
  return response.json();
}
