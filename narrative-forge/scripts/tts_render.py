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
    
    # Cut the provenance appendix FIRST. It quotes every source passage as
    # "> ..." lines, which the legacy matcher below would happily narrate --
    # putting the raw stuttering transcript straight back into the audio the
    # rewrite existed to remove.
    raw_text = raw_text.split("--- SOURCE PROVENANCE ---")[0]

    clean_text = ""
    # LEGACY FORMAT: the chunk compiler emits narration as "> line".
    content_lines = re.findall(r"^>\s*(.+)$", raw_text, re.MULTILINE)

    for line in content_lines:
        # Remove markdown artifacts and double angles
        line = line.replace("&gt;&gt;", "").replace("&gt;", "").strip()
        if line:
            clean_text += line + " "

    if not clean_text.strip():
        # WRITTEN FORMAT (script_generator --write): plain prose under [BEAT]
        # headers, followed by a SOURCE PROVENANCE appendix. Narrate the prose
        # only -- reading the headers and the appendix aloud would put the raw
        # transcript back into the audio, which is the exact thing the rewrite
        # removed.
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("---") and line.endswith("---"):
                continue          # title rule
            if re.match(r"^\[[A-Z_ ]+\]", line):
                continue          # [HOOK], [BUILD_TRUTH], [DIAGNOSTICS] ...
            if line.startswith(">"):
                continue          # already handled above
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
