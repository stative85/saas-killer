# deploy_batch.py
import subprocess
import time
from pathlib import Path

# --- CONFIGURATION ---
RUN_IDS = [
    "sprint_run_001",
    "sprint_run_002",
    "sprint_run_003",
    "sprint_run_004",
    "sprint_run_005",
]

# Absolute Path Lockdown
ROOT_DIR = Path(__file__).parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
SECRETS = FORGE_DIR / "configs" / "client_secrets.json"
PYTHON = ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe"
DEPLOY_SCRIPT = FORGE_DIR / "deploy_youtube.py"
LOG_PATH = FORGE_DIR / "outputs" / "deploy_batch_log.txt"

def run_upload(run_id: str):
    print(f"[*] Engrossing Upload for: {run_id}")
    cmd = [
        str(PYTHON),
        str(DEPLOY_SCRIPT),
        "--run-id", run_id,
        "--secrets", str(SECRETS)
    ]

    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(f"\n=== START {run_id} ===\n")
        # We allow stdout/stderr to pass through to console for OAuth visibility
        result = subprocess.run(cmd, capture_output=False)
        log.write(f"EXIT_CODE: {result.returncode}\n")
        log.write(f"=== END {run_id} ===\n")

    return result.returncode

def main():
    if not SECRETS.exists():
        print(f"[!] CRITICAL: Missing secrets at {SECRETS}")
        print("[!] Download client_secrets.json from Google Cloud Console first.")
        return

    print(f"\n🐺 WENDIGO BATCH DEPLOYER - Sequential Staging")
    print("-" * 50)

    for i, run_id in enumerate(RUN_IDS):
        print(f"[{i+1}/{len(RUN_IDS)}] Processing {run_id}...")
        
        code = run_upload(run_id)

        if code != 0:
            print(f"[🛑] FAILURE: {run_id} — stopping batch. Check logs at {LOG_PATH}")
            break

        if i < len(RUN_IDS) - 1:
            print("[*] Cooling down 20s for API stability...")
            time.sleep(20)

    print("-" * 50)
    print("BATCH COMPLETE. All assets staged for review.")

if __name__ == "__main__":
    main()
