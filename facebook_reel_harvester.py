import os
import re
import json
import whisper
import yt_dlp
import argparse
import concurrent.futures
import time
import random
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# --- CONFIGURATION & HARDENING ---
URLS_FILE = Path("narrative_harvester/urls.txt")
BASE_DIR = Path("narrative_harvester")
AUDIO_DIR = BASE_DIR / "audio"
VIDEO_DIR = BASE_DIR / "video"  # For future OCR passes
TRANSCRIPT_DIR = BASE_DIR / "transcripts"
METADATA_DIR = BASE_DIR / "metadata"
MASTER_REPORT = BASE_DIR / "MASTER_HARVEST_REPORT.md"

for d in [AUDIO_DIR, VIDEO_DIR, TRANSCRIPT_DIR, METADATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class ReelMachine:
    def __init__(self, model_name="base", browser=None):
        self.model_name = model_name
        self.browser = browser
        self.model = None
        self.stats = {"success": 0, "failed": 0, "skipped": 0}

    def load_model(self):
        if not self.model:
            print(f"[*] Loading Whisper {self.model_name.upper()} model...")
            self.model = whisper.load_model(self.model_name)

    def get_ydl_opts(self, is_video=False):
        opts = {
            'format': 'bestvideo+bestaudio/best' if is_video else 'bestaudio/best',
            'outtmpl': str((VIDEO_DIR if is_video else AUDIO_DIR) / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'playlist_items': None, 
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
            'sleep_interval': 3,
            'max_sleep_interval': 7,
        }
        if not is_video:
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        if self.browser:
            opts['cookiesfrombrowser'] = (self.browser,)
        return opts

    def download(self, url):
        # Human-like delay before starting each download
        time.sleep(random.uniform(2, 5))
        with yt_dlp.YoutubeDL(self.get_ydl_opts()) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                if not info: return []
                entries = info.get('entries', [info])
                files = []
                for entry in entries:
                    if entry:
                        base_path = ydl.prepare_filename(entry).rsplit('.', 1)[0]
                        files.append({
                            "path": base_path + ".mp3",
                            "title": entry.get('title', 'Unknown'),
                            "url": entry.get('webpage_url', url),
                            "duration": entry.get('duration'),
                            "uploader": entry.get('uploader')
                        })
                return files
            except Exception as e:
                print(f"[!] Download failed for {url}: {e}")
                return []

    def transcribe(self, item):
        audio_path = Path(item['path'])
        if not audio_path.exists(): return None
        
        transcript_path = TRANSCRIPT_DIR / (audio_path.stem + ".json")
        if transcript_path.exists():
            self.stats["skipped"] += 1
            with open(transcript_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        try:
            print(f"[*] Transcribing: {audio_path.name}")
            result = self.model.transcribe(str(audio_path), verbose=False)
            
            # Robust data structure
            data = {
                "metadata": item,
                "text": result["text"].strip(),
                "segments": [{
                    "start": s["start"],
                    "end": s["end"],
                    "text": s["text"].strip()
                } for s in result["segments"]],
                "harvest_date": datetime.now().isoformat()
            }
            
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Also save as clean text for easy reading
            with open(TRANSCRIPT_DIR / (audio_path.stem + ".txt"), "w", encoding="utf-8") as f:
                f.write(data["text"])
                
            self.stats["success"] += 1
            return data
        except Exception as e:
            print(f"[!] Transcription failed for {audio_path.name}: {e}")
            self.stats["failed"] += 1
            return None

def compile_master_report(results):
    with open(MASTER_REPORT, "w", encoding="utf-8") as f:
        f.write(f"# 🛡️ TOTAL HARVEST REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for i, res in enumerate(results):
            if not res: continue
            meta = res['metadata']
            f.write(f"## {i+1}. {meta['title']}\n")
            f.write(f"- **URL:** {meta['url']}\n")
            f.write(f"- **Uploader:** {meta['uploader']}\n")
            f.write(f"- **Duration:** {meta['duration']}s\n\n")
            f.write("### 📝 Transcript\n")
            f.write(f"> {res['text']}\n\n")
            f.write("---\n\n")
    print(f"[+] Master Report Compiled: {MASTER_REPORT}")

def main():
    parser = argparse.ArgumentParser(description="TOTAL REEL HARVESTER")
    parser.add_argument("--browser", help="Browser for cookies (chrome, edge, firefox)")
    parser.add_argument("--model", default="base", help="Whisper model size")
    args = parser.parse_args()

    machine = ReelMachine(model_name=args.model, browser=args.browser)
    
    if not URLS_FILE.exists():
        print(f"[!] Missing {URLS_FILE}")
        return

    with open(URLS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        print("[!] No URLs to process.")
        return

    # PHASE 1: HARDENED DOWNLOAD
    print(f"[*] Starting concurrent extraction of {len(urls)} sources...")
    all_items = []
    # Reduced max_workers to 1 for maximum stealth (one by one)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future_to_url = {executor.submit(machine.download, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            all_items.extend(future.result())

    if not all_items:
        print("[!] No reels captured. Check URLs/Cookies.")
        return

    # PHASE 2: POWER TRANSCRIPTION
    machine.load_model()
    results = []
    for item in tqdm(all_items, desc="Transcribing"):
        res = machine.transcribe(item)
        if res: results.append(res)

    # PHASE 3: MASTER SYNTHESIS
    compile_master_report(results)
    
    print(f"\n[+] HARVEST COMPLETE: {machine.stats['success']} new, {machine.stats['skipped']} skipped, {machine.stats['failed']} failed.")

if __name__ == "__main__":
    main()
