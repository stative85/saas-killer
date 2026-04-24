# stress_test.py
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime

# --- PATHS ---
FORGE_DIR = Path(__file__).parent.parent.absolute()
RUN_FULL = FORGE_DIR / "run_full.py"
PYTHON_EXE = str(FORGE_DIR.parent / "harvester_venv" / "Scripts" / "python.exe")

def run_stress(count=10):
    print(f"\n[STRESSOR] Initiating {count}-run Operational Pressure...")
    print(f"[*] Target: {RUN_FULL}")
    
    start_time = time.time()
    success_count = 0
    
    for i in range(1, count + 1):
        mode = "retention_aggressive" if i % 2 == 0 else "fracture_aggressive"
        run_id = f"stress_test_{i:02d}_{datetime.now().strftime('%H%M%S')}"
        
        print(f"\n[>] Run {i}/{count} | ID: {run_id} | Mode: {mode}")
        
        cmd = [PYTHON_EXE, str(RUN_FULL), "--mode", mode, "--run-id", run_id]
        
        # Capture output to prevent terminal flood but log result
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        if result.returncode == 0:
            print(f"  [OK] Run {i} Successful.")
            success_count += 1
        else:
            print(f"  [🛑] Run {i} Failed. Error: {result.stderr[:200]}")

    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print(f"[💎] STRESS TEST COMPLETE")
    print(f"  - Success: {success_count}/{count}")
    print(f"  - Total Duration: {duration:.2f}s")
    print(f"  - Avg Run Time: {duration/count:.2f}s")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10)
    args = parser.parse_args()
    run_stress(args.n)
