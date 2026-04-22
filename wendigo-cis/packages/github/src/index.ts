import { Octokit } from "@octokit/rest";
import { createAppAuth } from "@octokit/auth-app";
import { config } from "@wendigo/config";
import { WendigoReport } from "@wendigo/contracts";
import { applyPatch } from "diff";
import crypto from "node:crypto";

export class GithubClient {
  private getOctokit(installationId: number): Octokit {
    if (!config.GITHUB_APP_ID || !config.GITHUB_APP_PRIVATE_KEY) {
      throw new Error("GitHub App credentials missing from config");
    }
    return new Octokit({
      authStrategy: createAppAuth,
      auth: {
        appId: config.GITHUB_APP_ID,
        privateKey: config.GITHUB_APP_PRIVATE_KEY,
        installationId: installationId,
      },
    });
  }

  private generateBranchName(jobId: string, baseSha: string): string {
    const hash = crypto.createHash("sha256")
      .update(`${jobId}:${baseSha}`)
      .digest("hex")
      .substring(0, 8);
    return `wendigo/sec-${hash}`;
  }

  async createRemediationPr(
    installationId: number,
    owner: string,
    repo: string,
    baseBranch: string,
    report: WendigoReport,
    patch: string,
    testContent: string,
    testPath: string,
    prTitle: string,
    prBody: string
  ): Promise<{ prNumber: number; prUrl: string; branchName: string; commitSha: string }> {
    const octokit = this.getOctokit(installationId);
    
    // 1. Get base branch SHA
    const { data: refData } = await octokit.git.getRef({ owner, repo, ref: `heads/${baseBranch}` });
    const baseSha = refData.object.sha;
    const branchName = this.generateBranchName(report.jobId, baseSha);

    // 2. Fetch original target file content
    const { data: fileData } = await octokit.repos.getContent({
      owner, repo, path: report.targetFile, ref: baseSha
    }) as any;
    const originalContent = Buffer.from(fileData.content, 'base64').toString('utf-8');

    // 3. Apply Patch
    const patchedContent = applyPatch(originalContent, patch);
    if (patchedContent === false) {
      throw new Error(`[GITHUB] Failed to apply patch to ${report.targetFile}`);
    }

    // 4. Create Branch
    await octokit.git.createRef({ owner, repo, ref: `refs/heads/${branchName}`, sha: baseSha });

    // 5. Create Blobs
    const { data: patchedBlob } = await octokit.git.createBlob({ owner, repo, content: patchedContent, encoding: "utf-8" });
    const { data: testBlob } = await octokit.git.createBlob({ owner, repo, content: testContent, encoding: "utf-8" });

    // 6. Create Tree & Commit
    const { data: commitData } = await octokit.git.getCommit({ owner, repo, commit_sha: baseSha });
    const { data: newTree } = await octokit.git.createTree({
      owner, repo, base_tree: commitData.tree.sha,
      tree: [
        { path: report.targetFile, mode: "100644", type: "blob", sha: patchedBlob.sha },
        { path: testPath, mode: "100644", type: "blob", sha: testBlob.sha },
      ],
    });

    const { data: newCommit } = await octokit.git.createCommit({
      owner, repo, message: `[WENDIGO] Apply security patch for ${report.vulnId}`,
      tree: newTree.sha, parents: [baseSha],
    });

    await octokit.git.updateRef({ owner, repo, ref: `heads/${branchName}`, sha: newCommit.sha });

    // 7. Create PR
    const { data: pr } = await octokit.pulls.create({
      owner, repo, title: prTitle, body: prBody, head: branchName, base: baseBranch,
    });

    await octokit.issues.addLabels({ owner, repo, issue_number: pr.number, labels: ["wendigo-cis", "security"] });

    return { prNumber: pr.number, prUrl: pr.html_url, branchName, commitSha: newCommit.sha };
  }
}
