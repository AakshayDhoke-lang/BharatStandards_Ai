import { useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AlertTriangle, Check, Copy, Download, FileText, Save, ShieldCheck, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppShell, DataTable, EmptyState, PageHeader, Panel, StatusBadge } from "./ui";
import type { AnalysisResult, ParsedDocument } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { saveAnalysisForUser } from "@/lib/analysis-storage";
import { downloadAnalysisPdf } from "@/lib/report";

function displayValue(value: unknown): string {
  if (value == null || value === "") return "";
  if (Array.isArray(value)) return value.map(displayValue).filter(Boolean).join(", ");
  if (typeof value === "object") return Object.entries(value as Record<string, unknown>).map(([k,v])=>`${k}: ${displayValue(v)}`).filter(x=>!x.endsWith(": ")).join(" · ");
  return String(value);
}

function titleCase(key: string) {
  return key.replace(/([a-z])([A-Z])/g,"$1 $2").replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());
}

function comparisonRows(profile: Record<string, any>) {
  const rows: Array<[string,string]> = [];
  const add=(label:string,value:unknown)=>{const text=displayValue(value);if(text)rows.push([label,text])};
  add("Product", profile.product?.name);
  add("Category", profile.product?.category);
  add("Subcategory", profile.product?.subcategory);
  add("Quantity", profile.product?.quantity);
  add("Application", profile.application?.useCase);
  add("Environment", profile.application?.environment);
  add("Material", profile.materials);
  for (const section of ["dimensions","technicalProperties","performance","safety","testing"]) {
    const value=profile[section];
    if (value && typeof value === "object" && !Array.isArray(value)) Object.entries(value).forEach(([k,v])=>add(titleCase(k),v));
    else add(titleCase(section),value);
  }
  if (profile.certification?.requested) add("Certification", profile.certification?.details || "Requested");
  return rows;
}

export function ResultsPage(){
 const [copied,setCopied]=useState("");
 const [saveState,setSaveState]=useState<"idle"|"saving"|"saved"|"local"|"error">("idle");
 const { user } = useAuth();
 const location=useLocation();
 const state=location.state as {analysis?:AnalysisResult;parsedDocument?:ParsedDocument|null;sourceText?:string}|null;
 const live=state?.analysis;
 const parsed=state?.parsedDocument;
 const profile=(live?.requirementProfile ?? {}) as Record<string,any>;
 const product=profile.product ?? {};
 const primary=(live?.primaryStandard ?? live?.recommendations?.[0]) as any;
 const comparison=useMemo(()=>comparisonRows(profile),[profile]);
 const copy=(v:string)=>{navigator.clipboard?.writeText(v);setCopied(v);setTimeout(()=>setCopied(""),1200)};

 if(!live) return <AppShell><PageHeader title="Analysis Result" description="No current analysis is loaded." actions={<Button asChild><Link to="/analyze"><Sparkles/>New Analysis</Link></Button>}/><EmptyState title="No current result available" description="Run a new description or document analysis. Previous or sample results are never injected into this page." action={<Button asChild><Link to="/analyze">Analyze Tender</Link></Button>}/></AppShell>;

 const analysisId=live.analysisId;
 const detectedProduct=product?.name || "Not specified";
 const primaryNumber=primary?.isNumber || "No recommendation";
 const primaryTitle=primary?.title || "No verified result available";
 const primaryConfidence=Number(primary?.confidence ?? live.confidence?.overall ?? 0);
 const allied=live.alliedStandards ?? [];
 const versions=live.versionChecks ?? [];
 const certifications=live.certifications ?? [];
 const qcos=live.qcos ?? [];
 const rawCoverage=live.coverage as any;
 const coverageResult=Array.isArray(rawCoverage)
   ? { evaluated: Boolean(primary) && rawCoverage.some((x:any)=>String(x.standardCoverage||"").toUpperCase()!=="NOT_EVALUATED"), summary: null, requirements: rawCoverage.map((x:any)=>({key:x.requirement,label:titleCase(x.requirement),tenderRequirement:x.evidence||"Current requirement profile",tenderPresence:x.tenderPresent?"PRESENT":"NOT_PRESENT",status:x.standardCoverage||"UNKNOWN",evidence:[x.evidence].filter(Boolean)})) }
   : (rawCoverage ?? { evaluated:false, summary:null, requirements:[] });
 const coverage=coverageResult.requirements ?? [];
 const missing=live.missingRequirements ?? [];
 const evidence=(live.evidence ?? []).filter((e:any)=>e.analysisId===analysisId && (!live.inputId || e.inputId===live.inputId));
 const version=versions[0];
 const certification=certifications[0];
 const qco=qcos[0];
 const warnings=live.warnings ?? [];
 const coverageSummary=coverageResult.summary ?? coverage.reduce((acc:any,x:any)=>{const k=String(x.status||"UNKNOWN").toUpperCase();if(k==="COVERED")acc.covered++;else if(k==="PARTIAL")acc.partial++;else if(k==="NOT_COVERED")acc.notCovered++;else if(k==="NOT_APPLICABLE")acc.notApplicable++;else acc.unknown++;return acc;},{covered:0,partial:0,notCovered:0,unknown:0,notApplicable:0});
 const coverageLabel=coverageResult.evaluated ? `${coverageSummary.covered} Covered · ${coverageSummary.partial} Partial · ${coverageSummary.unknown} Unknown${coverageSummary.notCovered?` · ${coverageSummary.notCovered} Not Covered`:""}` : "Not evaluated";
 const certificationSummary=(live as any).certificationSummary ?? {};
 const canonicalProductFamily=(live as any).canonicalProductFamily as string|undefined;
 const canonicalProduct=(live as any).canonicalProduct as any;
 const candidateDiagnostics=((live as any).candidateDiagnostics ?? []) as any[];
 const sourcePage=parsed?.pages?.find(p=>p.text?.trim())?.page;

 const download=()=>downloadAnalysisPdf(live);
 const save=async()=>{
   if(!user){setSaveState("error");return;}
   setSaveState("saving");
   try{
     const result=await saveAnalysisForUser(user.uid,live);
     setSaveState(result.storage==="local"?"local":"saved");
   }catch{setSaveState("error");}
 };

 return <AppShell>
 <PageHeader title="Analysis Complete" description={`Current-case result generated through ${live.provider === "lmstudio" ? "LM Studio" : live.provider === "nvidia" ? "NVIDIA" : "the selected AI provider"}. All sections below consume this analysis only.`} actions={<><Button variant="outline" onClick={download}><Download/>Download PDF Report</Button><Button variant="outline" onClick={save} disabled={saveState==="saving"}><Save/>{saveState==="saving"?"Saving…":saveState==="saved"?"Saved to History":saveState==="local"?"Saved Locally":saveState==="error"?"Save Failed":"Save Analysis"}</Button><Button asChild><Link to="/analyze"><Sparkles/>New Analysis</Link></Button></>}/>
 <div className="mb-5 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-md border bg-card px-4 py-3 text-xs"><span><strong>Detected Product:</strong> {detectedProduct}</span>{canonicalProduct?.productName&&<span><strong>Canonical Product:</strong> {canonicalProduct.productName} ({canonicalProduct.productId})</span>}{canonicalProductFamily&&<span><strong>Product Family:</strong> {String(canonicalProductFamily).replaceAll("_"," ")}</span>}<button onClick={()=>copy(analysisId)} className="inline-flex items-center gap-1"><strong>Analysis ID:</strong> {analysisId} <Copy className="h-3 w-3"/>{copied===analysisId&&<span className="text-success">Copied</span>}</button><span><strong>Input ID:</strong> {live.inputId ?? live.input?.inputId ?? "—"}</span><span><strong>Timestamp:</strong> {new Date(live.createdAt).toLocaleString()}</span><StatusBadge tone={live.dataMode==="DEMO"?"warning":"success"}>{live.dataMode}</StatusBadge></div>{saveState==="saved"&&<div className="mb-5 rounded-md border border-success/20 bg-success-soft px-4 py-3 text-sm text-success">Analysis saved to your Firestore-backed Analysis History.</div>}{saveState==="local"&&<div className="mb-5 rounded-md border border-warning/20 bg-warning-soft px-4 py-3 text-sm">Firestore was unavailable, so this analysis was saved locally on this device and is still available in Analysis History.</div>}{saveState==="error"&&<div className="mb-5 rounded-md border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">Could not save this analysis. Please verify that you are signed in and Firestore rules are deployed.</div>}
 <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">{[["Primary Standard",primaryNumber],["Confidence Score",primaryConfidence?`${primaryConfidence}%`:"Not available"],["Standard Coverage",coverageLabel],["Certification",certification?.mandatory===true?"Required":certification?.mandatory===false?"Not mandatory":certificationSummary.certificationMandatory===true?"Required":certificationSummary.certificationMandatory===false?"Not mandatory":"Needs Review"],["Warnings",String(warnings.length)]].map(([label,value],i)=><div key={label} className={`app-card border-t-2 p-4 ${i===0?"border-t-primary":i===4?"border-t-warning":"border-t-ai"}`}><p className="text-[11px] font-semibold uppercase text-muted-foreground">{label}</p><p className="mt-2 text-xl font-semibold text-navy">{value}</p></div>)}</div>

 <div className="mt-5 grid gap-5 xl:grid-cols-[1.05fr_1.35fr]"><Panel title="Detected Procurement Requirement" description="Fresh structured profile from the current input only">{comparison.length?<div className="grid grid-cols-1 gap-x-8 gap-y-3 sm:grid-cols-2">{comparison.map(([k,v])=><div key={`${k}-${v}`} className="border-b pb-2"><p className="text-[11px] uppercase text-muted-foreground">{k}</p><p className="mt-1 text-sm font-medium">{v}</p></div>)}</div>:<EmptyState title="No structured requirements" description="The model did not return usable requirement fields for this case."/>}<details className="mt-4 rounded-md border bg-muted/30"><summary className="cursor-pointer px-3 py-2 text-xs font-medium">View Current Requirement Profile JSON</summary><pre className="max-h-80 overflow-auto border-t p-3 text-[11px]">{JSON.stringify(profile,null,2)}</pre></details></Panel>
 <section className="app-card border-l-4 border-l-ai"><div className="border-b px-5 py-4"><div className="mb-2 flex flex-wrap gap-2"><StatusBadge tone="ai">Current Recommendation</StatusBadge><StatusBadge tone={live.dataMode==="DEMO"?"warning":"success"}>{live.dataMode} Data</StatusBadge>{primary?.status&&<StatusBadge>{primary.status}</StatusBadge>}</div><p className="text-xs font-medium text-muted-foreground">Recommended Indian Standard</p><div className="mt-1 flex items-center gap-2"><h2 className="text-2xl font-semibold text-navy">{primaryNumber}</h2>{primary&&<Button size="icon" variant="ghost" onClick={()=>copy(primaryNumber)}><Copy/></Button>}</div><p className="mt-1 text-sm">{primaryTitle}</p></div><div className="p-5">{primary?<><div className="h-2 overflow-hidden rounded-sm bg-muted"><div className="h-full bg-success" style={{width:`${primaryConfidence}%`}}/></div><p className="mt-3 text-xs text-muted-foreground">Matched evidence: {primary.matchedEvidence?.length ? primary.matchedEvidence.map((e:any)=>typeof e==="string"?e:e.text).join(", ") : "Product-family compatibility"}</p><div className="mt-4"><Button asChild><Link to={`/standards/${encodeURIComponent(primary.standardId || primaryNumber)}`}>View Standard Details</Link></Button></div></>:<div className="rounded-md border border-warning/25 bg-warning-soft p-4 text-sm"><strong>Needs Review.</strong> No compatible standard was found for this current case. No previous or unrelated standard has been substituted.</div>}</div></section></div>

 <div className="mt-5 grid gap-5 xl:grid-cols-[1.2fr_.8fr]"><Panel title="Why this standard was recommended" description="Dynamic requirement comparison from the current profile">{comparison.length?<div className="grid gap-x-5 sm:grid-cols-2">{comparison.map(([k,v])=><div key={`${k}-${v}`} className="flex items-start justify-between gap-3 border-b py-2.5 text-sm"><div><span>{k}</span><p className="max-w-72 text-[11px] text-muted-foreground">{v}</p></div><span className="flex shrink-0 items-center gap-1 text-success"><Check className="h-4 w-4"/>Current</span></div>)}</div>:<p className="text-sm text-muted-foreground">No comparison rows are available.</p>}</Panel><Panel title="Candidate Standards" description="Product-compatible candidates only">{(live.candidateStandards??live.recommendations??[]).length?<div className="space-y-2">{(live.candidateStandards??live.recommendations??[]).map((c:any)=><div key={c.standardId} className="rounded-md border p-3"><div className="flex justify-between gap-3"><strong className="text-sm text-primary">{c.isNumber}</strong><StatusBadge>{c.confidence}%</StatusBadge></div><p className="mt-1 text-xs">{c.title}</p></div>)}</div>:<p className="text-sm text-muted-foreground">No product-compatible candidate was found.</p>}</Panel></div>

 {candidateDiagnostics.length>0&&<details className="mt-5 rounded-md border bg-card"><summary className="cursor-pointer px-4 py-3 text-sm font-medium">Candidate compatibility diagnostics</summary><div className="border-t p-4"><div className="space-y-3">{candidateDiagnostics.map((d:any)=><div key={d.standardId} className="rounded-md border p-3 text-xs"><div className="flex flex-wrap items-center justify-between gap-2"><strong>{d.standardId}</strong><StatusBadge>{d.productCompatible?"Compatible":d.rejectReason||"Rejected"}</StatusBadge></div><div className="mt-2 grid gap-1 sm:grid-cols-2"><span>Requirement family: {d.requirementProductFamily||"UNRESOLVED"}</span><span>Candidate family: {d.candidateProductFamily}</span><span>Product compatible: {String(d.productCompatible)}</span><span>Category compatible: {String(d.categoryCompatible)}</span><span>Scope compatible: {String(d.scopeCompatible)}</span><span>Score: {d.finalScore==null?"NOT_CALCULATED":d.finalScore}</span></div>{d.matchedTerms?.length>0&&<p className="mt-2 text-muted-foreground">Matched terms: {d.matchedTerms.join(", ")}</p>}</div>)}</div></div></details>}

 {live.bisIntelligence&&<Panel title="BIS Intelligence" description={live.bisIntelligence.shadowMode?"Shadow comparison — legacy matcher remains final":"Custom standard retrieval and deterministic verification"} className="mt-5"><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><div><p className="text-[11px] text-muted-foreground">Model</p><p className="text-sm font-medium">{live.bisIntelligence.modelName} {live.bisIntelligence.modelVersion}</p></div><div><p className="text-[11px] text-muted-foreground">Domain</p><p className="text-sm font-medium">{live.bisIntelligence.predictedDomain||"Not available"}</p></div><div><p className="text-[11px] text-muted-foreground">Decision</p><StatusBadge>{live.bisIntelligence.decision}</StatusBadge></div><div><p className="text-[11px] text-muted-foreground">Legacy agreement</p><p className="text-sm font-medium">{live.bisIntelligence.legacyAgreement===true?"Yes":live.bisIntelligence.legacyAgreement===false?"No / unavailable":"Not evaluated"}</p></div></div>{live.bisIntelligence.candidates?.length?<div className="mt-4 space-y-2"><p className="text-xs font-medium text-muted-foreground">Top candidates</p>{live.bisIntelligence.candidates.slice(0,3).map((c:any,i:number)=><div key={`${c.standardId||c.isNumber}-${i}`} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-2 text-xs"><span><strong>{i+1}. {c.isNumber||c.standardId}</strong> {c.title?`— ${c.title}`:""}</span><span>{typeof c.rankingScore==="number"?c.rankingScore.toFixed(3):"—"}</span></div>)}</div>:<p className="mt-4 text-xs text-muted-foreground">No trained BIS Intelligence candidate is available. Existing canonical matching remains protected by feature flags.</p>}</Panel>}

 <Panel title="Verified Processing Pipeline" description="Actual current-request pipeline" className="mt-5"><div className="grid gap-3 md:grid-cols-4">{live.pipeline?.map((step:any)=><div key={step.stage} className="rounded-md border bg-muted/20 p-3"><div className="flex items-center justify-between gap-2"><p className="text-xs font-semibold text-navy">{String(step.stage).replaceAll("_"," ")}</p><StatusBadge>{step.status}</StatusBadge></div><p className="mt-2 text-[11px] text-muted-foreground">{step.model || (step.characters?`${step.characters} characters`:`${step.candidates ?? 0} candidates`)}</p></div>)}</div><div className="mt-4 rounded-md border border-ai/25 bg-ai-soft p-3 text-xs"><strong>Provider:</strong> {live.provider || "—"} · <strong>Model:</strong> {live.model} · <strong>Dataset:</strong> {live.dataMode}. Raw files are not sent to the model; only current extracted text is processed.</div></Panel>

 <Panel title="Allied & Normative Standards" description="Relationships looked up only from the current primary standard" className="mt-5 overflow-hidden">{allied.length?<div className="-m-5"><DataTable columns={["Standard","Title","Relationship","Applicability","Mandatory","Reason","Status"]} rows={allied.map((x:any)=>[<span className="font-medium text-primary">{x.standard}</span>,x.title,<StatusBadge tone="info">{x.relationship}</StatusBadge>,<StatusBadge>{x.applicability}</StatusBadge>,x.mandatory,x.reason,<StatusBadge>{x.status}</StatusBadge>])}/></div>:<p className="text-sm text-muted-foreground">No verified allied standards are available for this standard in the current knowledge base.</p>}</Panel>

 <div className="mt-5 grid gap-5 xl:grid-cols-2"><Panel title="Version & Amendment Status" description="Version data scoped to the current primary standard">{version?<div className="grid gap-3 sm:grid-cols-3"><div><p className="text-xs text-muted-foreground">Current Version</p><strong>{version.currentVersion}</strong></div><div><p className="text-xs text-muted-foreground">Status</p><StatusBadge>{version.status}</StatusBadge></div><div><p className="text-xs text-muted-foreground">Reaffirmed</p><strong>{version.reaffirmed ?? "Not recorded"}</strong></div><div className="sm:col-span-3"><p className="text-xs text-muted-foreground">Amendments</p><p className="text-sm">{Array.isArray(version.amendments) ? (version.amendments.length ? version.amendments.join(", ") : "No amendments recorded in active knowledge base.") : "No verified amendment information available."}</p></div></div>:<p className="text-sm text-muted-foreground">Version Status: <strong>Needs Review</strong>. No version record exists for the current primary standard.</p>}</Panel><Panel title="Certification Requirements" description="Certification/QCO data scoped to the current product or standard">{certification?<div className="flex gap-4"><div className="grid h-12 w-12 shrink-0 place-items-center rounded-md bg-success-soft text-success"><ShieldCheck/></div><div className="grid flex-1 gap-3 sm:grid-cols-2">{[["Certification Type",certification.type],["Mandatory",certification.mandatory===true?"Yes":certification.mandatory===false?"No":"Not established"],["Scheme",certification.scheme||"Needs Review"],["Status",certification.status||"Needs Review"],["QCO",qco?.name||"No verified QCO record"],["Effective Date",qco?.effectiveDate||"Not recorded"]].map(([k,v])=><div key={k}><p className="text-[11px] text-muted-foreground">{k}</p><p className="text-sm font-medium">{v}</p></div>)}</div></div>:<p className="text-sm text-muted-foreground"><strong>Needs Review.</strong> No verified certification/QCO record was found for the current product in the active knowledge base.</p>}</Panel></div>

 <Panel title="Tender Requirements vs Standard Coverage" description={coverageResult.evaluated?coverageLabel:"Tender presence and standards coverage are intentionally separate"} className="mt-5 overflow-hidden">{coverage.length?<div className="-m-5"><DataTable columns={["Requirement","Tender Requirement","Tender Presence","Evidence","Standard Coverage"]} rows={coverage.map((x:any)=>[x.label||titleCase(x.key||x.requirement||"requirement"),<span className="max-w-md whitespace-normal break-words">{x.tenderRequirement||"Not specified"}</span>,<StatusBadge>{String(x.tenderPresence||"").toUpperCase()==="PRESENT"?"Present":"Not present"}</StatusBadge>,<div className="max-w-xl space-y-1 whitespace-normal break-words">{(Array.isArray(x.evidence)?x.evidence:[x.evidence]).filter(Boolean).map((e:any,i:number)=><p key={i}>{String(e)}</p>)}</div>,<StatusBadge>{String(x.status||x.standardCoverage||"UNKNOWN").replaceAll("_"," ")}</StatusBadge>])}/></div>:<p className="text-sm text-muted-foreground">No requirement-presence data is available.</p>} {!coverageResult.evaluated&&<div className="mt-5 rounded-md border border-warning/25 bg-warning-soft p-3 text-sm"><strong>Standard coverage not evaluated.</strong> {primary?"Coverage evaluation did not complete for this result.":"No compatible primary standard was selected."}</div>}</Panel>

 {(missing.length>0||warnings.length>0)&&<Panel title="Needs Review / Warnings" description="Current-case gaps only" className="mt-5"><div className="space-y-3">{[...missing,...warnings].map((w:any,i)=><div key={i} className="flex gap-2 rounded-md border border-warning/25 bg-warning-soft p-3 text-sm"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning"/><div><span>{typeof w==="string"?w:(w.message||displayValue(w))}</span>{typeof w==="object"&&w?.code&&<p className="mt-1 text-[11px] text-muted-foreground">{w.code}</p>}</div></div>)}</div></Panel>}

 <Panel title="Evidence & Sources" description="Evidence items must match the current analysis and input IDs" className="mt-5">{evidence.length?evidence.map((e:any,i:number)=><div key={`${e.inputId}-${i}`} className="mb-3 rounded-md border last:mb-0"><div className="flex items-center gap-3 p-4"><FileText className="h-4 w-4 text-primary"/><div className="flex-1"><p className="text-sm font-medium">{e.sourceType}</p><p className="text-xs text-muted-foreground">{live.input?.type==="FILE"&&sourcePage?`Page ${sourcePage} · `:""}Analysis {analysisId}</p></div><StatusBadge>Current Input</StatusBadge></div><div className="border-t bg-muted/30 p-4 text-sm whitespace-pre-wrap">{e.text}</div></div>):<p className="text-sm text-muted-foreground">No current-input evidence was returned.</p>}</Panel>
 </AppShell>
}
