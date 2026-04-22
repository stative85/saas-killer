import { execa } from "execa";
import path from "node:path";

async function main() {
  console.log("[WENDIGO] Starting local development cluster...");

  // Assuming Redis and Postgres are running locally via Docker or native
  const env = {
    ...process.env,
    NODE_ENV: "development",
    REDIS_URL: process.env.REDIS_URL || "redis://localhost:6379",
    DATABASE_URL: process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/wendigo",
  };

  const startService = (name: string, command: string, cwd: string) => {
    console.log(`[WENDIGO] Booting ${name}...`);
    const p = execa("yarn", ["run", "start"], { cwd, env });
    
    p.stdout?.on("data", (data) => console.log(`[${name}] ${data.toString().trim()}`));
    p.stderr?.on("data", (data) => console.error(`[${name} ERROR] ${data.toString().trim()}`));
    
    return p;
  };

  try {
    await Promise.all([
      startService("INGRESS", "start", path.resolve("apps/ingress-api")),
      startService("ORCHESTRATOR", "start", path.resolve("apps/orchestrator")),
      startService("WORKER", "start", path.resolve("apps/worker")),
    ]);
  } catch (err) {
    console.error("[WENDIGO] Cluster failed:", err);
    process.exit(1);
  }
}

main();
