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
    """Computes a composite hash of all files in a directory, excluding the receipt."""
    hasher = hashlib.sha256()
    # Sort files to ensure deterministic hashing
    for f in sorted(path.rglob("*")):
        if f.is_file() and f.name != "archive_receipt.json":
            # 1. FIX: Hash relative path, not bare name
            rel_path = f.relative_to(path)
            hasher.update(str(rel_path).encode())
            # 2. Hash content
            with open(f, "rb") as rb:
                for chunk in iter(lambda: rb.read(4096), b""):
                    hasher.update(chunk)
    return hasher.hexdigest()

def archive_run(run_dir: Path, archive_base: Path, should_verify: bool):
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
            backup_path = dest.with_suffix(f".bak_{datetime.now().strftime('%H%M%S')}")
            dest.rename(backup_path)
            shutil.copytree(run_dir, dest)
    else:
        shutil.copytree(run_dir, dest)
    
    # 3. Verify Integrity (Respecting Config)
    if should_verify:
        dest_hash = get_dir_hash(dest)
        if src_hash != dest_hash:
            print(f"  [🛑] CRITICAL: Hash mismatch! {src_hash[:8]} != {dest_hash[:8]}")
            return False
        print(f"  [OK] Integrity Verified ({src_hash[:8]})")

    # 4. Seal with Receipt (Excluded from hash in Step 1)
    receipt = {
        "archived_at": datetime.now().isoformat(),
        "run_id": run_id,
        "hash": src_hash,
        "status": "VERIFIED" if should_verify else "COPIED"
    }
    with open(dest / "archive_receipt.json", "w") as f:
        json.dump(receipt, f, indent=2)
    
    # 5. Prune
    print(f"  [OK] Sealed. Pruning original...")
    shutil.rmtree(run_dir)
    return True

def main():
    # Load Config
    if not CONFIG_FILE.exists():
        print(f"[!] Error: Config missing at {CONFIG_FILE}")
        return

    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)
    
    archive_config = config.get("archive", {})
    archive_base = Path(archive_config.get("path", "D:/WENDIGO_ARCHIVE"))
    verify_hashes = archive_config.get("verify_hashes", True) # Honor the law
    
    archive_base.mkdir(parents=True, exist_ok=True)

    print(f"\n[WENDIGO] Evidence Archive Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"[*] Base: {archive_base}")
    print(f"[*] Hash Verification: {'ENABLED' if verify_hashes else 'DISABLED'}")
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
            
        if bundle.get("feedback_status") == "ingested":
            if archive_run(run_dir, archive_base, verify_hashes):
                count += 1
                
    print(f"-" * 50)
    print(f"[✅] Cycle Complete. {count} runs archived.")

if __name__ == "__main__":
    main()
