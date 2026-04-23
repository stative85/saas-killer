# run_full.py
import argparse
import subprocess
import os
import json
import csv
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
REGISTRY_FILE = OUTPUTS_DIR / "runs_registry.csv"
FEEDBACK_DIR = OUTPUTS_DIR / "feedback"
PYTHON_EXE = str(ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe")

def run_step(name, cmd, cwd=None):
    print(f"[*] Executing {name}...")
    full_cmd = [PYTHON_EXE] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    if result.returncode != 0:
        print(f"[!] Error in {name}: {result.stderr}")
        return False, result.stdout
    return True, result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlist", help="YouTube Playlist URL")
    parser.add_argument("--mode", default="fracture_aggressive", choices=["fracture_aggressive", "retention_aggressive"])
    parser.add_argument("--run-id", default="auto")
    parser.add_argument("--hook-override", action="store_true", help="Force top 1 hook from ranker")
    parser.add_argument("--hook-text", help="Manually provided hook string")
    parser.add_argument("--hook-type", default="declarative", help="Category: declarative, confrontational, question")
    parser.add_argument("--yolo", action="store_true", help="Bypass all gates and auto-render")
    args = parser.parse_args()

    if args.yolo:
        print("\n[!!!] YOLO MODE ACTIVATED: ALL GATES OPEN. MAX AGGRESSION. [!!!]")
        global MIN_TOTAL_SCORE, SIMILARITY_THRESHOLD
        MIN_TOTAL_SCORE = 0.0
        SIMILARITY_THRESHOLD = 1.0

    run_id = args.run_id if args.run_id != "auto" else datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_path = RUNS_DIR / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🐺 NARRATIVE FORGE SPRINT - RUN: {run_id} | MODE: {args.mode}")
    print("-" * 50)

    # 1. EVOLVE (A/B Harness)
    mode_name, style_name = args.mode.split('_')
    run_step("EVOLVE", [
        str(SCRIPTS_DIR / "ab_harness.py"), 
        "--n", "5", 
        "--mode", mode_name, 
        "--style", style_name
    ], cwd=FORGE_DIR)

    # 2. RANK HOOKS
    latest_best_dir = FORGE_DIR / "outputs" / "scripts" / "best"
    best_files = sorted(latest_best_dir.glob("*.txt"), key=os.path.getmtime)
    if not best_files:
        print("[!] No best scripts found to rank hooks from.")
        return
    latest_best = best_files[-1]
    
    hooks_json = run_path / "hooks.json"
    run_step("RANK_HOOKS", [
        str(SCRIPTS_DIR / "hook_ranker.py"), 
        "--script", str(latest_best),
        "--quotes", r"C:\Users\cleve\OneDrive\Pictures\corpus_run\exports\top_quotes.txt",
        "--chunks", r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks_with_arcs.jsonl",
        "--out", str(hooks_json)
    ], cwd=FORGE_DIR)

    # 3. HOOK OVERRIDE
    applied_hook = ""
    if args.hook_text:
        print(f"[*] Applying Manual Hook Override: {args.hook_text}")
        script_text = latest_best.read_text(encoding="utf-8")
        # Ensure we replace ONLY the hook phase
        new_script = re.sub(r"\[HOOK\].*\nArcs:.*\n> .*\n", f"[HOOK]\nArcs: Manual_Divergence\n> {args.hook_text}\n", script_text)
        latest_best.write_text(new_script, encoding="utf-8")
        applied_hook = args.hook_text
    elif args.hook_override:
        print("[*] Applying Ranker Hook Override...")
        with open(hooks_json, "r") as f:
            hooks = json.load(f)
        top_hook = hooks[0]['text']
        script_text = latest_best.read_text(encoding="utf-8")
        new_script = re.sub(r"\[HOOK\].*\nArcs:.*\n> .*\n", f"[HOOK]\nArcs: Hybrid_Override\n> {top_hook}\n", script_text)
        latest_best.write_text(new_script, encoding="utf-8")
        applied_hook = top_hook
        print(f"  [+] Overrode hook with: {top_hook[:50]}...")

    # 4. BUILD METADATA
    meta_json = run_path / "metadata.json"
    run_step("BUILD_METADATA", [
        str(SCRIPTS_DIR / "metadata_builder.py"),
        "--script", str(latest_best),
        "--obsessions", r"C:\Users\cleve\OneDrive\Pictures\corpus_run\exports\obsession_terms.txt",
        "--hooks", str(hooks_json),
        "--out", str(meta_json)
    ], cwd=FORGE_DIR)

    # 5. GENERATE FEEDBACK TEMPLATE
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    with open(meta_json, "r") as f:
        meta = json.load(f)
        
    feedback = {
        "run_id": run_id,
        "mode": args.mode,
        "hook_type": args.hook_type,
        "title": meta["title_variants"][0],
        "hook_used": applied_hook if applied_hook else meta["primary_hook"],
        "views": 0,
        "avg_watch_ratio": 0.0,
        "likes": 0,
        "script_path": str(latest_best)
    }
    
    fb_file = FEEDBACK_DIR / f"{run_id}_feedback.json"
    with open(fb_file, "w") as f:
        json.dump(feedback, f, indent=2)

    if args.yolo:
        print("[*] YOLO AUTO-RENDER ENGAGED...")
        run_step("RENDER_YOLO", [
            "scripts/tts_render.py",
            "--in-file", str(latest_best),
            "--out-file", str(run_path / "audio.wav")
        ], cwd=FORGE_DIR)
        run_step("PACKAGE_YOLO", [
            "scripts/package_video.py",
            "--audio", str(run_path / "audio.wav"),
            "--out", str(run_path / "video.mp4")
        ], cwd=FORGE_DIR)

    print("-" * 50)
    print(f"[OK] SPRINT CYCLE COMPLETE: {run_id}")
    print(f"[OK] FEEDBACK TEMPLATE: {fb_file}")

if __name__ == "__main__":
    main()
