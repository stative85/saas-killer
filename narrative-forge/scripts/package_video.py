# package_video.py
import subprocess
import argparse
from pathlib import Path

def package(audio_path: Path, out_path: Path):
    print(f"[*] Packaging {audio_path.name} with High-Energy Visual Logic...")
    
    # TETRYEN VISUAL LOGIC: white wireframe grid over a dark neutral ground.
    #
    # drawgrid is a FILTER, not a source -- "-f lavfi -i drawgrid=..." is not a
    # valid input and ffmpeg refuses it outright. It has to be applied to the
    # colour source in the filter chain.
    #
    # The colour source also carried d=1, which with -shortest capped every
    # render at one second regardless of how long the narration ran. Left
    # open-ended here so -shortest takes its length from the audio instead.
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x111111:s=1280x720:r=30",
        "-i", str(audio_path),
        "-filter_complex",
        "[0:v]drawgrid=w=64:h=64:t=1:c=white@0.2[bg]",
        "-map", "[bg]", "-map", "1:a",
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
