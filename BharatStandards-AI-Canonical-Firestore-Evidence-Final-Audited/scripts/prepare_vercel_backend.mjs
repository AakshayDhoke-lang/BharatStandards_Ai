import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceApp = path.join(root, "backend", "app");
const target = path.join(root, "vercel-backend");
const targetApp = path.join(target, "app");

fs.rmSync(targetApp, { recursive: true, force: true });
fs.mkdirSync(targetApp, { recursive: true });
fs.cpSync(sourceApp, targetApp, {
  recursive: true,
  filter(src) {
    return !src.includes("__pycache__") && !src.endsWith(".pyc");
  },
});

console.log("Vercel backend synchronized from backend/app -> vercel-backend/app");
console.log("Deploy with: cd vercel-backend && vercel --prod");
