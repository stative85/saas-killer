# run_full.py
import argparse
import subprocess
import os
import json
import csv
from pathlib import Path
from datetime import datetime

# --- PATHS ---
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
CONFIG_DIR = BASE_DIR / "configs"
OUTPUTS_DIR = BASE_DIR / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
LEDGER_FILE = OUTPUTS_DIR / "run_ledger.csv"

def run_step(name, cmd):
    print(f"[*] Executing {name}...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(f"[!] Error in {name}: {result.stderr}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="NARRATIVE FORGE - FULL PIPELINE")
    parser.add_argument("--playlist", help="YouTube Playlist URL to harvest")
    parser.add_argument("--run-id", default="auto", help="Custom Run ID")
    args = parser.parse_args()

    # 1. Setup Run ID
    run_id = args.run_id if args.run_id != "auto" else datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_path = RUNS_DIR / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    
    raw_dir = run_path / "raw"
    repaired_dir = run_path / "repaired"
    corpus_dir = run_path / "corpus"
    
    print(f"\n🐺 WENDIGO NARRATIVE FORGE - RUN: {run_id}")
    print("-" * 50)

    # 2. HARVEST (Optional if playlist provided)
    if args.playlist:
        raw_dir.mkdir(exist_ok=True)
        # Use our headless parallel harvester
        run_step("HARVEST", ["python", str(SCRIPTS_DIR / "headless_harvester_v3.py"), "--url", args.playlist, "--out", str(raw_dir)])
    else:
        # Fallback: assume data exists in common store or user provided
        print("[!] No playlist provided. Skipping harvest. Using existing raw data if available.")

    # 3. REPAIR
    run_step("REPAIR", ["python", str(SCRIPTS_DIR / "repair_forge.py"), "--input-dir", str(raw_dir), "--output-dir", str(repaired_dir)])

    # 4. INDEX
    run_step("INDEX", ["python", str(SCRIPTS_DIR / "post_harvest_indexer.py"), "--input-dir", str(repaired_dir), "--output-dir", str(corpus_dir)])

    # 5. EVOLVE (A/B HARNESS)
    # The A/B Harness already coordinates generator + scorer
    print("[*] Engaging Evolutionary Harness...")
    subprocess.run([
        "python", str(SCRIPTS_DIR / "ab_harness.py"),
        "--n", "5",
        "--chunks", str(corpus_dir / "index" / "chunks.jsonl"),
        "--out-dir", str(run_path / "generation")
    ])

    # 6. EXTRACT BEST
    # We move the winning script and scores to the run root
    gen_dir = run_path / "generation"
    best_file = gen_dir / "best_variant.txt"
    if best_file.exists():
        best_file.replace(run_path / "best_narrative.txt")
        (gen_dir / "best_scores.json").replace(run_path / "scores.json")

    # 7. LOG TO LEDGER
    score = 0.0
    if (run_path / "scores.json").exists():
        with open(run_path / "scores.json", "r") as f:
            score = json.load(f).get("total", 0.0)

    with open(LEDGER_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["run_id", "timestamp", "score", "status"])
        writer.writerow([run_id, datetime.now().isoformat(), score, "COMPLETE"])

    print("-" * 50)
    print(f"[✅] PIPELINE COMPLETE: {run_path / 'best_narrative.txt'}")
    print(f"[✅] FINAL SCORE: {score:.2f}")

if __name__ == "__main__":
    main()
