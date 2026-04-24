# infowars_inhaler.py
import os
import random
import shutil
from pathlib import Path

# --- CONFIG ---
SOURCE_BASE = Path(r"D:\infowars-main\infowars-main\transcripts\alex-jones-show")
TARGET_RAW = Path(r"C:\Users\cleve\Downloads\CLI\facebook_reel_harvester\narrative-forge\outputs\infowars_raw")
SAMPLE_SIZE = 15 # Files per year

def inhale():
    print(f"[*] INFOWARS INHALER ENGAGED. Sampling {SAMPLE_SIZE} files per epoch...")
    TARGET_RAW.mkdir(parents=True, exist_ok=True)

    years = sorted([d.name for d in SOURCE_BASE.iterdir() if d.is_dir()])
    
    total_inhaled = 0
    for year in years:
        year_path = SOURCE_BASE / year
        files = list(year_path.glob("*.txt"))
        
        if not files: continue
        
        sample = random.sample(files, min(SAMPLE_SIZE, len(files)))
        print(f"  [>] Inhaling {year}: {len(sample)} fragments.")
        
        for f in sample:
            # Flatten into a single dir with year prefix for indexing
            dest = TARGET_RAW / f"{year}_{f.name}"
            shutil.copy(f, dest)
            total_inhaled += 1

    print(f"\n[✅] INHALATION COMPLETE. {total_inhaled} high-entropy fragments ready for the Forge.")

if __name__ == "__main__":
    inhale()
