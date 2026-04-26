# shadow_publisher.py
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

# --- CONFIG ---
TARGET_PROFILE = "https://www.facebook.com/61588493966285/reels/" # Source of signal
REFINERY_ROOT = Path("C:/Users/cleve/Downloads/CLI/facebook_reel_harvester")
PYTHON = str(REFINERY_ROOT / "harvester_venv" / "Scripts" / "python.exe")

def run_loop():
    print(f"\n[🌑] SHADOW PUBLISHER ONLINE. Time: {datetime.now()}")
    
    while True:
        # 1. DISCOVER
        print("[*] Phase 1: Ninja Discovery...")
        subprocess.run([PYTHON, "ninja_discovery.py"]) # This finds reel IDs
        
        # 2. HARVEST & TRANSCRIBE
        # Watchdog is already running? If not, we trigger a harvest pass.
        print("[*] Phase 2: Signal Extraction...")
        subprocess.run([PYTHON, "harvester_watchdog.py"])
        
        # 3. REFINE
        # We find the latest harvested transcript and run a forge pass
        transcripts = sorted(list(Path("narrative_harvester/transcripts").glob("*.json")), key=lambda x: x.stat().st_mtime, reverse=True)
        if transcripts:
            latest = transcripts[0]
            run_id = f"shadow_run_{datetime.now().strftime('%m%d_%H%M')}"
            print(f"[>] Signal Found: {latest.name}. Launching Refinery {run_id}...")
            
            # Execute the full refinery loop
            subprocess.run([PYTHON, "narrative-forge/run_full.py", "--mode", "retention_aggressive", "--run-id", run_id])
            
            # 4. WEAPONIZE REVENUE
            # (Affiliate Mapper is already integrated in run_full.py)
            
            # 5. UPLOAD (Final Egress)
            # Future: Trigger headless YouTube/TikTok uploader here
            print(f"[✅] Shadow Asset Ready: outputs/runs/{run_id}/deploy_pack.json")
        
        print("[*] Loop Complete. Sleeping for 1 hour...")
        time.sleep(3600)

if __name__ == "__main__":
    run_loop()
