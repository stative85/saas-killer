# run_full.py
import argparse
import subprocess
import os
import json
import re
from pathlib import Path
from datetime import datetime

# --- CONFIG ---
MIN_TOTAL_SCORE = 0.50
SIMILARITY_THRESHOLD = 0.80

# --- PATHS ---
ROOT_DIR = Path(__file__).parent.parent.absolute()
FORGE_DIR = ROOT_DIR / "narrative-forge"
SCRIPTS_DIR = FORGE_DIR / "scripts"
OUTPUTS_DIR = FORGE_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
LEDGER_FILE = OUTPUTS_DIR / "master_ledger.json"

def get_python_exe():
    local_venv = FORGE_DIR.parent / "harvester_venv" / "Scripts" / "python.exe"
    if local_venv.exists(): return str(local_venv)
    original_venv = Path(r"C:\Users\cleve\Downloads\CLI\facebook_reel_harvester\harvester_venv\Scripts\python.exe")
    if original_venv.exists(): return str(original_venv)
    return "python"

PYTHON_EXE = get_python_exe()

def run_step(name, cmd, manifest_stages):
    print(f"[*] Executing {name}...")
    full_cmd = [str(PYTHON_EXE)] + [str(c) for c in cmd]
    
    start_time = datetime.now().isoformat()
    result = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    end_time = datetime.now().isoformat()
    
    ok = result.returncode == 0
    manifest_stages.append({
        "name": name,
        "ok": ok,
        "exit_code": result.returncode,
        "start": start_time,
        "end": end_time,
        "stderr_tail": result.stderr[-500:] if result.stderr else ""
    })
    
    if not ok:
        print(f"[!] Error in {name}: {result.stderr}")
        return False, result.stdout
    return True, result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlist", help="YouTube Playlist URL")
    parser.add_argument("--mode", default="fracture_aggressive", choices=["fracture_aggressive", "retention_aggressive"])
    parser.add_argument("--run-id", default="auto")
    parser.add_argument("--hook-text", help="Manual hook override")
    parser.add_argument("--hook-type", default="declarative")
    args = parser.parse_args()

    run_id = args.run_id if args.run_id != "auto" else datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_path = RUNS_DIR / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "run_id": run_id,
        "engine": PYTHON_EXE,
        "mode": args.mode,
        "hook_type": args.hook_type,
        "stages": [],
        "final_ok": False
    }

    print(f"\n🐺 WENDIGO FORGE v1.2 - SPRINT RUN: {run_id}")

    # 1. EVOLVE
    mode_name, style_name = args.mode.split('_')
    chunks_path = Path(r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks_with_arcs.jsonl")
    if not chunks_path.exists():
        chunks_path = FORGE_DIR / "outputs" / "infowars_corpus_modern_hardened" / "index" / "chunks_with_arcs.jsonl"

    ok, _ = run_step("EVOLVE", [
        SCRIPTS_DIR / "ab_harness.py", "--n", "5", "--mode", mode_name, "--style", style_name, "--chunks", str(chunks_path)
    ], manifest["stages"])

    # 2. FIND ASSETS
    best_scripts = sorted((OUTPUTS_DIR / "scripts" / "best").glob("*.txt"), key=os.path.getmtime)
    latest_best = best_scripts[-1] if best_scripts else None
    
    if ok and latest_best:
        # 3. PREFLIGHT
        preflight_json = run_path / "preflight.json"
        run_step("PREFLIGHT", [SCRIPTS_DIR / "local_critic.py", "--script", str(latest_best), "--out", str(preflight_json)], manifest["stages"])

        # 4. DEPLOY PACK (Metadata + Hooks)
        meta_json = run_path / "metadata.json"
        run_step("METADATA", [
            SCRIPTS_DIR / "metadata_builder.py", "--script", str(latest_best), "--obsessions", r"C:\Users\cleve\OneDrive\Pictures\corpus_run\exports\obsession_terms.txt", "--hooks", "none", "--out", str(meta_json)
        ], manifest["stages"])

        # 5. SEAL PACK
        if meta_json.exists():
            meta = json.loads(meta_json.read_text())
            deploy_pack = {
                "run_id": run_id,
                "title": meta.get("title_variants", ["WENDIGO"])[0],
                "description": meta.get("description", ""),
                "tags": meta.get("tags", []),
                "pinned_comment": meta.get("pinned_comment", ""),
                "primary_hook": meta.get("primary_hook", ""),
                "thumbnail_text": meta.get("thumbnail_text_variants", ["THE TRUTH"])[0]
            }
            (run_path / "deploy_pack.json").write_text(json.dumps(deploy_pack, indent=2))
            print(f"[✅] Deploy Pack Sealed.")

    manifest["final_ok"] = all(s["ok"] for s in manifest["stages"])
    (run_path / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[✅] Run Manifest Written: {run_id}")

if __name__ == "__main__":
    main()
