import { TrapdoorEvent } from "../packages/contracts/src";
import axios from "axios";

const payload: TrapdoorEvent = {
  eventType: "security.alert",
  source: "snyk",
  receivedAt: new Date().toISOString(),
  repository: {
    owner: "stative85",
    name: "Chrysalis-Lattice",
    defaultBranch: "main",
    installationId: 1010101, // Mock
  },
  alert: {
    vulnId: "SNYK-JS-CHRY SALIS-PROTOTYPE-POLLUTION",
    cve: null,
    severity: "high",
    vulnType: "prototype-pollution",
    targetFile: "neuro-engine/packages/utils/src/index.ts", // Actual target in monorepo
    failingCondition: "recursive merge allows __proto__ assignment",
    advisoryUrl: "https://snyk.io/vuln/example",
    packageName: null,
    packageVersion: null,
    fixedVersion: "1.0.1",
    baseSha: "7e8a9b0c" // Mock SHA
  },
  constraints: {
    language: "typescript",
    maxFilesTouched: 1,
    maxDilationSteps: 3,
    requirePr: true,
    allowAutoMerge: false,
  },
};

async function fire() {
  console.log("[SIMULATOR] Firing Snyk alert for Chrysalis-Lattice...");
  try {
    const res = await axios.post("http://localhost:3000/webhooks/snyk", payload);
    console.log("[SIMULATOR] Response:", res.data);
  } catch (err) {
    console.error("[SIMULATOR] Failed to fire alert. Is Ingress API running?");
  }
}

fire();
