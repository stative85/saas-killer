import { TriageArtifact } from "@wendigo/contracts";

/**
 * CalculateApexScore
 * 
 * The cold, mathematical heart of Wendigo.
 * Determines if a contender survives the crucible and ranks them for apex selection.
 * 
 * Logic:
 * 1. Hard fail on compile failure, fatal errors, or regression introduction.
 * 2. Require a minimum fuzzing depth (10k iterations).
 * 3. Weighted score based on invariants, boundary purity, performance, and minimality.
 */
export function CalculateApexScore(artifact: TriageArtifact): number {
  // Hard Kill Criteria
  if (artifact.isFatality || artifact.compileDelta === "FAILED") return 0;
  if (artifact.fuzzScore < 10000) return 0;
  if (artifact.regressionCount > 0) return 0;

  let score = 0;
  
  // Weights
  // 30% - Invariant Success
  score += 0.30 * artifact.invariantScore;
  
  // 25% - Baseline Stability (Assuming 1.0 if passed regression)
  score += 0.25 * 1.0;
  
  // 15% - Boundary Purity (AST isolation)
  score += 0.15 * (artifact.boundaryPurity / 100);
  
  // 10% - Fuzzing Confidence (Assuming 1.0 if passed threshold)
  score += 0.10 * 1.0;

  // 10% - Performance Impact (Penalize latency > 10ms)
  const perfWeight = Math.max(0, 1.0 - artifact.latencyVarianceMs / 10);
  score += 0.10 * perfWeight;

  // 5% - Minimality (Penalize large diffs > 20 lines)
  const minimalityWeight = Math.max(0, 1.0 - artifact.unifiedDiffLength / 20);
  score += 0.05 * minimalityWeight;

  // Ensure even a perfect score is strictly capped, and surviving patches get a baseline.
  return Math.max(0.001, score);
}
