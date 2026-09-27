import fs from "node:fs";
import path from "node:path";
const value = (process.argv[2] || "").toLowerCase();
if (!["on","off"].includes(value)) {
  console.error("Usage: node scripts/set_demo_mode.mjs on|off"); process.exit(1);
}
const enabled = value === "on";
const envPath = path.resolve(".env");
let text = fs.existsSync(envPath) ? fs.readFileSync(envPath,"utf8") : "";
function setVar(name,val){
  const re = new RegExp(`^${name}=.*$`,"m");
  if(re.test(text)) text=text.replace(re,`${name}=${val}`); else text += `${text.endsWith("\n")?"":"\n"}${name}=${val}\n`;
}
setVar("VITE_DEMO_MODE", String(enabled));
setVar("DEMO_MODE", String(enabled));
fs.writeFileSync(envPath,text);
console.log(`BharatStandards AI DEMO mode: ${enabled?"ENABLED":"DISABLED"}`);
console.log("Restart npm run dev:full for the frontend/backend to reload the mode.");
