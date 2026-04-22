-- 001_initial_schema.sql

CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  dedupe_key TEXT NOT NULL UNIQUE,
  state TEXT NOT NULL,
  source TEXT NOT NULL,
  repo_owner TEXT NOT NULL,
  repo_name TEXT NOT NULL,
  repo_default_branch TEXT NOT NULL,
  installation_id BIGINT NOT NULL,
  vuln_id TEXT NOT NULL,
  cve TEXT NULL,
  severity TEXT NOT NULL,
  vuln_type TEXT NOT NULL,
  target_file TEXT NOT NULL,
  failing_condition TEXT NOT NULL,
  advisory_url TEXT NULL,
  package_name TEXT NULL,
  package_version TEXT NULL,
  fixed_version TEXT NULL,
  base_sha TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL,
  failure_reason TEXT NULL
);

CREATE TABLE job_stage_runs (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  attempt INT NOT NULL DEFAULT 1,
  worker_id TEXT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at TIMESTAMPTZ NULL,
  error_message TEXT NULL
);

CREATE TABLE job_artifacts (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  stage TEXT NOT NULL,
  artifact_type TEXT NOT NULL,
  storage_uri TEXT NOT NULL,
  checksum TEXT NOT NULL,
  content_type TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE contenders (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  contender_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  latency_ms INT NOT NULL,
  token_input INT NOT NULL,
  token_output INT NOT NULL,
  compile_precheck_passed BOOLEAN NOT NULL,
  boundary_violation BOOLEAN NOT NULL,
  unified_diff_length INT NOT NULL,
  raw_artifact_uri TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE validation_results (
  id UUID PRIMARY KEY,
  contender_row_id UUID NOT NULL REFERENCES contenders(id) ON DELETE CASCADE,
  compile_delta TEXT NOT NULL,
  fuzz_score INT NOT NULL,
  invariant_score DOUBLE PRECISION NOT NULL,
  boundary_purity DOUBLE PRECISION NOT NULL,
  regression_count INT NOT NULL,
  latency_variance_ms DOUBLE PRECISION NOT NULL,
  unified_diff_length INT NOT NULL,
  is_fatality BOOLEAN NOT NULL,
  fatality_reason TEXT NULL,
  apex_score DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE pull_requests (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  github_pr_number INT NOT NULL,
  github_pr_url TEXT NOT NULL,
  branch_name TEXT NOT NULL,
  commit_sha TEXT NOT NULL,
  report_artifact_uri TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE job_locks (
  dedupe_key TEXT PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_jobs_state ON jobs(state);
CREATE INDEX idx_jobs_repo ON jobs(repo_owner, repo_name);
CREATE INDEX idx_jobs_vuln ON jobs(vuln_id);
CREATE INDEX idx_stage_runs_job_stage ON job_stage_runs(job_id, stage);
CREATE INDEX idx_artifacts_job_stage ON job_artifacts(job_id, stage);
CREATE INDEX idx_contenders_job ON contenders(job_id);
