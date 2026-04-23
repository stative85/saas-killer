# ab_harness.py
import subprocess
import json
import argparse
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
PYTHON_EXE = r".\harvester_venv\Scripts\python.exe"
GENERATOR_SCRIPT = r"scripts\script_generator.py"
SCORER_SCRIPT = r"scripts\script_scorer.py"
CHUNKS_FILE = r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks_with_arcs.jsonl"
BASE_EXPORT_DIR = Path(r"C:\Users\cleve\OneDrive\Pictures\corpus_run\exports\scripts")

def run_harness(n_variants=5, mode="fracture", style="aggressive"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"run_{timestamp}"
    candidate_dir = BASE_EXPORT_DIR / "candidates" / run_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Starting Directed Evolution Run: {run_id}")
    
    # 1. Generate N Variants
    for i in range(1, n_variants + 1):
        print(f"  [>] Generating Variant {i}/{n_variants}...")
        subprocess.run([
            PYTHON_EXE, GENERATOR_SCRIPT,
            "--chunks", CHUNKS_FILE,
            "--mode", mode,
            "--style", style
        ], capture_output=True)
        
        # The generator saves to a default file, we move it to our candidate dir
        # (Assuming the generator writes 'generated_script_{mode}_{style}.txt')
        src_file = BASE_EXPORT_DIR / f"generated_script_{mode}_{style}.txt"
        dest_file = candidate_dir / f"variant_{i:02d}.txt"
        if src_file.exists():
            src_file.replace(dest_file)

    # 2. Score & Rank
    score_report = candidate_dir / "scores.json"
    print(f"[*] Scoring candidates...")
    subprocess.run([
        PYTHON_EXE, SCORER_SCRIPT,
        "--in-dir", str(candidate_dir),
        "--out", str(score_report)
    ])

    # 3. Select Best
    with open(score_report, "r") as f:
        scores = json.load(f)
    
    best_candidate = scores[0]
    best_file = Path(best_candidate['file'])
    best_score = best_candidate['score']['total']
    
    best_export_dir = BASE_EXPORT_DIR / "best"
    best_export_dir.mkdir(exist_ok=True)
    
    final_output = best_export_dir / f"{run_id}_best.txt"
    final_scores = best_export_dir / f"{run_id}_scores.json"
    
    # Copy best with Provenance Stamp
    text = best_file.read_text(encoding="utf-8")
    provenance = f"\n\n[PROVENANCE]\nrun_id={run_id}\nmode={mode}_{style}\nscore={best_score:.2f}\n"
    
    with open(final_output, "w", encoding="utf-8") as f:
        f.write(text + provenance)
        
    with open(final_scores, "w", encoding="utf-8") as f:
        json.dump(best_candidate['score'], f, indent=2)

    print(f"\n[💎] EVOLUTION COMPLETE.")
    print(f"[💎] Best Variant: {final_output.name}")
    print(f"[💎] Quality Score: {best_score:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--mode", default="fracture")
    parser.add_argument("--style", default="aggressive")
    args = parser.parse_args()
    
    run_harness(n_variants=args.n, mode=args.mode, style=args.style)
