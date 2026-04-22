import { execa } from "execa";
import fs from "fs-extra";
import path from "node:path";
import os from "node:os";

export class RepoRuntime {
  private workDir: string;

  constructor(private jobId: string) {
    this.workDir = path.join(os.tmpdir(), "wendigo", jobId);
  }

  async setup(cloneUrl: string, sha: string): Promise<void> {
    await fs.ensureDir(this.workDir);
    await execa("git", ["clone", cloneUrl, "."], { cwd: this.workDir });
    await execa("git", ["checkout", sha], { cwd: this.workDir });
  }

  async applyPatch(patch: string): Promise<void> {
    const patchPath = path.join(this.workDir, "contender.patch");
    await fs.writeFile(patchPath, patch);
    await execa("git", ["apply", "contender.patch"], { cwd: this.workDir });
  }

  async runCommand(cmd: string, args: string[]): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    const result = await execa(cmd, args, { cwd: this.workDir, reject: false });
    return {
      stdout: result.stdout,
      stderr: result.stderr,
      exitCode: result.exitCode ?? 0
    };
  }

  async cleanup(): Promise<void> {
    await fs.remove(this.workDir);
  }
}
