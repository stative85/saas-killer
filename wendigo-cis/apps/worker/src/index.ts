import { Worker, Job } from "bullmq";
import { RepoRuntime } from "@wendigo/repo-runtime";
import { Slicer } from "@wendigo/slicer";
import { InvariantCompiler } from "@wendigo/invariants";
import { Arena } from "@wendigo/arena";
import { Validator } from "@wendigo/validator";
import { ArtifactStore } from "@wendigo/artifact-store";
import { Orchestrator } from "../../orchestrator/src/index";
import { CalculateApexScore } from "@wendigo/validator/src/scoring";

const artifactStore = new ArtifactStore();
const orchestrator = new Orchestrator(process.env.REDIS_URL!);
const redisConn = { connection: { url: process.env.REDIS_URL } };

// ARENA WORKER
new Worker("job.arena", async (job: Job) => {
  const { jobId } = job.data;
  const slice = JSON.parse((await artifactStore.get(`local://${jobId}/slice.json`)).toString());
  const invariants = JSON.parse((await artifactStore.get(`local://${jobId}/invariants.json`)).toString());

  const arena = new Arena();
  const contenders = await arena.conduct(jobId, slice, invariants);
  
  await artifactStore.put(jobId, "contenders.json", JSON.stringify(contenders), "application/json");
  await orchestrator.advanceJob(jobId, "ARENA_COMPLETE");
}, redisConn);

// VALIDATE WORKER
new Worker("job.validate", async (job: Job) => {
  const { jobId } = job.data;
  const contenders = JSON.parse((await artifactStore.get(`local://${jobId}/contenders.json`)).toString());
  const invariants = JSON.parse((await artifactStore.get(`local://${jobId}/invariants.json`)).toString());

  const validator = new Validator();
  const runtime = new RepoRuntime(jobId);
  
  let bestScore = 0;
  let winner = null;

  for (const patch of contenders) {
    const report = await validator.evaluate(jobId, runtime, patch, invariants);
    const score = CalculateApexScore(report);
    if (score > bestScore) {
      bestScore = score;
      winner = { patch, report, score };
    }
  }

  if (winner) {
    await artifactStore.put(jobId, "validation-winner.json", JSON.stringify(winner), "application/json");
    await orchestrator.advanceJob(jobId, "VALIDATED");
  } else {
    console.error(`[WORKER] CRUCIBLE FATALITY: No contender survived for ${jobId}`);
    await db.updateJobState(jobId, "HUMAN_REVIEW_REQUIRED");
  }
}, redisConn);

import { GithubClient } from "@wendigo/github";
import { PrReporter } from "@wendigo/pr-reporter";
import { Database } from "@wendigo/db";

const db = new Database();

// PR WORKER
new Worker("job.pr", async (job: Job) => {
  const { jobId } = job.data;
  const winnerData = JSON.parse((await artifactStore.get(`local://${jobId}/validation-winner.json`)).toString());
  const reportArtifact = JSON.parse((await artifactStore.get(`local://${jobId}/report.json`)).catch(() => "{}").toString()); // Assuming report was built in validate stage
  
  // v0 Dummy Report for PR structure
  const dummyReport = {
    vulnId: "SNYK-JS-LODASH-1001",
    cve: null,
    severity: "high",
    targetFile: "utils/merge.ts",
    executionSummary: { extractedLoc: 150, confidenceScore: 0.95, apexContender: winnerData.patch.contenderId },
    receipts: { rollbackConfidence: "HIGH" }
  };

  const prReporter = new PrReporter();
  const prTitle = prReporter.buildTitle(dummyReport as any);
  const prBody = prReporter.buildBody(dummyReport as any);

  const github = new GithubClient();
  
  try {
    const result = await github.createRemediationPr(
      1234567, // Dummy installation ID for v0
      "my-org", // Dummy owner
      "my-repo", // Dummy repo
      "main",
      dummyReport as any,
      winnerData.patch.unifiedDiff,
      "// Generated test content",
      "tests/wendigo_invariant.spec.ts",
      prTitle,
      prBody
    );

    console.log(`[WORKER] PR Generated: ${result.prUrl}`);
    await db.recordPullRequest(jobId, result.prNumber, result.prUrl, result.branchName, result.commitSha, "local://dummy-uri");
    await orchestrator.advanceJob(jobId, "PR_GENERATED");
  } catch (err) {
    console.error(`[WORKER] PR Generation failed:`, err);
  }
}, redisConn);

console.log("[WENDIGO] ALL WORKER SYSTEMS GO. MAX RPM.");
