# ⚖️ WENDIGO FORENSIC ARTIFACT STANDARD (v1)

Every run must emit a `forensic_bundle.json` with the following sacred fields. No exceptions.

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | string | Unique identifier (YYYY-MM-DD_HHMMSS) |
| `timestamp` | string | ISO-8601 creation time |
| `mode` | string | fracture_aggressive, retention_aggressive, etc. |
| `hook_type` | string | declarative, confrontational, question, etc. |
| `script_path` | string | Relative path to the winning script |
| `render_path` | string | Relative path to the rendered asset (MP4) |
| `critic_model` | string | The specific LLM used for synthetic preflight |
| `predicted_watch_ratio` | float | 0.0 - 1.0 (Synthetic prediction) |
| `slop_detected` | boolean | True if AI-slop threshold was breached |
| `critical_flaw` | string | The primary reason for potential failure |
| `winning_line` | string | The highest-resonance line in the script |
| `deployment_status` | string | staged, uploaded, failed, none |
| `feedback_status` | string | pending, ingested, none |

## 🏛️ Storage Protocol
1. **Per-Run Bundle:** Stored in `outputs/runs/{run_id}/forensic_bundle.json`.
2. **Master Ledger:** `outputs/master_ledger.json` is a derived index containing all bundles.
3. **Immutability:** Once a run is marked 'VALIDATED', its bundle must not be modified except for `feedback_status`.
