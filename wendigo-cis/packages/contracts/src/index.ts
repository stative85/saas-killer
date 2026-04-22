import { z } from "zod";

export type JobState =
  | "RECEIVED"
  | "REPO_PREPARED"
  | "SLICED"
  | "INVARIANTS_COMPILED"
  | "ARENA_COMPLETE"
  | "VALIDATED"
  | "PR_GENERATED"
  | "DONE"
  | "FAILED"
  | "HUMAN_REVIEW_REQUIRED";

export const TrapdoorEventSchema = z.object({
  eventType: z.literal("security.alert"),
  source: z.enum(["snyk", "dependabot"]),
  receivedAt: z.string(),
  repository: z.object({
    owner: z.string(),
    name: z.string(),
    defaultBranch: z.string(),
    installationId: z.number(),
  }),
  alert: z.object({
    vulnId: z.string(),
    cve: z.string().nullable(),
    severity: z.enum(["low", "medium", "high", "critical"]),
    vulnType: z.string(),
    targetFile: z.string(),
    failingCondition: z.string(),
    advisoryUrl: z.string().nullable(),
    packageName: z.string().nullable(),
    packageVersion: z.string().nullable(),
    fixedVersion: z.string().nullable(),
    baseSha: z.string().nullable(),
  }),
  constraints: z.object({
    language: z.literal("typescript"),
    maxFilesTouched: z.number().int().positive(),
    maxDilationSteps: z.number().int().positive(),
    requirePr: z.literal(true),
    allowAutoMerge: z.literal(false),
  }),
});

export type TrapdoorEvent = z.infer<typeof TrapdoorEventSchema>;

export interface SliceArtifact {
  jobId: string;
  targetFile: string;
  selectedFiles: Array<{
    path: string;
    content: string;
    role: "target" | "dependency" | "type" | "test" | "utility";
  }>;
  extractedLoc: number;
  confidenceScore: number;
  dilationCount: number;
  dependencyChecksum: string;
  unsupportedReason?: string | null;
}

export interface InvariantSpec {
  jobId: string;
  vulnType: string;
  targetFile: string;
  generatedTests: Array<{
    path: string;
    content: string;
    kind: "invariant" | "fuzz" | "regression";
  }>;
  baselineContracts: Array<{
    name: string;
    description: string;
    expectedShape: Record<string, unknown>;
  }>;
  mutationBoundaries: {
    allowedFiles: string[];
    forbiddenGlobs: string[];
    maxFilesTouched: number;
  };
}

export type ContenderID = "APEX-GPT-O1" | "APEX-CLAUDE-3.5" | "APEX-GROK-4.2";

export interface ContenderPatch {
  contenderId: ContenderID;
  provider: "openai" | "anthropic" | "xai";
  model: string;
  latencyMs: number;
  tokenInput: number;
  tokenOutput: number;
  unifiedDiff: string;
  filesTouched: string[];
  compilePrecheckPassed: boolean;
  boundaryViolation: boolean;
  rawArtifactUri: string;
}

export interface TriageArtifact {
  compileDelta: "PASSED" | "FAILED";
  fuzzScore: number;
  invariantScore: number;
  boundaryPurity: number;
  regressionCount: number;
  latencyVarianceMs: number;
  unifiedDiffLength: number;
  isFatality: boolean;
  fatalityReason?: string | null;
}

export interface WendigoReport {
  jobId: string;
  repo: string;
  vulnId: string;
  cve: string | null;
  severity: string;
  targetFile: string;
  executionSummary: {
    extractedLoc: number;
    confidenceScore: number;
    dilationCount: number;
    modelsDispatched: number;
    apexContender: ContenderID | null;
  };
  contenders: Array<{
    contenderId: ContenderID;
    status: "SURVIVED" | "PURGED";
    reason: string;
    metrics?: Partial<TriageArtifact>;
  }>;
  receipts: {
    testsAppended: string[];
    throughputImpactMs: number;
    rollbackConfidence: "LOW" | "MEDIUM" | "HIGH";
  };
  finalState: "PR_OPENED" | "NO_SAFE_PATCH" | "HUMAN_REVIEW_REQUIRED";
}
