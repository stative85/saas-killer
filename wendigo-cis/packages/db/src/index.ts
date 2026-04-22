import { Pool } from "pg";
import { config } from "@wendigo/config";
import { JobState } from "@wendigo/contracts";

export class Database {
  private pool: Pool;

  constructor() {
    this.pool = new Pool({
      connectionString: config.DATABASE_URL,
    });
  }

  async createJob(...args: any[]): Promise<void> {
    if (!config.DATABASE_URL.includes("localhost")) {
       // Real DB logic...
    }
    console.log(`[DB-MOCK] Job Created: ${args[0]}`);
  }

  async updateJobState(jobId: string, state: JobState): Promise<void> {
    console.log(`[DB-MOCK] Job ${jobId} State -> ${state}`);
  }

  async recordArtifact(jobId: string, stage: string, type: string, uri: string, checksum: string, contentType: string): Promise<void> {
    const query = `
      INSERT INTO job_artifacts (
        id, job_id, stage, artifact_type, storage_uri, checksum, content_type
      ) VALUES (
        gen_random_uuid(), $1, $2, $3, $4, $5, $6
      )
    `;
    await this.pool.query(query, [jobId, stage, type, uri, checksum, contentType]);
  }

  async recordPullRequest(jobId: string, prNumber: number, prUrl: string, branchName: string, commitSha: string, reportUri: string): Promise<void> {
    const query = `
      INSERT INTO pull_requests (
        id, job_id, github_pr_number, github_pr_url, branch_name, commit_sha, report_artifact_uri
      ) VALUES (
        gen_random_uuid(), $1, $2, $3, $4, $5, $6
      )
    `;
    await this.pool.query(query, [jobId, prNumber, prUrl, branchName, commitSha, reportUri]);
  }
}
