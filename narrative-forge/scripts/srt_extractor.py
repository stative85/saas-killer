import os
import argparse
import re
from pathlib import Path

def extract_srt(srt_path: Path, out_path: Path):
    print(f"[*] Extracting raw speech from: {srt_path.name}")
    content = srt_path.read_text(encoding="utf-8", errors="replace")
    
    # Split into SRT blocks
    blocks = content.split("\n\n")
    clean_text = []
    
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3: continue
        # Lines[0] is index, Lines[1] is timestamp, Lines[2:] is text
        text = " ".join(lines[2:]).strip()
        # Remove simple HTML tags often found in SRT
        text = re.sub(r"<[^>]+>", "", text)
        if text:
            clean_text.append(text)
            
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(clean_text), encoding="utf-8")
    print(f"[✅] Extracted {len(clean_text)} speech blocks to {out_path.name}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    
    for srt in args.in_dir.glob("*.srt"):
        out_file = args.out_dir / f"{srt.stem}.txt"
        extract_srt(srt, out_file)

if __name__ == "__main__":
    main()
