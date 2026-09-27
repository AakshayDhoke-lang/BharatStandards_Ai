import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  Building2,
  Check,
  FileSpreadsheet,
  FileText,
  HeartPulse,
  LoaderCircle,
  Settings2,
  Sparkles,
  UploadCloud,
  X,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { parseDocument, runAnalysis, type ParsedDocument } from "@/lib/api";
import { QUICK_TEST_CASES } from "@/data/quickTestCases";
import { cn } from "@/lib/utils";
import { AppShell, PageHeader, Panel, StatusBadge } from "./ui";

const pipelineLabels = [
  "Document Received",
  "Parsing Document",
  "Extracting Procurement Requirements with AI",
  "Matching Against Available Standards",
  "Preparing Analysis Output",
];

const caseIcons = {
  Electrical: Zap,
  Mechanical: Settings2,
  Civil: Building2,
  Medical: HeartPulse,
};

export function AnalyzePage() {
  const [mode, setMode] = useState<"upload" | "text">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [selectedQuickCase, setSelectedQuickCase] = useState<string | null>(null);
  const [stage, setStage] = useState(-1);
  const [error, setError] = useState("");
  const [parsed, setParsed] = useState<ParsedDocument | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const nav = useNavigate();
  const location = useLocation();
  const input = useRef<HTMLInputElement>(null);

  const resetAnalysisForm = useCallback(() => {
    setMode("upload");
    setFile(null);
    setText("");
    setSelectedQuickCase(null);
    setStage(-1);
    setError("");
    setParsed(null);
    setElapsed(0);
    if (input.current) input.current.value = "";
  }, []);

  // Every navigation to /analyze represents a fresh NEW ANALYSIS form.
  useEffect(() => {
    resetAnalysisForm();
  }, [location.key, resetAnalysisForm]);

  useEffect(() => {
    if (stage < 0) { setElapsed(0); return; }
    const started = Date.now();
    const id = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, [stage]);

  const useQuickCase = (caseId: string, description: string) => {
    setMode("text");
    setText(description);
    setSelectedQuickCase(caseId);
    setFile(null);
    setParsed(null);
    setError("");
    setStage(-1);
  };

  const start = async () => {
    setError("");
    setParsed(null);
    try {
      let sourceText = text.trim();
      let sourceName = "Manual procurement description";
      let parsedForResult: ParsedDocument | null = null;
      setStage(0);

      if (mode === "upload") {
        if (!file) {
          setError("Choose a tender or technical specification first.");
          setStage(-1);
          return;
        }
        sourceName = file.name;
        setStage(1);
        const result = await parseDocument(file);
        parsedForResult = result;
        setParsed(result);
        sourceText = (result.fullText || result.markdown || "").trim();
        if (!sourceText) throw new Error(result.warnings?.[0] || "No usable text could be extracted from this document.");
      }

      if (!sourceText) throw new Error("Enter a procurement requirement before analysis.");
      setStage(2);
      const analysis = await runAnalysis(sourceText, sourceName, mode === "upload" ? "FILE" : "TEXT");
      setStage(3);
      await new Promise((resolve) => setTimeout(resolve, 250));
      setStage(4);
      await new Promise((resolve) => setTimeout(resolve, 250));
      nav("/results", { state: { analysis, parsedDocument: parsedForResult, sourceText } });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
      setStage(-1);
    }
  };

  const busy = stage >= 0;
  return <AppShell>
    <PageHeader title="Analyze Tender" description="Upload procurement documents or describe your requirement. A new analysis always starts empty; sample cases are loaded only when you explicitly choose one." />
    <div className="mx-auto w-full max-w-5xl min-w-0">
      <div className="mb-5 grid w-full grid-cols-2 rounded-md border bg-card p-1 sm:inline-flex sm:w-auto">
        <Button className="min-w-0" variant={mode === "upload" ? "default" : "ghost"} disabled={busy} onClick={() => { setMode("upload"); setError(""); }}><UploadCloud />Upload Document</Button>
        <Button className="min-w-0" variant={mode === "text" ? "default" : "ghost"} disabled={busy} onClick={() => { setMode("text"); setError(""); }}><FileText />Enter Description</Button>
      </div>

      {!busy ? <Panel
        title={mode === "upload" ? "Upload Tender or Technical Specification" : "Describe Procurement Requirement"}
        description={mode === "upload" ? "Lightweight parsing avoids sending raw binary documents to the LLM." : "Provide enough technical context to improve standards matching."}
        action={<Button type="button" size="sm" variant="ghost" onClick={resetAnalysisForm}>Clear</Button>}
      >
        {mode === "upload" ? <>
          <input ref={input} type="file" className="hidden" accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.pptx,.html,.htm" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(""); }} />
          {!file ? <button type="button" onClick={() => input.current?.click()} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); setFile(e.dataTransfer.files[0] ?? null); setError(""); }} className="grid min-h-56 w-full place-items-center rounded-md border-2 border-dashed border-input bg-muted/25 p-5 text-center hover:border-primary/60 hover:bg-secondary/50 sm:min-h-72 sm:p-8">
            <div className="min-w-0"><div className="mx-auto grid h-12 w-12 place-items-center rounded-md bg-secondary text-primary"><UploadCloud /></div><h3 className="mt-4 font-semibold text-navy">Drag and drop your document here</h3><p className="mt-1 text-sm text-muted-foreground">or click to browse from your computer</p><p className="mt-5 break-words text-xs text-muted-foreground">PDF, DOCX, XLSX, CSV, TXT, Markdown, PPTX and HTML · Maximum 50 MB</p><div className="mt-3"><StatusBadge tone="ai"><Sparkles className="h-3 w-3" /> Lightweight parser stack</StatusBadge></div></div>
          </button> : <div className="flex min-h-44 flex-col gap-4 rounded-md border bg-muted/30 p-4 sm:flex-row sm:items-center sm:p-5"><div className="grid h-12 w-12 shrink-0 place-items-center rounded-md bg-secondary text-primary"><FileSpreadsheet /></div><div className="min-w-0 flex-1"><p className="break-all font-medium">{file.name}</p><p className="mt-1 text-xs text-muted-foreground">{file.type || "Document"} · {(file.size / 1024 / 1024).toFixed(2)} MB</p><p className="mt-1 text-xs text-muted-foreground">FastAPI parses the file locally. The AI model receives extracted text only — never the raw file.</p></div><div className="flex items-center justify-between gap-2 sm:justify-end"><StatusBadge>Ready</StatusBadge><Button variant="ghost" size="icon" onClick={() => { setFile(null); setParsed(null); if (input.current) input.current.value = ""; }}><X /><span className="sr-only">Remove file</span></Button></div></div>}
        </> : <>
          <label htmlFor="requirement" className="mb-2 block text-sm font-medium">Procurement specification</label>
          <Textarea id="requirement" value={text} placeholder="Describe the product, procurement requirement, or paste tender specifications here..." onChange={e => setText(e.target.value)} className="min-h-[200px] w-full resize-y break-words leading-6 sm:min-h-52" />
          <div className="mt-5 border-t pt-4">
            <div className="mb-3"><p className="text-sm font-semibold text-navy">Quick test cases</p><p className="text-xs text-muted-foreground">Optional sample inputs for testing. Selecting one only fills the description; analysis will not start automatically.</p></div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {QUICK_TEST_CASES.map((item) => {
                const Icon = caseIcons[item.category];
                const selected = selectedQuickCase === item.id;
                return <button
                  key={item.id}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => useQuickCase(item.id, item.description)}
                  className={cn("min-w-0 rounded-md border p-3 text-left transition hover:border-primary/50 hover:bg-secondary/40", selected && "border-primary bg-secondary/60 ring-1 ring-primary/20")}
                >
                  <div className="flex items-center gap-2"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-secondary text-primary"><Icon className="h-4 w-4" /></span><span className="min-w-0 text-xs font-semibold uppercase text-muted-foreground">{item.category}</span></div>
                  <p className="mt-2 break-words text-sm font-medium text-navy">{item.title}</p>
                  <span className="mt-2 inline-flex min-h-9 items-center text-xs font-medium text-primary">Use case</span>
                </button>;
              })}
            </div>
          </div>
        </>}
        {error && <div className="mt-4 flex min-w-0 gap-2 rounded-md border border-destructive/25 bg-destructive/10 p-3 text-sm text-destructive"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /><span className="min-w-0 break-words">{error}</span></div>}
        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"><Button type="button" variant="outline" onClick={resetAnalysisForm}>Clear</Button><Button className="w-full sm:w-auto" onClick={() => void start()}><Sparkles />Analyze with BharatStandards AI</Button></div>
      </Panel> : <Panel title="Analysis Pipeline" description="Live hand-off from parser → AI model → standards retrieval.">
        <div className="space-y-3">{pipelineLabels.map((label, index) => <div key={label} className="flex min-w-0 items-center gap-3 rounded-md border p-3"><div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-muted">{index < stage ? <Check className="h-4 w-4 text-success" /> : index === stage ? <LoaderCircle className="h-4 w-4 animate-spin text-primary" /> : <span className="text-xs text-muted-foreground">{index + 1}</span>}</div><div className="min-w-0 flex-1"><p className="break-words text-sm font-medium">{label}</p>{index === 1 && parsed && <p className="break-words text-xs text-muted-foreground">{parsed.processingEngine} · {parsed.characterCount.toLocaleString()} characters extracted</p>}</div><div className="hidden shrink-0 sm:block">{index < stage && <StatusBadge>Complete</StatusBadge>}{index === stage && <StatusBadge tone="ai">Processing · {elapsed}s</StatusBadge>}</div></div>)}</div>
        {stage === 2 && elapsed >= 15 ? <div className="mt-4 break-words rounded-md border border-ai/25 bg-ai-soft p-3 text-xs text-muted-foreground">The selected AI provider is processing the request. Complex analyses or local models may take longer; processing stops with a diagnostic after about 2 minutes.</div> : null}
        {parsed?.warnings?.length ? <div className="mt-4 break-words rounded-md border border-warning/25 bg-warning-soft p-3 text-xs text-warning">{parsed.warnings.join(" ")}</div> : null}
      </Panel>}
    </div>
  </AppShell>;
}
