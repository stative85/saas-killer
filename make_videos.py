"""MAKE VIDEOS - one command. Transcripts in, finished videos out.

    python make_videos.py --input <folder-of-transcripts> --count 5

That is the whole interface. It runs every stage in order and tells you which
one failed if one does, instead of leaving you to guess:

    1. DESTUTTER   YouTube auto-captions repeat every line ~3x as they scroll.
                   Nothing else in this repo calls destutter_forge, and
                   repair_forge leaves the repetition untouched -- so without
                   this step every later stage reads each sentence three times.
    2. INDEX       chunk, score, promote the top ~15% as "hot"
    3. WRITE       rewrite selected beats into narration with a LOCAL model
                   (LM Studio / llama.cpp / Ollama). No API key, no per-call
                   cost, and the source archive never leaves this machine.
    4. NARRATE     Edge TTS -> mp3
    5. PACKAGE     ffmpeg -> 1280x720 mp4

Every script keeps a SOURCE PROVENANCE appendix naming the passage each beat
came from, so any line can be checked against the original tape.

REQUIRES: ffmpeg on PATH, `pip install edge-tts`, and a local model server
running (LM Studio on 127.0.0.1:1234 by default).
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.absolute()
SCRIPTS = ROOT / "narrative-forge" / "scripts"


def run(label, cmd, quiet=False):
    """Run a stage. Returns (ok, output). UTF-8 forced: these scripts print
    emoji, and a Windows cp1252 console kills them mid-write otherwise."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable] + [str(c) for c in cmd],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    ok = p.returncode == 0
    if not ok and not quiet:
        tail = (p.stderr or p.stdout or "").strip().splitlines()
        print("    [X] %s failed:" % label)
        for line in tail[-4:]:
            print("        " + line)
    return ok, (p.stdout or "")


def main():
    ap = argparse.ArgumentParser(description="Transcripts in, videos out.")
    ap.add_argument("--input", required=True, type=Path,
                    help="Folder of .txt transcripts")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "videos")
    ap.add_argument("--count", type=int, default=3, help="How many videos")
    ap.add_argument("--mode", default="retention",
                    choices=["retention", "fracture"])
    ap.add_argument("--style", default="aggressive",
                    choices=["aggressive", "humanist"])
    ap.add_argument("--llm-model", default=os.environ.get("LOCAL_LLM_MODEL", ""),
                    help="Local model id. Blank = whatever is loaded.")
    ap.add_argument("--voice", default="en-US-ChristopherNeural")
    ap.add_argument("--keep-work", action="store_true",
                    help="Keep intermediate files for inspection")
    args = ap.parse_args()

    if not args.input.is_dir():
        sys.exit("[X] --input is not a folder: %s" % args.input)
    srcs = sorted([p for p in args.input.iterdir()
                   if p.suffix.lower() in (".txt", ".srt", ".vtt")])
    if not srcs:
        sys.exit("[X] no .txt/.srt/.vtt files in %s" % args.input)
    if not shutil.which("ffmpeg"):
        sys.exit("[X] ffmpeg is not on PATH. Install it first -- no video "
                 "can be produced without it.")

    work = args.out / ("_work_%d" % int(time.time()))
    clean = work / "clean"
    idx = work / "index"
    scripts_dir = work / "scripts"
    for d in (clean, idx, scripts_dir, args.out):
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 62)
    print(" MAKE VIDEOS  |  %d source files  ->  %d videos"
          % (len(srcs), args.count))
    print("=" * 62)

    # 1. DESTUTTER ---------------------------------------------------------
    print("\n[1/5] De-stuttering %d file(s)..." % len(srcs))
    kept = 0
    for i, s in enumerate(srcs, 1):
        # Copy to an ASCII name first: several of these scripts choke on the
        # fullwidth colon and other characters common in YouTube filenames.
        tmp = work / ("_src_%03d.txt" % i)
        try:
            tmp.write_text(s.read_text(encoding="utf-8", errors="replace"),
                           encoding="utf-8")
        except Exception as exc:
            print("    [!] skip %s (%s)" % (s.name, exc))
            continue
        out = clean / ("doc_%03d.txt" % i)
        ok, _ = run("destutter", [SCRIPTS / "destutter_forge.py",
                                  "--input", tmp, "--output", out], quiet=True)
        if ok and out.exists() and out.stat().st_size > 0:
            kept += 1
            before, after = tmp.stat().st_size, out.stat().st_size
            pct = (100.0 * (before - after) / before) if before else 0
            print("    %-28s %7d -> %6d bytes  (-%.0f%%)"
                  % (s.name[:28], before, after, pct))
        else:
            # Not fatal: use the raw file rather than dropping the source.
            shutil.copy(tmp, out)
            kept += 1
            print("    %-28s de-stutter failed, using raw" % s.name[:28])
        tmp.unlink(missing_ok=True)
    if kept == 0:
        sys.exit("[X] nothing survived stage 1.")

    # 2. INDEX -------------------------------------------------------------
    print("\n[2/5] Indexing...")
    ok, out = run("index", [SCRIPTS / "post_harvest_indexer.py",
                            "--input-dir", clean, "--output-dir", idx])
    if not ok:
        sys.exit("[X] indexing failed.")
    print("    " + out.strip().splitlines()[-1])
    hot = idx / "index" / "chunks_hot.jsonl"
    allc = idx / "index" / "chunks.jsonl"
    chunks = hot if hot.exists() and hot.stat().st_size > 0 else allc
    if not chunks.exists():
        sys.exit("[X] indexer produced no chunks.")

    # 3. WRITE -------------------------------------------------------------
    print("\n[3/5] Writing %d script(s) with a local model..." % args.count)
    cmd = [SCRIPTS / "script_generator.py", "--chunks", chunks,
           "--out", scripts_dir / "script.txt", "--write",
           "--mode", args.mode, "--style", args.style,
           "--count", str(args.count)]
    if args.llm_model:
        cmd += ["--llm-model", args.llm_model]
    ok, out = run("write", cmd)
    if not ok:
        sys.exit("[X] script writing failed. Is a local model server running "
                 "on 127.0.0.1:1234? Start LM Studio, or set LOCAL_LLM_URL.")
    for line in out.strip().splitlines():
        if line.startswith("[*]") or line.startswith("[DONE]"):
            print("    " + line)

    written = sorted(scripts_dir.glob("script_*.txt"))
    if not written:
        one = scripts_dir / "script.txt"
        written = [one] if one.exists() else []
    if not written:
        sys.exit("[X] no scripts were produced.")

    # 4 + 5. NARRATE AND PACKAGE ------------------------------------------
    print("\n[4/5] Narrating and [5/5] packaging %d video(s)..." % len(written))
    made = []
    for i, sp in enumerate(written, 1):
        mp3 = work / ("narration_%02d.mp3" % i)
        mp4 = args.out / ("video_%02d.mp4" % i)
        ok, _ = run("tts", [SCRIPTS / "tts_render.py", "--in-file", sp,
                            "--out-file", mp3, "--voice", args.voice])
        if not ok:
            print("    [!] %d: narration failed, skipping" % i)
            continue
        ok, _ = run("package", [SCRIPTS / "package_video.py",
                                "--audio", mp3, "--out", mp4])
        if ok and mp4.exists():
            made.append(mp4)
            print("    [OK] %s  (%.1f MB)"
                  % (mp4.name, mp4.stat().st_size / 1e6))
            # Keep the script next to its video: it carries the provenance a
            # client needs to verify any line.
            shutil.copy(sp, args.out / (mp4.stem + "_script.txt"))
        else:
            print("    [!] %d: packaging failed" % i)

    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)

    print("\n" + "=" * 62)
    if made:
        print(" DONE: %d video(s) in %s" % (len(made), args.out))
        print(" Each has a _script.txt beside it with source provenance.")
    else:
        print(" NOTHING PRODUCED. The failing stage is named above.")
        sys.exit(1)
    print("=" * 62)


if __name__ == "__main__":
    main()
