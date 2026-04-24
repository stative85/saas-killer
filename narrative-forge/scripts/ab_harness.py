# ab_harness.py
import subprocess
import json
import argparse
import os
import re
from pathlib import Path
from datetime import datetime

# --- PATH LOCKDOWN ---
FORGE_DIR = Path(__file__).parent.parent.absolute()
ROOT_DIR = FORGE_DIR.parent
PYTHON_EXE = str(ROOT_DIR / "harvester_venv" / "Scripts" / "python.exe")
if not Path(PYTHON_EXE).exists():
    PYTHON_EXE = r"C:\Users\cleve\Downloads\CLI\facebook_reel_harvester\harvester_venv\Scripts\python.exe"

GENERATOR_SCRIPT = str(FORGE_DIR / "scripts" / "script_generator.py")
SCORER_SCRIPT = str(FORGE_DIR / "scripts" / "script_scorer.py")
BASE_EXPORT_DIR = FORGE_DIR / "outputs" / "scripts"

def run_harness(n_variants=5, mode="fracture", style="aggressive", chunks_file=None):
    if not chunks_file:
        chunks_file = r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks_with_arcs.jsonl"
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"run_{timestamp}"
    candidate_dir = BASE_EXPORT_DIR / "candidates" / run_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Starting Directed Evolution Run: {run_id}")
    
    for i in range(1, n_variants + 1):
        print(f"  [>] Generating Variant {i}/{n_variants}...")
        gen_mode = mode if "_" in mode else f"{mode}_aggressive"
        
        subprocess.run([
            str(PYTHON_EXE), str(GENERATOR_SCRIPT),
            "--chunks", str(chunks_file),
            "--mode", gen_mode,
            "--out", str(BASE_EXPORT_DIR / f"generated_script_{gen_mode}.txt")
        ], check=True, capture_output=True)
        
        src_file = BASE_EXPORT_DIR / f"generated_script_{gen_mode}.txt"
        dest_file = candidate_dir / f"variant_{i:02d}.txt"
        if src_file.exists():
            src_file.replace(dest_file)

    score_report = candidate_dir / "scores.json"
    print(f"[*] Scoring candidates...")
    subprocess.run([
        str(PYTHON_EXE), str(SCORER_SCRIPT),
        "--in-dir", str(candidate_dir),
        "--out", str(score_report)
    ], check=True, capture_output=True)

    with open(score_report, "r") as f:
        scores = json.load(f)
    
    best_candidate = scores[0]
    best_file = Path(best_candidate['file'])
    best_score = best_candidate['score']['total']
    
    best_export_dir = BASE_EXPORT_DIR / "best"
    best_export_dir.mkdir(exist_ok=True)
    
    final_output = best_export_dir / f"{run_id}_best.txt"
    final_scores = best_export_dir / f"{run_id}_scores.json"
    
    text = best_file.read_text(encoding="utf-8")
    provenance = f"\n\n[PROVENANCE]\nrun_id={run_id}\nmode={mode}\nscore={best_score:.2f}\n"
    
    with open(final_output, "w", encoding="utf-8") as f:
        f.write(text + provenance)
        
    with open(final_scores, "w", encoding="utf-8") as f:
        json.dump(best_candidate['score'], f, indent=2)

    print(f"\n[DONE] EVOLUTION COMPLETE.")
    print(f"[DONE] Best Variant: {final_output.name}")
    print(f"[DONE] Quality Score: {best_score:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--mode", default="fracture")
    parser.add_argument("--style", default="aggressive")
    parser.add_argument("--chunks", help="Path to chunks file")
    args = parser.parse_args()
    
    run_harness(n_variants=args.n, mode=args.mode, style=args.style, chunks_file=args.chunks)
