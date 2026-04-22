import { Project, SourceFile } from "ts-morph";
import { SliceArtifact } from "@wendigo/contracts";

export class Slicer {
  private project: Project;

  constructor(tsconfigPath?: string) {
    this.project = new Project({
      tsConfigFilePath: tsconfigPath,
      skipAddingFilesFromTsConfig: true,
    });
  }

  async slice(jobId: string, rootDir: string, targetPath: string): Promise<SliceArtifact> {
    const absolutePath = `${rootDir}/${targetPath}`;
    const sourceFile = this.project.addSourceFileAtPath(absolutePath);
    
    const selectedFiles: SliceArtifact['selectedFiles'] = [
      {
        path: targetPath,
        content: sourceFile.getFullText(),
        role: "target"
      }
    ];

    // v0: Extract immediate imports and types
    // This is the "neighborhood" extraction logic
    const importDeclarations = sourceFile.getImportDeclarations();
    for (const imp of importDeclarations) {
      const moduleSpecifier = imp.getModuleSpecifierValue();
      if (moduleSpecifier.startsWith(".")) {
        // It's a local dependency - we should ideally dilate here
        // For v0, we just note it or add it if it's small
      }
    }

    return {
      jobId,
      targetFile: targetPath,
      selectedFiles,
      extractedLoc: sourceFile.getEndLineNumber(),
      confidenceScore: 0.9, // Initial heuristic
      dilationCount: 0,
      dependencyChecksum: "v0-stub-checksum"
    };
  }
}
