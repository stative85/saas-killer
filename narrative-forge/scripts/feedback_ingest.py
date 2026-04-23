# feedback_ingest.py
import json
import argparse
import re
from pathlib import Path
from collections import Counter

# --- PATHS ---
BEST_DIR = Path(r"C:\Users\cleve\OneDrive\Pictures\corpus_run\exports\scripts\best")
BIAS_CONFIG = Path(r"narrative-forge\configs\bias_store.json")

def ingest(run_id, views, watch_ratio):
    print(f"[*] Ingesting feedback for Run: {run_id}")
    
    script_file = BEST_DIR / f"{run_id}_best.txt"
    if not script_file.exists():
        print(f"[!] Script not found for {run_id}")
        return

    text = script_file.read_text(encoding="utf-8").lower()
    # Extract significant words (len > 5)
    words = re.findall(r"\b\w{6,}\b", text)
    
    # Load bias store
    if BIAS_CONFIG.exists():
        with open(BIAS_CONFIG, "r") as f:
            store = json.load(f)
    else:
        store = {"positive": [], "negative": []}

    # THRESHOLDS
    if views > 1000 and watch_ratio > 0.40:
        print(f"  [+] Performance Peak detected. Boosting terms.")
        store["positive"] = list(set(store["positive"] + words))[:200]
    elif views < 100 or watch_ratio < 0.15:
        print(f"  [-] Performance Drop detected. Penalizing terms.")
        store["negative"] = list(set(store["negative"] + words))[:200]
    
    with open(BIAS_CONFIG, "w") as f:
        json.dump(store, f, indent=2)
    
    print(f"[✅] Feedback Loop Closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--views", type=int, default=0)
    parser.add_argument("--watch", type=float, default=0.0)
    args = parser.parse_args()
    
    ingest(args.run_id, args.views, args.watch)
