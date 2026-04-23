# deploy_youtube.py
import argparse
import subprocess
import json
import os
from pathlib import Path

# --- PATHS ---
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUTS_DIR = BASE_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"

def get_latest_run():
    runs = sorted(RUNS_DIR.glob("*"), key=os.path.getmtime, reverse=True)
    return runs[0] if runs else None

def main():
    parser = argparse.ArgumentParser(description="WENDIGO YOUTUBE DEPLOYER")
    parser.add_argument("--run-id", default="latest", help="Specific Run ID to deploy")
    parser.add_argument("--secrets", default="configs/client_secrets.json")
    args = parser.parse_args()

    # 1. Target Selection
    run_path = RUNS_DIR / args.run_id if args.run_id != "latest" else get_latest_run()
    if not run_path or not run_path.exists():
        print(f"[!] Target run not found: {run_path}")
        return

    print(f"\n🐺 WENDIGO DEPLOYER ENGAGED - Target: {run_path.name}")
    print("-" * 50)

    # 2. Metadata Generation
    script_file = run_path / "best_narrative.txt"
    meta_file = run_path / "youtube_metadata.json"
    subprocess.run(["python", str(SCRIPTS_DIR / "metadata_builder.py"), "--script", str(script_file), "--out", str(meta_file)], check=True)
    
    with open(meta_file, "r") as f:
        meta = json.load(f)

    # SAFETY GATE: No accidental public blasts
    assert meta["privacyStatus"] == "private", "CRITICAL ERROR: privacyStatus must be 'private' for staging!"

    # 3. Asset Verification
    video_file = BASE_DIR / "outputs/render/final_video.mp4" # v1: check common render folder
    if not video_file.exists():
        print(f"[!] Asset missing: {video_file}")
        return

    # 4. Upload (Private Staging)
    print("[*] Launching Uploader...")
    upload_cmd = [
        "python", str(SCRIPTS_DIR / "youtube_uploader.py"),
        "--video", str(video_file),
        "--title", meta["title"],
        "--description", meta["description"],
        "--tags", ",".join(meta["tags"]),
        "--run-id", run_path.name,
        "--secrets", args.secrets
    ]
    subprocess.run(upload_cmd, check=True)

    # 5. Status Polling
    manifest_file = OUTPUTS_DIR / "publish" / f"{run_path.name}_manifest.json"
    if manifest_file.exists():
        with open(manifest_file, "r") as f:
            manifest = json.load(f)
        
        video_id = manifest["video_id"]
        print(f"[*] Starting Status Radar for ID: {video_id}")
        subprocess.run(["python", str(SCRIPTS_DIR / "youtube_status.py"), "--id", video_id], check=True)
        
        # 6. Final Manifest (Corpse Trail)
        manifest["upload_status"] = "processed"
        manifest["asset_path"] = str(video_file)
        with open(run_path / "publish_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        print("-" * 50)
        print(f"[✅] DEPLOYMENT STAGED: {run_path / 'publish_manifest.json'}")
        print(f"[✅] MANUALLY VERIFY HERE: https://studio.youtube.com/video/{video_id}/edit")

if __name__ == "__main__":
    main()
