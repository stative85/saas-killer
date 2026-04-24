# evidence_archive.py
import json
import shutil
import hashlib
import yaml
import argparse
from pathlib import Path
from datetime import datetime

# --- PATHS ---
FORGE_DIR = Path(__file__).parent.parent.absolute()
RUNS_DIR = FORGE_DIR / "outputs" / "runs"
CONFIG_FILE = FORGE_DIR / "configs" / "default.yaml"

def get_dir_hash(path: Path) -> str:
    """Computes a composite hash of all files in a directory."""
    hasher = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            # Update with relative path and file content
            hasher.update(str(f.name).encode())
            with open(f, "rb") as rb:
                for chunk in iter(lambda: rb.read(4096), b""):
                    hasher.update(chunk)
    return hasher.hexdigest()

def archive_run(run_dir: Path, archive_base: Path):
    run_id = run_dir.name
    dest = archive_base / run_id
    
    print(f"[*] Archiving {run_id} -> {dest}")
    
    # 1. Calculate Source Hash
    src_hash = get_dir_hash(run_dir)
    
    # 2. Copy (Non-destructive)
    if dest.exists():
        print(f"  [!] Collision detected at {dest}. Verifying existing...")
        if get_dir_hash(dest) == src_hash:
            print(f"  [OK] Archive already contains identical data.")
        else:
            print(f"  [!] Archive collision has different hash. Backing up old archive.")
            dest.rename(dest.with_suffix(".bak_" + datetime.now().strftime("%H%M%S")))
            shutil.copytree(run_dir, dest)
    else:
        shutil.copytree(run_dir, dest)
    
    # 3. Verify Integrity
    dest_hash = get_dir_hash(dest)
    if src_hash != dest_hash:
        print(f"  [🛑] CRITICAL: Hash mismatch! {src_hash[:8]} != {dest_hash[:8]}")
        return False

    # 4. Seal with Receipt
    receipt = {
        "archived_at": datetime.now().isoformat(),
        "run_id": run_id,
        "hash": src_hash,
        "status": "VERIFIED"
    }
    with open(dest / "archive_receipt.json", "w") as f:
        json.dump(receipt, f, indent=2)
    
    # 5. Prune (Only after verification)
    print(f"  [OK] Verified. Pruning original...")
    shutil.rmtree(run_dir)
    return True

def main():
    # Load Config
    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)
    
    archive_base = Path(config.get("archive", {}).get("path", "D:/WENDIGO_ARCHIVE"))
    archive_base.mkdir(parents=True, exist_ok=True)

    print(f"\n[WENDIGO] Evidence Archive Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"[*] Base: {archive_base}")
    print("-" * 50)

    if not RUNS_DIR.exists():
        print("[!] No runs directory found.")
        return

    count = 0
    for run_dir in RUNS_DIR.iterdir():
        if not run_dir.is_dir(): continue
        
        bundle_path = run_dir / "forensic_bundle.json"
        if not bundle_path.exists(): continue
        
        with open(bundle_path, "r") as f:
            bundle = json.load(f)
            
        # Only archive runs that have been ingested into memory
        if bundle.get("feedback_status") == "ingested":
            if archive_run(run_dir, archive_base):
                count += 1
                
    print(f"-" * 50)
    print(f"[✅] Cycle Complete. {count} runs archived and verified.")

if __name__ == "__main__":
    main()
