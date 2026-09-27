import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { cert, getApps, initializeApp } from "firebase-admin/app";
import { getFirestore, FieldValue } from "firebase-admin/firestore";

const projectId = process.env.FIREBASE_PROJECT_ID || "bharatstandards-ai";
const serviceAccountPath = process.env.FIREBASE_SERVICE_ACCOUNT_PATH;
if (!serviceAccountPath) {
  console.error("FIREBASE_SERVICE_ACCOUNT_PATH is required. Point it to a Firebase service-account JSON file.");
  process.exit(1);
}
const absolute = path.resolve(serviceAccountPath);
if (!fs.existsSync(absolute)) {
  console.error(`Service-account file not found: ${absolute}`);
  process.exit(1);
}
const serviceAccount = JSON.parse(fs.readFileSync(absolute, "utf8"));
const app = getApps()[0] ?? initializeApp({ credential: cert(serviceAccount), projectId });
const db = getFirestore(app);
const root = db.collection("datasets").doc("demo");

const standards = [
  { id:"DEMO_IS_374_2019", designation:"DEMO IS 374 : 2019", title:"Demo electric ceiling fan specification", domain:"Electrical Appliances", category:"Fans", year:2019, status:"ACTIVE", dataMode:"DEMO" },
  { id:"DEMO_IS_302_2_80_2017", designation:"DEMO IS 302-2-80 : 2017", title:"Demo safety requirements for fans", domain:"Electrical Appliances", category:"Safety", year:2017, status:"ACTIVE", dataMode:"DEMO" },
  { id:"DEMO_IS_2062_2011", designation:"DEMO IS 2062 : 2011", title:"Demo structural steel specification", domain:"Materials & Structural", category:"Steel", year:2011, status:"ACTIVE", dataMode:"DEMO" },
  { id:"DEMO_IS_456_2000", designation:"DEMO IS 456 : 2000", title:"Demo concrete code of practice", domain:"Civil Engineering", category:"Concrete", year:2000, status:"ACTIVE", dataMode:"DEMO" },
  { id:"DEMO_IS_13252_2010", designation:"DEMO IS 13252 (Part 1) : 2010", title:"Demo IT equipment safety", domain:"Electronics & IT", category:"Computing", year:2010, status:"SUPERSEDED", dataMode:"DEMO" },
];
const products = [
  {id:"ceiling_fan",name:"Ceiling Fan",domain:"Electrical Appliances",aliases:["ceiling fan","electric fan"],dataMode:"DEMO"},
  {id:"steel_plate",name:"Structural Steel Plate",domain:"Materials & Structural",aliases:["steel plate"],dataMode:"DEMO"},
  {id:"desktop_computer",name:"Desktop Computer",domain:"Electronics & IT",aliases:["desktop pc"],dataMode:"DEMO"},
  {id:"ready_mixed_concrete",name:"Ready Mixed Concrete",domain:"Civil Engineering",aliases:["RMC"],dataMode:"DEMO"},
];
const evaluations = [
  ["civil","Civil Engineering",120,94,99,96],
  ["electrical","Electrical Appliances",148,95,99,97],
  ["electronics","Electronics & IT",96,89,96,92],
  ["materials","Materials & Structural",112,91,97,93],
].map(([id,domain,queries,top1,top3,certification])=>({id,domain,queries,top1,top3,certification,dataMode:"DEMO"}));

const batch = db.batch();
batch.set(root, { name:"BharatStandards AI Demo Dataset", dataMode:"DEMO", updatedAt:FieldValue.serverTimestamp() }, { merge:true });
for (const item of standards) batch.set(root.collection("standards").doc(item.id), { ...item, updatedAt:FieldValue.serverTimestamp() });
for (const item of products) batch.set(root.collection("products").doc(item.id), { ...item, updatedAt:FieldValue.serverTimestamp() });
for (const item of evaluations) batch.set(root.collection("evaluationQueries").doc(item.id), { ...item, updatedAt:FieldValue.serverTimestamp() });
await batch.commit();
console.log(`Seeded DEMO dataset into Firestore project ${projectId}: datasets/demo/...`);
console.log("No records were written to datasets/real.");
