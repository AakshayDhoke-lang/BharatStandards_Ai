import type { AnalysisResult } from "@/lib/api";

function text(value: unknown): string {
  if (value == null || value === "") return "Not available";
  if (Array.isArray(value)) return value.map(text).join(", ");
  if (typeof value === "object") return Object.entries(value as Record<string, unknown>)
    .map(([k, v]) => `${k.replace(/([a-z])([A-Z])/g, "$1 $2")}: ${text(v)}`)
    .join("; ");
  return String(value);
}

function ascii(value: string) {
  return value
    .replace(/[–—]/g, "-")
    .replace(/•/g, "-")
    .replace(/[^\x20-\x7E]/g, "?");
}

function wrap(value: string, max = 92) {
  const words = ascii(value).split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > max && current) {
      lines.push(current);
      current = word;
    } else current = next;
  }
  if (current) lines.push(current);
  return lines.length ? lines : [""];
}

function escapePdf(value: string) {
  return value.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}

function buildPdf(lines: string[]) {
  const linesPerPage = 48;
  const pages: string[][] = [];
  for (let i = 0; i < lines.length; i += linesPerPage) pages.push(lines.slice(i, i + linesPerPage));
  if (!pages.length) pages.push(["BharatStandards AI report"]);

  const objects: string[] = [];
  const add = (body: string) => { objects.push(body); return objects.length; };
  const catalogId = add("");
  const pagesId = add("");
  const fontId = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
  const pageIds: number[] = [];

  pages.forEach((pageLines) => {
    const content = ["BT", "/F1 10 Tf", "14 TL", "50 790 Td"];
    pageLines.forEach((line, index) => {
      if (index > 0) content.push("T*");
      content.push(`(${escapePdf(line)}) Tj`);
    });
    content.push("ET");
    const stream = content.join("\n");
    const contentId = add(`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
    const pageId = add(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >>`);
    pageIds.push(pageId);
  });

  objects[catalogId - 1] = `<< /Type /Catalog /Pages ${pagesId} 0 R >>`;
  objects[pagesId - 1] = `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pageIds.length} >>`;

  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((body, index) => {
    offsets.push(pdf.length);
    pdf += `${index + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xref = pdf.length;
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let i = 1; i < offsets.length; i += 1) pdf += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xref}\n%%EOF`;
  return new Blob([pdf], { type: "application/pdf" });
}

export function downloadAnalysisPdf(analysis: AnalysisResult) {
  const profile = analysis.requirementProfile ?? {};
  const product = (profile as any)?.product ?? {};
  const primary = (analysis.primaryStandard ?? analysis.recommendations?.[0]) as any;
  const lines: string[] = [];
  const add = (value = "") => wrap(value).forEach((line) => lines.push(line));
  const section = (title: string) => { lines.push(""); add(title.toUpperCase()); add("-".repeat(Math.min(title.length + 4, 60))); };

  add("BHARATSTANDARDS AI");
  add("Procurement Standards Analysis Report");
  add(`Analysis ID: ${analysis.analysisId}`);
  add(`Generated: ${new Date(analysis.createdAt).toLocaleString()}`);
  add(`Data mode: ${analysis.dataMode} | Provider: ${analysis.provider || "configured provider"} | Model: ${analysis.model}`);

  section("Procurement Summary");
  add(`Product: ${text(product.name)}`);
  add(`Category: ${text(product.category)}`);
  add(`Subcategory: ${text(product.subcategory)}`);
  add(`Quantity: ${text(product.quantity)}`);
  add(`Application: ${text((profile as any)?.application?.useCase)}`);
  add(`Environment: ${text((profile as any)?.application?.environment)}`);
  add(`Materials: ${text((profile as any)?.materials)}`);

  section("Recommended Standard");
  if (primary) {
    add(`${primary.isNumber || "Standard"} - ${primary.title || ""}`);
    add(`Confidence: ${primary.confidence ?? analysis.confidence?.overall ?? "Needs Review"}${primary.confidence != null ? "%" : ""}`);
    add(`Matched evidence: ${text(primary.matchedEvidence)}`);
  } else add("No compatible standard was selected. This case requires review.");

  section("Technical Requirements Extracted");
  ["dimensions", "technicalProperties", "performance", "safety", "testing"].forEach((key) => {
    const value = (profile as any)[key];
    if (value && (typeof value !== "object" || Object.keys(value).length)) add(`${key.replace(/([a-z])([A-Z])/g, "$1 $2")}: ${text(value)}`);
  });

  section("Allied Standards");
  const allied = analysis.alliedStandards ?? [];
  if (allied.length) allied.forEach((item: any) => add(`- ${item.isNumber || item.standard || item.standardId || "Standard"}: ${item.title || item.relation || ""}`));
  else add("No verified allied standards are available for this analysis.");


  section("Standard Coverage");
  const coverage: any = analysis.coverage;
  if (coverage && !Array.isArray(coverage) && coverage.evaluated) {
    const summary = coverage.summary ?? {};
    add(`Summary: ${summary.covered ?? 0} Covered; ${summary.partial ?? 0} Partial; ${summary.notCovered ?? 0} Not Covered; ${summary.unknown ?? 0} Unknown; ${summary.notApplicable ?? 0} Not Applicable`);
    (coverage.requirements ?? []).forEach((item: any) => {
      add(`${item.label || item.key}: ${item.status || "UNKNOWN"}`);
      add(`Tender requirement: ${item.tenderRequirement || "Not specified"}`);
      (item.evidence ?? []).forEach((ev: any) => add(`Evidence: ${text(ev)}`));
    });
  } else if (Array.isArray(coverage) && coverage.length) {
    coverage.forEach((item: any) => add(`${item.requirement}: ${item.standardCoverage || "UNKNOWN"} - ${item.evidence || ""}`));
  } else add("Standard coverage was not evaluated for this analysis.");

  section("Version / Amendments");
  const versions = analysis.versionChecks ?? [];
  if (versions.length) versions.forEach((item: any) => {
    add(`Current version: ${item.currentVersion || "Not recorded"}`);
    add(`Status: ${item.status || "Not recorded"}`);
    add(`Reaffirmed: ${item.reaffirmed ?? "Not recorded"}`);
    add(`Amendments: ${Array.isArray(item.amendments) ? (item.amendments.length ? item.amendments.join(", ") : "No amendments recorded in active knowledge base") : "No verified amendment information available"}`);
  }); else add("No verified version record is available for this analysis.");

  section("Certification / QCO");
  const certifications = analysis.certifications ?? [];
  const qcos = analysis.qcos ?? [];
  if (!certifications.length && !qcos.length) add("No verified certification/QCO record was established. Needs Review.");
  certifications.forEach((item: any) => add(`Certification: ${text(item)}`));
  qcos.forEach((item: any) => add(`QCO: ${text(item)}`));

  section("Knowledge Evidence Provenance");
  const provenance = analysis.knowledgeEvidenceProvenance ?? analysis.datasetDiagnostics ?? {};
  add(`Dataset: ${text((provenance as any).datasetMode || analysis.dataMode)}`);
  add(`Product record: ${text((provenance as any).productId)}`);
  add(`Primary standard record: ${text((provenance as any).primaryStandardId)}`);
  add(`Relationship records: ${text((provenance as any).relationshipIds)}`);
  add(`Certification records: ${text((provenance as any).certificationIds || (provenance as any).certificationId)}`);
  add(`QCO records: ${text((provenance as any).qcoIds || (provenance as any).qcoId)}`);
  add(`Version record: ${text((provenance as any).versionRecordId)}`);
  add(`Source records: ${text((provenance as any).sourceIds)}`);

  section("Warnings and Review Items");
  const warnings = analysis.warnings ?? [];
  if (warnings.length) warnings.forEach((item: any) => add(`- ${typeof item === "string" ? item : text(item)}`));
  else add("No warnings recorded for this analysis.");

  section("Evidence");
  const evidence = analysis.evidence ?? [];
  if (evidence.length) evidence.slice(0, 20).forEach((item: any) => add(`- ${item.text || text(item)}${item.page ? ` (page ${item.page})` : ""}`));
  else add("No evidence excerpts were stored for this analysis.");

  const blob = buildPdf(lines);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `BharatStandards-Analysis-${analysis.analysisId}.pdf`;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
