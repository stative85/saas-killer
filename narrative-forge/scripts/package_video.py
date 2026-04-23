# package_video.py
import subprocess
import argparse
from pathlib import Path

def package(audio_path: Path, out_path: Path):
    print(f"[*] Packaging {audio_path.name} into video...")
    
    # We'll use a simple black background for v1. 
    # Future: waveform or static concept art.
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=1", # Source image duration dummy
        "-i", str(audio_path),
        "-vf", "format=yuv420p",
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        print(f"[✅] Video packaged: {out_path}")
    else:
        print(f"[!] FFmpeg Error: {result.stderr.decode()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    
    package(Path(args.audio), Path(args.out))
