# tts_render.py
import asyncio
import edge_tts
import argparse
import sys
import re
from pathlib import Path

DEFAULT_VOICE = "en-US-ChristopherNeural"

async def render(text_path: Path, out_path: Path, voice: str):
    print(f"[*] Reading text from {text_path}...")
    raw_text = text_path.read_text(encoding="utf-8")
    
    clean_text = ""
    # Regex to find lines starting with >
    content_lines = re.findall(r"^>\s*(.+)$", raw_text, re.MULTILINE)
    
    for line in content_lines:
        # Remove markdown artifacts and double angles
        line = line.replace("&gt;&gt;", "").replace("&gt;", "").strip()
        if line:
            clean_text += line + " "

    if not clean_text.strip():
        print("[!] No text found to narrate! Check your script format.")
        sys.exit(1)

    print(f"[*] Text Extracted ({len(clean_text)} chars).")
    print(f"[*] Communicating with Edge TTS (Voice: {voice})...")
    
    try:
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(str(out_path))
        
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"[✅] Narration complete: {out_path} ({out_path.stat().st_size} bytes)")
        else:
            print(f"[!] Error: Output file is empty!")
            sys.exit(1)
            
    except Exception as e:
        print(f"[!] TTS Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-file", required=True)
    parser.add_argument("--out-file", required=True)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    args = parser.parse_args()
    
    asyncio.run(render(Path(args.in_file), Path(args.out_file), args.voice))
