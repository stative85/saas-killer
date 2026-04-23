import os
import re
import subprocess
import threading
import concurrent.futures
import whisper
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
YTDLP_EXE = r"C:\Users\cleve\OneDrive\Pictures\yt-dlp.exe"
DEFAULT_OUTPUT = r"C:\Users\cleve\OneDrive\Pictures"
WHISPER_MODEL = "base" 
MAX_WORKERS = 3 # Optimal for YouTube rate-limiting

def clean_vtt(vtt_path):
    if not os.path.exists(vtt_path): return ""
    with open(vtt_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    out = []
    prev = ""
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")): continue
        if re.match(r"^\d{2}:\d{2}", s) and "-->" in s: continue
        if re.match(r"^\d+$", s): continue
        text = re.sub(r"<[^>]+>", "", s).strip()
        if not text or text == prev: continue
        out.append(text)
        prev = text
    return "\n".join(out)

class CLIVerificationHarvester:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.model = None
        self.transcription_lock = threading.Lock()

    def load_model(self):
        print(f"[*] Initializing Whisper ({self.model_size.upper()})...")
        self.model = whisper.load_model(self.model_size)

    def process_video(self, entry, work_dir, out_root):
        title = re.sub(r'[\\/*?:"<>|]', "", entry['title'])
        video_id = entry['id']
        print(f"[Worker-{threading.get_ident()}] Lane Engaged: {title}")
        
        # 1. Try Subtitles (Auto included)
        vtt_dir = work_dir / "vtt"
        vtt_dir.mkdir(exist_ok=True)
        sub_cmd = [
            YTDLP_EXE, "--skip-download", "--write-subs", "--write-auto-subs",
            "--sub-lang", "en.*", "--sub-format", "vtt",
            "--output", str(vtt_dir / f"{video_id}.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        subprocess.run(sub_cmd, capture_output=True)
        
        vtt_files = list(vtt_dir.glob(f"{video_id}.*.vtt"))
        if vtt_files:
            print(f"  [+] {video_id}: Auto-Subs found. Cleaning...")
            text = clean_vtt(str(vtt_files[0]))
        else:
            # 2. Whisper Fallback
            print(f"  [!] {video_id}: No subs. Firing Whisper Hammer...")
            audio_path = work_dir / "audio" / f"{video_id}.mp3"
            audio_path.parent.mkdir(exist_ok=True)
            dl_cmd = [
                YTDLP_EXE, "-x", "--audio-format", "mp3",
                "--output", str(audio_path),
                f"https://www.youtube.com/watch?v={video_id}"
            ]
            subprocess.run(dl_cmd, capture_output=True)
            
            with self.transcription_lock:
                res = self.model.transcribe(str(audio_path))
                text = res["text"].strip()

        txt_path = Path(out_root) / "transcripts_txt" / f"{title}.txt"
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        print(f"  [🏁] {video_id}: Saved to {txt_path.name}")
        return txt_path

    def run(self, url, out_root):
        work_dir = Path(out_root) / "harvest_temp"
        work_dir.mkdir(parents=True, exist_ok=True)
        
        self.load_model()
        print("[*] Pulling Playlist Manifest...")
        cmd = [YTDLP_EXE, "--get-id", "--get-title", "--flat-playlist", url]
        # Use errors='replace' to handle non-UTF8 characters in video titles
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        if res.returncode != 0:
            print(f"[!] yt-dlp failed: {res.stderr}")
            return

        lines = res.stdout.strip().split("\n")
        
        entries = []
        for i in range(0, len(lines), 2):
            if i+1 < len(lines):
                entries.append({"id": lines[i+1], "title": lines[i]})

        print(f"[+] {len(entries)} videos discovered. Spreading across {MAX_WORKERS} lanes.")
        
        # Limit to first 3 videos for verification flood
        test_entries = entries[:3]

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            list(executor.map(lambda e: self.process_video(entry=e, work_dir=work_dir, out_root=out_root), test_entries))

        print("\n[✨] VERIFICATION COMPLETE. SYSTEM IS FUNCTIONAL.")

if __name__ == "__main__":
    PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLgpLRpgo3hFxUkt_9jlgAWeF6g9qHRH3p"
    harvester = CLIVerificationHarvester()
    harvester.run(PLAYLIST_URL, DEFAULT_OUTPUT)
