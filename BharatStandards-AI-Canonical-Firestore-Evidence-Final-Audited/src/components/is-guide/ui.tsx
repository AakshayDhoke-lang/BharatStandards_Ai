import { Link, useLocation } from "react-router-dom";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  BarChart3, Bell, BookOpen, Boxes, BrainCircuit, ChevronDown, ChevronLeft, ChevronRight,
  CircleHelp, ClipboardCheck, Database, FileClock, FileSearch, FolderSearch2, History, Languages,
  LogOut, Menu, Network, PanelLeftClose, PanelLeftOpen, Search, Settings, ShieldCheck, Sparkles,
  Home, MoreHorizontal, Activity,
  UploadCloud, UserRound, X, Command, Check, AlertTriangle, CircleDot, Copy, Filter, SlidersHorizontal, Wrench,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { checkBackendHealth, checkModelConnection } from "@/lib/api";
import { DEMO_MODE } from "@/lib/demo-mode";


const navSections: { label: string; items: { label: string; to: string; icon: LucideIcon }[] }[] = [
  { label: "OVERVIEW", items: [{ label: "Dashboard", to: "/", icon: BarChart3 }, { label: "Analyze Tender", to: "/analyze", icon: FileSearch }] },
  { label: "INTELLIGENCE", items: [{ label: "Standards Explorer", to: "/standards", icon: BookOpen }, { label: "Product Explorer", to: "/products", icon: Boxes }, { label: "Categories", to: "/categories", icon: Database }, { label: "Standards Relationships", to: "/relationships", icon: Network }] },
  { label: "COMPLIANCE", items: [{ label: "Certification & QCO", to: "/certification", icon: ShieldCheck }, { label: "Amendments & Versions", to: "/amendments", icon: FileClock }, { label: "Compliance Explorer", to: "/compliance", icon: ClipboardCheck }] },
  { label: "ANALYSIS", items: [{ label: "Analysis History", to: "/history", icon: History }, { label: "Evaluation Dashboard", to: "/evaluation", icon: BarChart3 }] },
  { label: "DATA", items: [{ label: "Data Sources", to: "/sources", icon: Database }, { label: "Data Ingestion", to: "/ingestion", icon: UploadCloud }, { label: "Review Queue", to: "/review", icon: FolderSearch2 }, { label: "Data Activity", to: "/activity", icon: Activity }] },
  { label: "SYSTEM", items: [{ label: "Settings", to: "/settings", icon: Settings }, { label: "System Diagnostics", to: "/diagnostics", icon: Wrench }] },
];

export function Logo({ compact = false, inverse = false }: { compact?: boolean; inverse?: boolean }) {
  return <div className="flex min-w-0 items-center gap-3"><div className={cn("relative grid h-9 w-9 shrink-0 place-items-center rounded-md border", inverse ? "border-sidebar-border bg-sidebar-accent" : "border-primary/20 bg-primary")}><FileSearch className="h-5 w-5 text-primary-foreground"/><span className="absolute -bottom-1 -right-1 grid h-4 w-4 place-items-center rounded-sm bg-ai text-[9px] text-primary-foreground"><Check className="h-3 w-3"/></span></div>{!compact && <div className="min-w-0"><div className={cn("font-semibold", inverse ? "text-sidebar-foreground" : "text-navy")}>BharatStandards <span className="text-ai">AI</span></div><div className={cn("truncate text-[10px]", inverse ? "text-sidebar-foreground/65" : "text-muted-foreground")}>Indian Standards Intelligence</div></div>}</div>
}

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [mobileMoreOpen, setMobileMoreOpen] = useState(false);
  const [backendState, setBackendState] = useState<"checking"|"connected"|"offline">("checking");
  const [modelState, setModelState] = useState<"checking"|"connected"|"offline">("checking");
  const [aiProviderLabel, setAiProviderLabel] = useState("AI Model");
  const [notifications, setNotifications] = useState(DEMO_MODE ? [
    { id: 1, title: "Version review required", detail: "IS 694 : 2010 has a revision record awaiting verification.", to: "/review", read: false },
    { id: 2, title: "Upcoming QCO", detail: "A tracked QCO becomes effective later this year.", to: "/certification", read: false },
  ] : []);
  const [language, setLanguage] = useState(() => localStorage.getItem("bsai.language") || "en");
  const collapseTimer = useRef<number | null>(null);
  const { pathname } = useLocation();
  const { user, role, logout } = useAuth();
  const displayName = user?.displayName || user?.email?.split("@")[0] || "User";
  const initials = displayName.split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase() || "BS";
  const languageLabel = language === "hi" ? "हिन्दी" : language === "mr" ? "मराठी" : "English";
  const unread = notifications.filter(n=>!n.read).length;

  useEffect(() => { const fn = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setSearchOpen(true); } }; window.addEventListener("keydown", fn); return () => window.removeEventListener("keydown", fn); }, []);
  useEffect(() => {
    let alive = true;
    const check = () => {
      setModelState("checking");
      checkBackendHealth().then((health) => { if (alive) { setBackendState("connected"); setAiProviderLabel(health.aiProvider === "lmstudio" ? "LM Studio" : health.aiProvider === "nvidia" ? "NVIDIA" : "AI Model"); } }).catch(() => { if (alive) { setBackendState("offline"); setModelState("offline"); } });
      checkModelConnection().then((result) => { if (alive) { setModelState("connected"); setAiProviderLabel(result.provider === "lmstudio" ? "LM Studio" : result.provider === "nvidia" ? "NVIDIA" : "AI Model"); } }).catch(() => { if (alive) setModelState("offline"); });
    };
    check();
    window.addEventListener("bsai-ai-provider-change", check);
    return () => { alive = false; window.removeEventListener("bsai-ai-provider-change", check); };
  }, []);
  useEffect(() => {
    const fn = () => setLanguage(localStorage.getItem("bsai.language") || "en");
    window.addEventListener("bsai-language-change", fn);
    return () => window.removeEventListener("bsai-language-change", fn);
  }, []);
  const setLang=(v:string)=>{ setLanguage(v); localStorage.setItem("bsai.language",v); window.dispatchEvent(new Event("bsai-language-change")); };
  const labels = navSections.flatMap((s) => s.items);
  const current = labels.find((x) => x.to === pathname)?.label ?? (pathname.startsWith("/standards/") ? "Standard Details" : "Workspace");
  const statusDot=(state:string)=>cn("h-2 w-2 rounded-full", state==="connected"?"bg-success":state==="offline"?"bg-destructive":"bg-warning animate-pulse");
  const statusText=(state:string)=>state==="connected"?"Connected":state==="offline"?"Offline":"Checking";

  useEffect(() => {
    if (!mobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") setMobileOpen(false); };
    window.addEventListener("keydown", onKeyDown);
    return () => { document.body.style.overflow = previousOverflow; window.removeEventListener("keydown", onKeyDown); };
  }, [mobileOpen]);

  return <div className="flex min-h-dvh w-full min-w-0 overflow-x-clip bg-background">
    {mobileOpen && <button aria-label="Close navigation overlay" className="fixed inset-0 z-40 bg-foreground/30 lg:hidden" onClick={() => setMobileOpen(false)}/>} 
    <aside
      onMouseEnter={() => { if (collapseTimer.current) window.clearTimeout(collapseTimer.current); if (window.innerWidth >= 1024) setCollapsed(false); }}
      onMouseLeave={() => { if (window.innerWidth >= 1024) collapseTimer.current = window.setTimeout(() => setCollapsed(true), 280); }}
      className={cn("fixed inset-y-0 left-0 z-50 flex max-w-[88vw] flex-col overflow-hidden bg-sidebar text-sidebar-foreground shadow-xl transition-[width,transform] duration-300 ease-out lg:max-w-none lg:translate-x-0", collapsed ? "w-[72px]" : "w-60", mobileOpen ? "translate-x-0 w-60" : "-translate-x-full")}
    >
      <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-4"><Logo compact={collapsed && !mobileOpen} inverse/><Button variant="ghost" size="icon" className="text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground" onClick={() => { if (window.innerWidth < 1024) setMobileOpen(false); else setCollapsed((value) => !value); }}>{collapsed ? <PanelLeftOpen/> : <><X className="lg:hidden"/><PanelLeftClose className="hidden lg:block"/></>}<span className="sr-only">Toggle sidebar</span></Button></div>
      <nav className="scrollbar-thin flex-1 overflow-y-auto px-2 py-4" aria-label="Main navigation">{navSections.map((section) => <div key={section.label} className="mb-4"><p className={cn("mb-1 px-3 text-[10px] font-semibold text-sidebar-foreground/45", collapsed && !mobileOpen && "sr-only")}>{section.label}</p><div className="space-y-0.5">{section.items.map((item) => { if(item.to === "/diagnostics" && role!=="ADMIN") return null; const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to); return <Link key={item.to} to={item.to} onClick={() => { setMobileOpen(false); if (window.innerWidth >= 1024) setCollapsed(true); }} title={collapsed ? item.label : undefined} className={cn("relative flex h-9 items-center gap-3 rounded-md px-3 text-[13px] text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-foreground", active && "bg-sidebar-accent font-medium text-sidebar-foreground before:absolute before:inset-y-2 before:left-0 before:w-0.5 before:bg-ai", collapsed && !mobileOpen && "justify-center px-0")}><item.icon className="h-4 w-4 shrink-0"/>{(!collapsed || mobileOpen) && <span>{item.label}</span>}</Link>})}</div></div>)}</nav>
      <div className="border-t border-sidebar-border p-3">{!collapsed || mobileOpen ? <div className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-md bg-sidebar-accent text-xs font-semibold">{initials}</div><div className="min-w-0 flex-1"><p className="truncate text-xs font-medium">{displayName}</p><p className="truncate text-[10px] text-sidebar-foreground/60">{user?.email || "Standards Workspace"}</p></div><Button variant="ghost" size="icon" className="h-8 w-8 text-sidebar-foreground/70 hover:bg-sidebar-accent" onClick={()=>void logout()}><LogOut className="h-4 w-4"/><span className="sr-only">Sign out</span></Button></div> : <div className="grid h-9 w-full place-items-center rounded-md bg-sidebar-accent text-xs font-semibold">{initials}</div>}</div>
    </aside>
    <div className="min-w-0 flex-1 overflow-x-clip lg:ml-[72px]" onClick={() => { if (window.innerWidth >= 1024 && !collapsed) setCollapsed(true); }}>
      <header className="sticky top-0 z-30 flex min-h-16 min-w-0 items-center gap-2 border-b bg-card px-3 py-2 sm:gap-3 sm:px-4 lg:px-6"><Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMobileOpen(true)}><Menu/><span className="sr-only">Open navigation</span></Button><div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex"><span>BharatStandards AI</span><ChevronRight className="h-3 w-3"/><span className="font-medium text-foreground">{current}</span></div>
      <div className="ml-auto flex items-center gap-1.5">
        <div className="hidden items-center gap-2 rounded-md border bg-background px-2.5 py-1.5 lg:flex" title="Live backend and selected AI provider connectivity"><span className={statusDot(backendState)}/><span className="text-[11px]">Backend {statusText(backendState)}</span><span className="h-4 w-px bg-border"/><span className={statusDot(modelState)}/><span className="text-[11px]">{aiProviderLabel} {statusText(modelState)}</span></div>
        <button onClick={() => setSearchOpen(true)} className="hidden h-9 w-[min(31vw,360px)] items-center gap-2 rounded-md border bg-background px-3 text-left text-sm text-muted-foreground hover:border-primary/50 md:flex"><Search className="h-4 w-4"/><span className="flex-1 truncate">Search IS number, product, category...</span><kbd className="rounded border bg-card px-1.5 py-0.5 text-[10px]">Ctrl K</kbd></button><Button variant="ghost" size="icon" className="md:hidden" onClick={() => setSearchOpen(true)}><Search/></Button>
        <DropdownMenu><DropdownMenuTrigger asChild><Button variant="ghost" size="sm" className="hidden gap-1 text-xs sm:inline-flex"><Languages/> {languageLabel} <ChevronDown className="h-3 w-3"/></Button></DropdownMenuTrigger><DropdownMenuContent align="end"><DropdownMenuItem onClick={()=>setLang("en")}>English</DropdownMenuItem><DropdownMenuItem onClick={()=>setLang("hi")}>हिन्दी</DropdownMenuItem><DropdownMenuItem onClick={()=>setLang("mr")}>मराठी</DropdownMenuItem></DropdownMenuContent></DropdownMenu>
        <Button variant="ghost" size="icon" asChild><Link to="/settings"><CircleHelp/><span className="sr-only">Help</span></Link></Button>
        <Popover><PopoverTrigger asChild><Button variant="ghost" size="icon" className="relative"><Bell/>{unread>0&&<span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-warning"/>}<span className="sr-only">Notifications</span></Button></PopoverTrigger><PopoverContent align="end" className="w-80 p-0"><div className="flex items-start justify-between gap-3 border-b px-4 py-3"><div><p className="text-sm font-semibold text-navy">Notifications</p><p className="text-xs text-muted-foreground">{unread} unread · {notifications.length} total</p></div><div className="flex gap-1"><Button size="sm" variant="ghost" className="h-7 px-2 text-[10px]" disabled={!unread} onClick={()=>setNotifications(n=>n.map(x=>({...x,read:true})))}>Mark as read</Button><Button size="sm" variant="ghost" className="h-7 px-2 text-[10px]" disabled={!notifications.length} onClick={()=>setNotifications([])}>Clear</Button></div></div><div className="divide-y">{notifications.length?notifications.map(n=><Link key={n.id} to={n.to} onClick={()=>setNotifications(items=>items.map(x=>x.id===n.id?{...x,read:true}:x))} className={cn("block p-4 hover:bg-muted/50",!n.read&&"bg-warning-soft/40")}><div className="flex items-start gap-2"><span className={cn("mt-1 h-2 w-2 shrink-0 rounded-full",n.read?"bg-muted-foreground/30":"bg-warning")}/><div><p className="text-sm font-medium">{n.title}</p><p className="mt-1 text-xs text-muted-foreground">{n.detail}</p></div></div></Link>):<div className="p-6 text-center text-xs text-muted-foreground">No notifications.</div>}</div></PopoverContent></Popover>
        <DropdownMenu><DropdownMenuTrigger asChild><button aria-label="Open profile menu" className="ml-1 grid h-8 w-8 place-items-center rounded-md bg-navy text-xs font-semibold text-primary-foreground">{initials}</button></DropdownMenuTrigger><DropdownMenuContent align="end" className="w-52"><DropdownMenuLabel><div className="max-w-44 truncate">{displayName}</div><div className="max-w-44 truncate text-[10px] font-normal text-muted-foreground">{user?.email}</div></DropdownMenuLabel><DropdownMenuSeparator/><DropdownMenuItem asChild><Link to="/settings"><Settings className="h-4 w-4"/>Settings</Link></DropdownMenuItem><DropdownMenuItem onClick={()=>void logout()}><LogOut className="h-4 w-4"/>Sign out</DropdownMenuItem></DropdownMenuContent></DropdownMenu>
      </div></header>
      {DEMO_MODE?<div className="border-b border-warning/20 bg-warning-soft px-4 py-2 text-center text-[11px] font-medium text-warning lg:px-6">DEMO DATA MODE · Testing records only — not official BIS data</div>:<div className="border-b border-success/20 bg-success-soft px-4 py-2 text-center text-[11px] font-medium text-success lg:px-6">REAL DATA MODE · Demo records are hidden</div>}
      <main className="min-w-0 w-full p-3 pb-24 sm:p-4 sm:pb-24 lg:p-6 lg:pb-6 xl:p-8">{children}</main>
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t bg-card/95 px-2 pb-[max(env(safe-area-inset-bottom),.4rem)] pt-2 shadow-[0_-8px_24px_rgba(0,0,0,.08)] backdrop-blur lg:hidden" aria-label="Mobile navigation">
        {[{label:"Home",to:"/",icon:Home},{label:"Analyze",to:"/analyze",icon:FileSearch},{label:"Standards",to:"/standards",icon:BookOpen}].map(item=>{const Icon=item.icon;const active=item.to==="/"?pathname==="/":pathname.startsWith(item.to);return <Link key={item.to} to={item.to} className={cn("flex min-h-12 flex-col items-center justify-center gap-1 rounded-md text-[10px] font-medium",active?"text-primary":"text-muted-foreground")}><Icon className="h-5 w-5"/>{item.label}</Link>})}
        <button type="button" onClick={()=>setMobileMoreOpen(true)} className="flex min-h-12 flex-col items-center justify-center gap-1 rounded-md text-[10px] font-medium text-muted-foreground"><MoreHorizontal className="h-5 w-5"/>More</button>
      </nav>
    </div><GlobalSearch open={searchOpen} onOpenChange={setSearchOpen}/><Dialog open={mobileMoreOpen} onOpenChange={setMobileMoreOpen}><DialogContent className="top-auto bottom-0 translate-y-0 rounded-b-none p-4 sm:max-w-lg lg:hidden"><DialogHeader><DialogTitle>More</DialogTitle><DialogDescription>Open another BharatStandards AI workspace.</DialogDescription></DialogHeader><div className="grid grid-cols-2 gap-2">{navSections.flatMap(s=>s.items).filter(item=>!["/","/analyze","/standards"].includes(item.to) && !(item.to==="/diagnostics" && role!=="ADMIN")).map(item=>{const Icon=item.icon;return <Button key={item.to} variant="outline" className="h-auto min-h-14 justify-start whitespace-normal text-left" asChild><Link to={item.to} onClick={()=>setMobileMoreOpen(false)}><Icon className="h-4 w-4 shrink-0"/><span className="break-words">{item.label}</span></Link></Button>})}</div></DialogContent></Dialog>
  </div>
}

function GlobalSearch({ open, onOpenChange }: { open: boolean; onOpenChange: (v:boolean)=>void }) {
  const [query, setQuery] = useState("");
  const results = useMemo(() => (DEMO_MODE ? [
    { type: "Standards", title: "IS 374 : 2019", detail: "Electric ceiling type fans", to: "/standards/IS-374" },
    { type: "Standards", title: "IS 302-2-80 : 2017", detail: "Safety requirements for fans", to: "/standards/IS-302" },
    { type: "Products", title: "Ceiling Fan", detail: "Electrical Appliances", to: "/products" },
    { type: "Analyses", title: "ANL-1048", detail: "Ceiling fans for government schools", to: "/results" },
    { type: "QCO", title: "Electric Fans QCO, 2024", detail: "Active since 05 Mar 2025", to: "/certification" },
  ] : []).filter((r) => `${r.title} ${r.detail}`.toLowerCase().includes(query.toLowerCase())), [query]);
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="top-[12%] translate-y-0 gap-0 overflow-hidden p-0 sm:max-w-2xl"><DialogHeader className="sr-only"><DialogTitle>Global search</DialogTitle><DialogDescription>Search standards, products, analyses and compliance records.</DialogDescription></DialogHeader><div className="flex items-center gap-3 border-b px-4"><Search className="h-5 w-5 text-muted-foreground"/><Input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} className="h-14 border-0 bg-transparent px-0 shadow-none focus-visible:ring-0" placeholder="Search standards, products, analyses and QCOs..."/></div><div className="max-h-[420px] overflow-auto p-2">{results.map((r) => <Link key={`${r.type}-${r.title}`} to={r.to} onClick={() => onOpenChange(false)} className="flex items-center gap-3 rounded-md px-3 py-3 hover:bg-muted"><div className="grid h-8 w-8 place-items-center rounded-md bg-secondary text-primary"><FileSearch className="h-4 w-4"/></div><div className="min-w-0 flex-1"><p className="text-[11px] font-semibold uppercase text-muted-foreground">{r.type}</p><p className="text-sm font-medium">{r.title}</p><p className="truncate text-xs text-muted-foreground">{r.detail}</p></div><ChevronRight className="h-4 w-4 text-muted-foreground"/></Link>)}</div><div className="flex justify-between border-t bg-muted/50 px-4 py-2 text-[11px] text-muted-foreground"><span>Use ↑ ↓ to navigate · Enter to open</span><span>Esc to close</span></div></DialogContent></Dialog>
}

export function PageHeader({ title, description, actions }: { title: string; description: string; actions?: ReactNode }) { return <div className="mb-5 flex min-w-0 flex-col justify-between gap-4 sm:mb-6 sm:flex-row sm:items-start"><div className="min-w-0"><h1 className="break-words text-2xl font-semibold leading-tight text-navy sm:text-[28px]">{title}</h1><p className="mt-1 max-w-3xl break-words text-sm text-muted-foreground">{description}</p></div>{actions && <div className="flex min-w-0 shrink-0 flex-wrap gap-2 [&>*]:max-w-full">{actions}</div>}</div> }

export function Panel({ title, description, action, children, className }: { title?: string; description?: string; action?: ReactNode; children: ReactNode; className?: string }) { return <section className={cn("app-card min-w-0", className)}>{(title || action) && <div className="flex min-w-0 flex-col items-start justify-between gap-3 border-b px-4 py-4 sm:flex-row sm:px-5"><div className="min-w-0"><h2 className="break-words text-base font-semibold text-navy">{title}</h2>{description && <p className="mt-0.5 break-words text-xs text-muted-foreground">{description}</p>}</div>{action && <div className="max-w-full shrink-0">{action}</div>}</div>}<div className="min-w-0 p-4 sm:p-5">{children}</div></section> }

export function StatusBadge({ children, tone }: { children: ReactNode; tone?: "success"|"warning"|"danger"|"info"|"neutral"|"ai" }) { const t = tone ?? (/verified|active|complete|covered|latest|connected/i.test(String(children)) ? "success" : /review|upcoming|outdated|attention|partial/i.test(String(children)) ? "warning" : /failed|withdrawn|missing|rejected/i.test(String(children)) ? "danger" : /AI|recommended|processing/i.test(String(children)) ? "ai" : "neutral"); return <span className={cn("inline-flex max-w-full items-center gap-1 whitespace-normal break-words rounded-md border px-2 py-1 text-[10px] font-semibold uppercase", t === "success" && "border-success/20 bg-success-soft text-success", t === "warning" && "border-warning/25 bg-warning-soft text-warning", t === "danger" && "border-destructive/20 bg-destructive/10 text-destructive", t === "info" && "border-info/20 bg-info-soft text-info", t === "ai" && "border-ai/30 bg-ai-soft text-ai", t === "neutral" && "bg-muted text-muted-foreground")}>{children}</span> }

export function DataTable({ columns, rows, onRowClick }: { columns: string[]; rows: (ReactNode[])[]; onRowClick?: (index:number)=>void }) { const [sortIndex, setSortIndex] = useState<number|null>(null); const [asc, setAsc] = useState(true); const sorted = useMemo(() => sortIndex === null ? rows : [...rows].sort((a,b) => String(a[sortIndex]).localeCompare(String(b[sortIndex])) * (asc ? 1 : -1)), [rows,sortIndex,asc]); return <div className="min-w-0">
  <div className="space-y-3 md:hidden">{sorted.map((row,ri)=><div key={ri} onClick={()=>onRowClick?.(ri)} className={cn("rounded-md border bg-card p-3",onRowClick&&"cursor-pointer active:bg-muted/60")}>{row.map((cell,ci)=><div key={ci} className="grid min-w-0 grid-cols-[minmax(92px,0.4fr)_minmax(0,1fr)] gap-3 border-b py-2 first:pt-0 last:border-0 last:pb-0"><div className="break-words text-[10px] font-semibold uppercase text-muted-foreground">{columns[ci]}</div><div className="min-w-0 break-words text-[13px] [&_*]:max-w-full">{cell}</div></div>)}</div>)}</div>
  <div className="hidden max-w-full overflow-x-auto md:block"><table className="w-full min-w-[760px] border-collapse text-left text-[13px]"><thead className="sticky top-0 bg-muted/80"><tr>{columns.map((c,i) => <th key={c} className="whitespace-nowrap border-b px-4 py-3 text-[11px] font-semibold uppercase text-muted-foreground"><button className="inline-flex items-center gap-1 hover:text-foreground" onClick={() => { if(sortIndex===i) setAsc(!asc); else {setSortIndex(i);setAsc(true)} }}>{c}{sortIndex===i && <ChevronDown className={cn("h-3 w-3", !asc && "rotate-180")}/>}</button></th>)}</tr></thead><tbody>{sorted.map((row,ri) => <tr key={ri} onClick={() => onRowClick?.(ri)} className={cn("border-b last:border-0", onRowClick && "cursor-pointer hover:bg-muted/60")}>{row.map((cell,ci) => <td key={ci} className="max-w-[28rem] break-words px-4 py-3 align-middle">{cell}</td>)}</tr>)}</tbody></table></div>
</div> }

export function FilterBar({ placeholder="Search records...", children, onSearch, onClear, advancedContent }: { placeholder?: string; children?: ReactNode; onSearch?: (value:string)=>void; onClear?: ()=>void; advancedContent?: ReactNode }) {
  const [value,setValue]=useState(""); const [advanced,setAdvanced]=useState(false);
  useEffect(()=>{const id=setTimeout(()=>onSearch?.(value),250);return()=>clearTimeout(id)},[value,onSearch]);
  const clear=()=>{setValue("");setAdvanced(false);onClear?.();};
  return <div className="mb-4 min-w-0"><div className="flex min-w-0 flex-col gap-2 md:flex-row md:flex-wrap"><div className="relative min-w-0 flex-1 md:min-w-60"><Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground"/><Input value={value} onChange={(e)=>setValue(e.target.value)} placeholder={placeholder} className="pl-9"/></div>{children}{advancedContent&&<Button type="button" variant={advanced?"secondary":"outline"} onClick={()=>setAdvanced(v=>!v)}><SlidersHorizontal/> Advanced</Button>}<Button type="button" variant="ghost" onClick={clear}>Clear</Button></div>{advanced&&advancedContent&&<div className="mt-3 rounded-md border bg-muted/25 p-3">{advancedContent}</div>}</div>
}

export function Pagination({ count = 48 }: { count?: number }) { const [page,setPage]=useState(1); return <div className="flex flex-col gap-3 border-t px-4 py-3 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between"><span>Showing {(page-1)*10+1}–{Math.min(page*10,count)} of {count}</span><div className="flex items-center gap-1"><Button type="button" size="icon" variant="outline" aria-label="Previous page" disabled={page===1} onClick={()=>setPage(p=>Math.max(1,p-1))}><ChevronLeft/></Button><span className="px-3 font-medium text-foreground">Page {page} of {Math.ceil(count/10)}</span><Button type="button" size="icon" variant="outline" aria-label="Next page" disabled={page===Math.ceil(count/10)} onClick={()=>setPage(p=>Math.min(Math.ceil(count/10),p+1))}><ChevronRight/></Button></div></div> }

export function EmptyState({ title="No records found", description="Try changing your search terms or filters.", action }: { title?:string; description?:string; action?:ReactNode }) { return <div className="grid min-h-64 place-items-center text-center"><div><div className="mx-auto grid h-11 w-11 place-items-center rounded-md bg-muted text-muted-foreground"><FolderSearch2/></div><h3 className="mt-3 font-semibold">{title}</h3><p className="mt-1 text-sm text-muted-foreground">{description}</p>{action && <div className="mt-4">{action}</div>}</div></div> }

export { AlertTriangle, BrainCircuit, Check, CircleDot, Command, Copy, Filter, Search, Sparkles, UserRound };
