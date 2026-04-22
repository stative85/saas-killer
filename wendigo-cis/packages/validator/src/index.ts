import { RepoRuntime } from "@wendigo/repo-runtime";
import { ContenderPatch, InvariantSpec, TriageArtifact } from "@wendigo/contracts";
import { CalculateApexScore } from "./scoring";
import fs from "node:fs/promises";
import path from "node:path";

export class Validator {
  async evaluate(
    jobId: string, 
    runtime: RepoRuntime, 
    patch: ContenderPatch, 
    invariants: InvariantSpec
  ): Promise<TriageArtifact> {
    console.log(`[VALIDATOR] Testing contender: ${patch.contenderId}`);
    
    // 1. Apply Patch
    try {
      await runtime.applyPatch(patch.unifiedDiff);
    } catch (err) {
      return this.fatality("PATCH_APPLICATION_FAILED");
    }

    // 2. Inject Invariant Tests
    for (const test of invariants.generatedTests) {
      const testPath = path.join(test.path); // Runtime workDir is handled by RepoRuntime
      // In a real impl, runtime.writeFile would be used
      // For v0 worker handles this via runtime.runCommand or similar
    }

    // 3. Compile Check
    const compile = await runtime.runCommand("npx", ["tsc", "--noEmit"]);
    if (compile.exitCode !== 0) {
      return this.fatality("COMPILE_FAILED");
    }

    // 4. Invariant & Regression Execution
    const testRun = await runtime.runCommand("npm", ["test"]);
    const passed = testRun.exitCode === 0;

    // 5. Score Calculation
    // Mocking metrics for v0 resonance
    const artifact: TriageArtifact = {
      compileDelta: "PASSED",
      fuzzScore: 10000, 
      invariantScore: passed ? 1.0 : 0.0,
      boundaryPurity: 100,
      regressionCount: 0,
      latencyVarianceMs: 0.5,
      unifiedDiffLength: patch.unifiedDiff.split("\n").length,
      isFatality: false
    };

    return artifact;
  }

  private fatality(reason: string): TriageArtifact {
    return {
      compileDelta: "FAILED",
      fuzzScore: 0,
      invariantScore: 0,
      boundaryPurity: 0,
      regressionCount: 1,
      latencyVarianceMs: 0,
      unifiedDiffLength: 0,
      isFatality: true,
      fatalityReason: reason
    };
  }
}
