# package_video.py
import subprocess
import argparse
from pathlib import Path

def package(audio_path: Path, out_path: Path):
    print(f"[*] Packaging {audio_path.name} with High-Energy Visual Logic...")
    
    # TETRYEN VISUAL LOGIC: High-energy white grid on dark neutral background
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x111111:s=1280x720:d=1", # Neutral Dark
        "-f", "lavfi", "-i", "drawgrid=w=64:h=64:t=1:c=white@0.2", # Geometric Wireframe
        "-i", str(audio_path),
        "-filter_complex", "[0][1]overlay=shortest=1[bg]", # Combine Grid and Color
        "-map", "[bg]", "-map", "2:a", # Map processed visual and raw audio
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        print(f"[✅] Visual Logic Deployed: {out_path}")
    else:
        print(f"[!] FFmpeg Error: {result.stderr.decode()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    
    package(Path(args.audio), Path(args.out))
