import fs from "node:fs";

const raw = process.argv[2]?.trim();
if (!raw) {
  console.error("Usage: npm run api:production -- https://your-backend.vercel.app");
  process.exit(1);
}
let url;
try {
  url = new URL(raw);
} catch {
  console.error("The backend URL is not a valid absolute URL.");
  process.exit(1);
}
if (url.protocol !== "https:") {
  console.error("Production API URL must use https://");
  process.exit(1);
}
const base = raw.replace(/\/$/, "");
fs.writeFileSync(".env.production.local", `VITE_API_BASE_URL=${base}\n`, "utf8");
console.log(`Production frontend API set to ${base}`);
console.log("Next: npm run build && firebase deploy --only hosting");
