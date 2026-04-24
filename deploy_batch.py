# deploy_batch.py
import subprocess
import time
import json
from pathlib import Path

# --- CONFIGURATION ---
RUN_IDS = [
    "sprint_run_001", "sprint_run_002", "sprint_run_003", 
    "sprint_run_004", "sprint_run_005"
]

ROOT_DIR = Path(__file__).parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
SECRETS = FORGE_DIR / "configs" / "client_secrets.json"
PYTHON = ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe"
DEPLOY_SCRIPT = FORGE_DIR / "scripts" / "youtube_uploader.py"
LOG_PATH = FORGE_DIR / "outputs" / "deploy_batch_log.txt"

def run_upload(run_id: str):
    run_dir = FORGE_DIR / "outputs" / "runs" / run_id
    pack_path = run_dir / "deploy_pack.json"
    video_path = run_dir / "video.mp4"
    
    if not pack_path.exists():
        print(f"[!] Error: Deploy Pack missing for {run_id}. Skipping.")
        return 1

    with open(pack_path, "r") as f:
        pack = json.load(f)

    print(f"[*] Uploading: {pack['title']} (Run: {run_id})")
    
    cmd = [
        str(PYTHON), str(DEPLOY_SCRIPT),
        "--video", str(video_path),
        "--title", pack["title"],
        "--description", pack["description"],
        "--tags", ",".join(pack["tags"]),
        "--run-id", run_id,
        "--secrets", str(SECRETS)
    ]

    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(f"\n=== START {run_id} ===\n")
        # Run and capture for log, but keep stdout for OAuth
        result = subprocess.run(cmd)
        log.write(f"EXIT_CODE: {result.returncode}\n")
        log.write(f"=== END {run_id} ===\n")

    return result.returncode

def main():
    if not SECRETS.exists():
        print(f"[!] ERROR: Missing {SECRETS}. Upload plane locked.")
        return

    print(f"\n[WENDIGO] Sequential Egress Protocol - v1.2 Standard")
    print("-" * 50)

    for i, run_id in enumerate(RUN_IDS):
        print(f"[{i+1}/{len(RUN_IDS)}] Processing {run_id}...")
        code = run_upload(run_id)
        if code != 0:
            print(f"[🛑] BATCH HALTED at {run_id}. Check {LOG_PATH}")
            break
        if i < len(RUN_IDS) - 1:
            print("[*] API Cooldown (20s)...")
            time.sleep(20)

    print("-" * 50)
    print("BATCH COMPLETE.")

if __name__ == "__main__":
    main()
