import { DEMO_MODE } from "@/lib/demo-mode";

export type StatusTone = "success" | "warning" | "danger" | "info" | "neutral" | "ai";

const metricsData = [
  { label: "Standards in Knowledge Base", value: "12,486", detail: "+184 this quarter", icon: "BookOpen" },
  { label: "Verified Standards", value: "10,942", detail: "87.6% verified", icon: "BadgeCheck" },
  { label: "Supported Product Categories", value: "328", detail: "24 domains", icon: "Boxes" },
  { label: "Analyses Completed", value: "1,846", detail: "+12.4% this month", icon: "FileCheck2" },
  { label: "QCOs Tracked", value: "742", detail: "36 upcoming", icon: "ShieldCheck" },
  { label: "Standards Needing Review", value: "68", detail: "Requires attention", icon: "CircleAlert" },
];

const recentAnalysesData = [
  { id: "ANL-1048", tender: "Ceiling fans for government schools", product: "Ceiling Fan", standard: "IS 374 : 2019", confidence: 95, compliance: 91, status: "Verified", date: "30 Aug 2026, 11:42" },
  { id: "ANL-1047", tender: "Structural steel plates — bridge works", product: "Steel Plate", standard: "IS 2062 : 2011", confidence: 89, compliance: 84, status: "Needs Review", date: "30 Aug 2026, 10:18" },
  { id: "ANL-1046", tender: "LED street lighting system", product: "LED Luminaire", standard: "IS 10322-5-3", confidence: 93, compliance: 88, status: "Completed", date: "29 Aug 2026, 16:35" },
  { id: "ANL-1045", tender: "PVC insulated electrical cables", product: "Electric Cable", standard: "IS 694 : 2010", confidence: 97, compliance: 96, status: "Verified", date: "29 Aug 2026, 14:05" },
  { id: "ANL-1044", tender: "Desktop computers for district offices", product: "Desktop PC", standard: "IS 13252 (Part 1)", confidence: 78, compliance: 72, status: "Needs Review", date: "28 Aug 2026, 17:22" },
];

const standardsData = [
  { standardId: "IS-374-2019", number: "IS 374 : 2019", title: "Electric ceiling type fans and regulators — Specification", domain: "Electrical Appliances", category: "Fans", year: 2019, status: "ACTIVE", relationships: 2, certification: "Needs Review", department: "Electrotechnical", committee: "ETD 32", reaffirmed: "2024", sourceTrust: "Tier 5 Official", verification: "Verified", lastVerified: "28 Aug 2026", scope: "Covers electric ceiling type fans and associated regulators intended for air circulation in domestic and similar environments.", includedProducts: ["Ceiling fans", "Regulators"], applications: ["Indoor air circulation", "Institutional buildings"], exclusions: ["Other fan product families unless explicitly covered"] },
  { standardId: "IS-302-2-80-2017", number: "IS 302-2-80 : 2017", title: "Safety of household electrical appliances — Fans", domain: "Electrical Appliances", category: "Safety", year: 2017, status: "ACTIVE", relationships: 12, certification: "Needs Review", department: "Electrotechnical", committee: "ETD", reaffirmed: "Needs Review", sourceTrust: "Tier 5 Official", verification: "Verified", lastVerified: "Needs Review", scope: "Safety requirements for fan appliances within the scope of this part.", includedProducts: ["Fans within scope"], applications: ["Electrical safety"], exclusions: [] },
  { standardId: "IS-2062-2011", number: "IS 2062 : 2011", title: "Hot rolled medium and high tensile structural steel", domain: "Materials & Structural", category: "Steel", year: 2011, status: "ACTIVE", relationships: 2, certification: "Needs Review", department: "Metallurgical Engineering", committee: "MTD", reaffirmed: "Needs Review", sourceTrust: "Tier 5 Official", verification: "Needs Review", lastVerified: "Needs Review", scope: "Hot rolled structural steel products within the stated grades and delivery conditions.", includedProducts: ["Structural steel plates", "Hot rolled structural steel"], applications: ["Structural fabrication", "Engineering works"], exclusions: ["Electrical cable products"] },
  { standardId: "IS-694-2010", number: "IS 694 : 2010", title: "PVC insulated cables for working voltages up to 1100 V", domain: "Electrical", category: "Cables", year: 2010, status: "REVISED", relationships: 1, certification: "Needs Review", department: "Electrotechnical", committee: "ETD", reaffirmed: "Needs Review", sourceTrust: "Tier 5 Official", verification: "Needs Review", lastVerified: "Needs Review", scope: "PVC insulated electrical cables for working voltages up to and including 1100 V.", includedProducts: ["PVC insulated electrical cables", "Building wire within scope"], applications: ["Electrical wiring"], exclusions: ["Water pipes", "Plumbing products"] },
  { standardId: "IS-456-2000", number: "IS 456 : 2000", title: "Plain and reinforced concrete — Code of practice", domain: "Civil Engineering", category: "Concrete", year: 2000, status: "ACTIVE", relationships: 18, certification: "Voluntary", department: "Civil Engineering", committee: "CED", reaffirmed: "Needs Review", sourceTrust: "Tier 5 Official", verification: "Verified", lastVerified: "Needs Review", scope: "General structural use of plain and reinforced concrete within the code scope.", includedProducts: ["Plain concrete", "Reinforced concrete"], applications: ["Structural concrete"], exclusions: [] },
  { standardId: "IS-13252-PART-1-2010", number: "IS 13252 (Part 1) : 2010", title: "Information technology equipment — Safety", domain: "Electronics & IT", category: "Computing", year: 2010, status: "SUPERSEDED", relationships: 11, certification: "QCO Active", department: "Electronics and IT", committee: "LITD", reaffirmed: "Needs Review", sourceTrust: "Tier 5 Official", verification: "Needs Review", lastVerified: "Needs Review", scope: "Safety requirements for information technology equipment within the standard scope.", includedProducts: ["Information technology equipment"], applications: ["Equipment safety"], exclusions: [] },
];

const alliedStandardsData = [
  { standard: "IS 302-2-80 : 2017", title: "Particular requirements for fans", relation: "SAFETY", applicability: "MANDATORY", mandatory: "Yes", reason: "Electrical safety requirements", status: "ACTIVE" },
  { standard: "IS 2312 : 1967", title: "Propeller type AC ventilating fans", relation: "NORMATIVE", applicability: "APPLICABLE", mandatory: "No", reason: "Referenced construction criteria", status: "ACTIVE" },
  { standard: "IS 555 : 1979", title: "Electric table type fans", relation: "TERMINOLOGY", applicability: "OPTIONAL", mandatory: "No", reason: "Common fan terminology", status: "REVISED" },
  { standard: "IS 6873 : 2019", title: "Limits and methods of measurement of radio disturbance", relation: "TEST METHOD", applicability: "APPLICABLE", mandatory: "Yes", reason: "EMC test requirements", status: "ACTIVE" },
];

const qcosData = [
  { qco: "Electric Fans (Quality Control) Order, 2024", product: "Ceiling Fans", standard: "IS 374 : 2019", ministry: "DPIIT", effective: "05 Mar 2025", status: "ACTIVE" },
  { qco: "Safety of Household Electrical Appliances Order", product: "Domestic Appliances", standard: "IS 302 (Series)", ministry: "DPIIT", effective: "15 Sep 2025", status: "ACTIVE" },
  { qco: "Solar DC Cable QCO, 2025", product: "Solar Cables", standard: "IS 17293", ministry: "MNRE", effective: "01 Dec 2026", status: "UPCOMING" },
];

const sourcesData = [
  { source: "BIS Standards Portal", authority: "Bureau of Indian Standards", trust: "Tier 5 — Official", type: "Standards", sync: "Today, 06:00", status: "Connected" },
  { source: "Gazette of India", authority: "Government of India", trust: "Tier 5 — Official", type: "QCO / Notification", sync: "Today, 05:30", status: "Connected" },
  { source: "DPIIT QCO Repository", authority: "Ministry of Commerce", trust: "Tier 4 — Government", type: "Certification", sync: "Yesterday", status: "Connected" },
  { source: "Government e-Marketplace", authority: "GeM", trust: "Tier 4 — Government", type: "Product taxonomy", sync: "28 Aug 2026", status: "Attention" },
];

export const analysisSteps = ["Document Received", "Processing Document", "Extracting Procurement Requirements", "Searching Standards", "Validating Candidates", "Checking Allied Standards", "Checking Latest Versions", "Checking Certification & QCO", "Evaluating Tender Coverage", "Generating Explanation"];

export const metrics = DEMO_MODE ? metricsData : [];
export const recentAnalyses = DEMO_MODE ? recentAnalysesData : [];
export const standards = DEMO_MODE ? standardsData : [];
export const alliedStandards = DEMO_MODE ? alliedStandardsData : [];
export const qcos = DEMO_MODE ? qcosData : [];
export const sources = DEMO_MODE ? sourcesData : [];
