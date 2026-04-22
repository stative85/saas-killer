import { InvariantSpec, TrapdoorEvent, SliceArtifact } from "@wendigo/contracts";

export interface InvariantGenerator {
  generate(jobId: string, event: TrapdoorEvent, slice: SliceArtifact): InvariantSpec;
}

/**
 * PrototypePollutionGenerator
 * 
 * Generates hostile tests for prototype pollution.
 * It injects a payload that attempts to modify Object.prototype.
 */
export class PrototypePollutionGenerator implements InvariantGenerator {
  generate(jobId: string, event: TrapdoorEvent, slice: SliceArtifact): InvariantSpec {
    const targetFile = event.alert.targetFile;
    
    const hostileFuzzTest = `
import { expect } from 'chai';
// Note: In reality, we'd resolve the actual export name from the AST in slicer
import { merge } from './${targetFile.replace('.ts', '')}';

describe('WENDIGO - Prototype Pollution Invariant', () => {
  it('should not allow modification of Object.prototype', () => {
    const payload = JSON.parse('{"__proto__": {"polluted": "yes"}}');
    const target = {};
    
    // Attempt the operation
    try {
      merge(target, payload);
    } catch (e) {
      // Errors are acceptable as long as the prototype isn't touched
    }
    
    expect(({} as any).polluted).to.be.undefined;
  });

  it('should still perform original merge function correctly (Regression)', () => {
    const a = { x: 1 };
    const b = { y: 2 };
    const result = merge(a, b);
    expect(result.x).to.equal(1);
    expect(result.y).to.equal(2);
  });
});
    `;

    return {
      jobId,
      vulnType: "prototype-pollution",
      targetFile,
      generatedTests: [
        {
          path: `wendigo_tests/prototype_pollution.spec.ts`,
          content: hostileFuzzTest,
          kind: "invariant"
        }
      ],
      baselineContracts: [],
      mutationBoundaries: {
        allowedFiles: [targetFile],
        forbiddenGlobs: ["**/node_modules/**", "**/tests/**"],
        maxFilesTouched: 1
      }
    };
  }
}

export class InvariantCompiler {
  private generators: Record<string, InvariantGenerator> = {
    "prototype-pollution": new PrototypePollutionGenerator(),
    // Future plugins: "ssrf", "path-traversal", etc.
  };

  compile(jobId: string, event: TrapdoorEvent, slice: SliceArtifact): InvariantSpec {
    const generator = this.generators[event.alert.vulnType] || this.generators["prototype-pollution"];
    return generator.generate(jobId, event, slice);
  }
}
