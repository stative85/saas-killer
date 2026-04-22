import { ContenderPatch, ContenderID } from "@wendigo/contracts";

export interface ModelRequest {
  jobId: string;
  contenderId: ContenderID;
  systemPrompt: string;
  userPrompt: string;
  temperature?: number;
}

export interface ModelProvider {
  dispatch(request: ModelRequest): Promise<ContenderPatch>;
}

/**
 * MockProvider for v0 local testing
 */
export class MockProvider implements ModelProvider {
  async dispatch(request: ModelRequest): Promise<ContenderPatch> {
    return {
      contenderId: request.contenderId,
      provider: "openai",
      model: "gpt-mock",
      latencyMs: 1500,
      tokenInput: 500,
      tokenOutput: 100,
      unifiedDiff: "--- target.ts\n+++ target.ts\n@@ -1,1 +1,2 @@\n-function merge(a, b) { return Object.assign(a, b); }\n+function merge(a, b) { if (b.__proto__) return a; return Object.assign(a, b); }",
      filesTouched: ["target.ts"],
      compilePrecheckPassed: true,
      boundaryViolation: false,
      rawArtifactUri: "mock://raw"
    };
  }
}

export class ModelGateway {
  private providers: Record<string, ModelProvider> = {
    "mock": new MockProvider(),
    // "openai": new OpenAIProvider(),
    // "anthropic": new AnthropicProvider(),
  };

  async call(provider: string, request: ModelRequest): Promise<ContenderPatch> {
    const p = this.providers[provider] || this.providers["mock"];
    return p.dispatch(request);
  }
}
