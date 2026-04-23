# ci_check.py
import json
import sys
from pathlib import Path

def run_check():
    base_p = Path("benchmarks/v0_baseline/score.json")
    new_p = Path("outputs/runs/ci_test/scores.json")

    if not base_p.exists() or not new_p.exists():
        print(f"FAIL: Comparison files missing. (Base: {base_p.exists()}, New: {new_p.exists()})")
        sys.exit(1)

    base = json.loads(base_p.read_text())
    new = json.loads(new_p.read_text())

    # Score Check (Tolerance of 0.05)
    if new["total"] < base["total"] - 0.05:
        print(f"FAIL: Score regression! {new['total']:.2f} < {base['total']:.2f}")
        sys.exit(1)
        
    # Novelty Check (Strict regression gate)
    base_novelty = base.get("novelty", 0.60) # Default baseline
    if new.get("novelty", 0.0) < base_novelty - 0.10:
        print(f"FAIL: Novelty collapse! {new['novelty']:.2f} < {base_novelty - 0.10:.2f}")
        sys.exit(1)

    print(f"PASS: System integrity maintained (Score: {new['total']:.2f}, Novelty: {new.get('novelty', 0.0):.2f})")

if __name__ == "__main__":
    run_check()
