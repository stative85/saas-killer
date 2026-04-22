import { SliceArtifact, InvariantSpec, ContenderPatch, ContenderID } from "@wendigo/contracts";
import { ModelGateway, ModelRequest } from "@wendigo/model-gateway";

export class Arena {
  private gateway = new ModelGateway();

  async conduct(jobId: string, slice: SliceArtifact, invariants: InvariantSpec): Promise<ContenderPatch[]> {
    const systemPrompt = `
You are WENDIGO-CIS, a security remediation engine. 
Your task is to fix a security vulnerability in the provided TypeScript code.
Vulnerability Type: ${invariants.vulnType}
Target File: ${invariants.targetFile}

RULES:
1. Output ONLY a unified diff.
2. Do not explain anything.
3. Preserve the existing API and types.
4. Do not add new dependencies.
5. Touch only the following allowed files: ${invariants.mutationBoundaries.allowedFiles.join(", ")}
    `;

    const userPrompt = `
CONTEXT SLICE:
${JSON.stringify(slice.selectedFiles, null, 2)}

Fix the vulnerability while ensuring that the provided logic remains functional.
    `;

    const contenders: ContenderID[] = ["APEX-GPT-O1"]; // v0: Start with one

    const results = await Promise.all(contenders.map(cid => 
      this.gateway.call("mock", {
        jobId,
        contenderId: cid,
        systemPrompt,
        userPrompt
      })
    ));

    return results;
  }
}
