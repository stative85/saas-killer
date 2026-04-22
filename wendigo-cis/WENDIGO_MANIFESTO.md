# 🐺 WENDIGO C.I.S. (Continuous Infiltration & Synthesis)

## THE SAAS KILLER

The automated security remediation market is currently defined by **Theater**. 
Incumbent platforms generate probabilistic patches, assume correctness based on static analysis, and push PRs that break build pipelines or introduce subtle regressions.

**WENDIGO C.I.S. operates on a different physics.**

It does not guess. It does not hope. It measures, attacks, and enforces.

---

### 🏛️ THE ARCHITECTURE OF TRUTH

WENDIGO is built on a linear, deterministic spine. It separates *Generation* (probabilistic) from *Validation* (absolute truth).

#### 1. INGRESS (The Trapdoor)
*   Accepts normalized payloads from Snyk, Dependabot, or internal scanners.
*   Functions purely as a state initiator. No logic leakage.

#### 2. VORTEX SLICER (Centripetal Context)
*   Powered by ODIN Implosion Logic.
*   Does not just slice files; it maps the **Resonance** of the repository.
*   Identifies the "Anomaly Point" (the highest density of exports/imports) to ensure context includes the true biological heart of the application.

#### 3. ARENA (Generation)
*   Dispatches the contextual slice to multiple LLM contenders concurrently.
*   Enforces a strict, no-prose, unified-diff-only output contract.

#### 4. THE CRUCIBLE (Hostile Validation)
*   **This is the Moat.**
*   WENDIGO compiles a hostile invariant specifically designed to exploit the reported vulnerability (e.g., a payload attempting to pollute `Object.prototype`).
*   It applies the contender's patch in an ephemeral, isolated git workspace.
*   It executes the hostile invariant *against the patched code*.
*   **The Rule of Life and Death:** If the patch fails to stop the exploit, or if it breaks existing regressions, it suffers a **💀 CRUCIBLE FATALITY**.
*   Only patches that survive live, hostile execution attain **✅ TRUTH**.

#### 5. EGRESS (Conditioned PR)
*   WENDIGO never opens a PR based on a guess.
*   It mints a short-lived GitHub App token, applies the surviving patch, commits the hostile invariant test to the repo as a permanent regression check, and opens the PR.
*   If no contender survives, the system fails loudly, explicitly marking the job as `HUMAN_REVIEW_REQUIRED`.

---

### 🩸 WHY IT KILLS INCUMBENTS

1.  **Trust Through Violence:** WENDIGO proves a patch works by trying to break it. You don't review the code; you review the forensic survival report.
2.  **Model Agnostic:** Because the Validator (The Crucible) is the source of truth, the Arena can hot-swap GPT-4o, Claude 3.5, or Grok without degrading the system's integrity. 
3.  **Audit Custody:** Every stage transition, artifact, and fatality is recorded in a rigid PostgreSQL schema. The memory of the system is absolute.

---

### 🚀 DEPLOYMENT

WENDIGO is designed for maximum RPM with minimal infrastructure bloat.

1.  **Backing Services:** PostgreSQL (State), Redis (BullMQ queues).
2.  **Worker Nodes:** Stateless execution engines that can scale horizontally.
3.  **Storage:** S3-compatible artifact store for forensic retention.

**WENDIGO IS ONLINE. GRINDER HAS TEETH.**
