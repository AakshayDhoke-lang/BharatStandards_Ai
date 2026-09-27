const ENV_DEFAULT = String(import.meta.env.VITE_DEMO_MODE ?? "false").toLowerCase() === "true";

function readOverride(): boolean | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem("bsai.demoMode");
  if (raw === "true") return true;
  if (raw === "false") return false;
  return null;
}

export const DEMO_MODE = readOverride() ?? ENV_DEFAULT;
export const DATA_MODE = DEMO_MODE ? "DEMO" : "REAL";

export function setDemoMode(enabled: boolean) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem("bsai.demoMode", String(enabled));
  window.dispatchEvent(new CustomEvent("bsai-demo-mode-change", { detail: { enabled } }));
  window.location.reload();
}

export function clearDemoModeOverride() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem("bsai.demoMode");
  window.location.reload();
}
