# run_full.py
import argparse
import subprocess
import os
import json
import csv
import math
from pathlib import Path
from datetime import datetime

# --- CONFIG ---
MIN_TOTAL_SCORE = 0.50
SIMILARITY_THRESHOLD = 0.80

# --- PATHS ---
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUTS_DIR = BASE_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
REGISTRY_FILE = OUTPUTS_DIR / "runs_registry.csv"

def get_jaccard_sim(str1, str2):
    a = set(str1.lower().split())
    b = set(str2.lower().split())
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))

def validate_script(text, score, run_id):
    # 1. Arc Balance Gate
    need = ["[HOOK]", "[BUILD", "[COLLISION]", "[RESOLUTION]"]
    if not all(k in text for k in need):
        return False, "MISSING_ARCS"
    
    # 2. Score Gate
    if score < MIN_TOTAL_SCORE:
        return False, f"LOW_SCORE_{score:.2f}"
    
    # 3. Similarity Gate (Anti-Echo)
    best_dir = OUTPUTS_DIR / "best"
    if best_dir.exists():
        for prior in best_dir.glob("*.txt"):
            prior_text = prior.read_text(encoding="utf-8")
            sim = get_jaccard_sim(text, prior_text)
            if sim > SIMILARITY_THRESHOLD:
                return False, f"SIMILARITY_STRIKE_{sim:.2f}"
                
    return True, "ACCEPTED"

def run_step(name, cmd, cwd=None):
    print(f"[*] Executing {name}...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    if result.returncode != 0:
        print(f"[!] Error in {name}: {result.stderr}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlist", help="Playlist URL")
    parser.add_argument("--run-id", default="auto")
    args = parser.parse_args()

    run_id = args.run_id if args.run_id != "auto" else datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_path = RUNS_DIR / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🐺 NARRATIVE FORGE RUN: {run_id}")

    # HARVEST -> REPAIR -> INDEX -> EVOLVE
    # (Simplified sequence calls scripts/ stubs for v1)
    python_exe = "python"
    
    # Run the chain (Checkpoints would be added here)
    run_step("HARVEST/REPAIR/INDEX", [python_exe, "scripts/headless_harvester_v3.py"], cwd=BASE_DIR) 

    # EVOLVE
    run_step("A/B HARNESS", [python_exe, "scripts/ab_harness.py", "--n", "5"], cwd=BASE_DIR)

    # GATE KEEPER
    best_file = BASE_DIR / "outputs/scripts/generated_script_fracture_aggressive.txt" # Harness output
    score_file = BASE_DIR / "outputs/scripts/best_scores.json" # Harness output
    
    accepted = False
    status = "REJECTED"
    final_score = 0.0

    if best_file.exists():
        text = best_file.read_text(encoding="utf-8")
        with open(score_file, "r") as f:
            scores = json.load(f)
            final_score = scores.get("total", 0.0)
        
        ok, reason = validate_script(text, final_score, run_id)
        status = reason
        if ok:
            accepted = True
            (OUTPUTS_DIR / "best").mkdir(exist_ok=True)
            best_file.replace(OUTPUTS_DIR / "best" / f"{run_id}_best.txt")
            print(f"[✅] SCRIPT ACCEPTED: {final_score:.2f}")
        else:
            print(f"[🛑] SCRIPT REJECTED: {reason}")

    # REGISTRY
    with open(REGISTRY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["run_id", "timestamp", "score", "status", "accepted"])
        writer.writerow([run_id, datetime.now().isoformat(), final_score, status, accepted])

if __name__ == "__main__":
    main()
