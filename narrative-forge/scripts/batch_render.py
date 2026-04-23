# batch_render.py
import subprocess
import os
from pathlib import Path

# --- PATHS ---
FORGE_DIR = Path(__file__).parent.parent.absolute()
SCRIPTS_DIR = FORGE_DIR / "scripts"
BEST_DIR = FORGE_DIR / "outputs" / "scripts" / "best"
RUNS_BASE = FORGE_DIR / "outputs" / "runs"
PYTHON_EXE = str(FORGE_DIR.parent / "harvester_venv" / "Scripts" / "python.exe")

RUN_MAP = {
    "run_2026-04-22_193859": "sprint_run_001",
    "run_2026-04-22_193919": "sprint_run_002",
    "run_2026-04-22_193925": "sprint_run_003",
    "run_2026-04-22_194154": "sprint_run_004",
    "run_2026-04-22_194201": "sprint_run_005"
}

def run_render(ts_id, sprint_id):
    script_file = BEST_DIR / f"{ts_id}_best.txt"
    run_dir = RUNS_BASE / sprint_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    audio_file = run_dir / "audio.wav"
    video_file = run_dir / "video.mp4"
    
    if not script_file.exists():
        print(f"[!] Skip {ts_id}: Script missing.")
        return

    print(f"[*] Rendering {sprint_id} from {ts_id}...")
    
    # 1. TTS
    subprocess.run([
        PYTHON_EXE, str(SCRIPTS_DIR / "tts_render.py"),
        "--in-file", str(script_file),
        "--out-file", str(audio_file)
    ], check=True)
    
    # 2. Package
    subprocess.run([
        PYTHON_EXE, str(SCRIPTS_DIR / "package_video.py"),
        "--audio", str(audio_file),
        "--out", str(video_file)
    ], check=True)
    
    print(f"[✅] Rendered: {video_file}")

if __name__ == "__main__":
    for ts, sprint in RUN_MAP.items():
        try:
            run_render(ts, sprint)
        except Exception as e:
            print(f"[!] Failed {sprint}: {e}")
