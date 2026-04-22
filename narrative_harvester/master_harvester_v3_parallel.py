import os
import re
import subprocess
import threading
import concurrent.futures
import json
import whisper
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
YTDLP_EXE = r"C:\Users\cleve\OneDrive\Pictures\yt-dlp.exe"
DEFAULT_OUTPUT = r"C:\Users\cleve\OneDrive\Pictures"
WHISPER_MODEL = "base" 
MAX_WORKERS = 4 # Parallel lanes

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

class ParallelHarvester(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MASTER HARVESTER V3 - PARALLEL HYBRID")
        self.geometry("900x700")
        self.configure(bg="#1a1b26")
        self._running = False
        self.model = None
        self._build_ui()

    def _build_ui(self):
        sty = ttk.Style(self)
        sty.theme_use("clam")
        sty.configure("TLabel", background="#1a1b26", foreground="#c0caf5", font=("Segoe UI", 10))
        sty.configure("H.TLabel", background="#1a1b26", foreground="#e0af68", font=("Segoe UI", 18, "bold"))
        sty.configure("TButton", font=("Segoe UI", 10, "bold"))
        sty.configure("TEntry", font=("Segoe UI", 10))

        ttk.Label(self, text="MASTER HARVESTER V3: PARALLEL", style="H.TLabel").pack(pady=(12, 2))
        ttk.Label(self, text="Multi-threaded Hybrid Subtitle + Whisper engine").pack()

        f1 = ttk.Frame(self)
        f1.pack(fill="x", padx=14, pady=6)
        ttk.Label(f1, text="URL:").pack(side="left")
        self.url_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.url_var, width=80).pack(side="left", fill="x", expand=True, padx=(8, 0))

        f2 = ttk.Frame(self)
        f2.pack(fill="x", padx=14, pady=4)
        ttk.Label(f2, text="Output:").pack(side="left")
        self.folder_var = tk.StringVar(value=DEFAULT_OUTPUT)
        ttk.Entry(f2, textvariable=self.folder_var, width=64).pack(side="left", fill="x", expand=True, padx=(8, 8))
        ttk.Button(f2, text="Browse", command=self._browse).pack(side="left")

        f3 = ttk.Frame(self)
        f3.pack(fill="x", padx=14, pady=6)
        self.go_btn = ttk.Button(f3, text="ENGAGE FULL RPM", command=self._start)
        self.go_btn.pack(side="left")
        self.stop_btn = ttk.Button(f3, text="ABORT", command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))

        self.log = tk.Text(self, bg="#16161e", fg="#9aa5ce", font=("Consolas", 9), wrap="word", relief="flat")
        self.log.pack(fill="both", expand=True, padx=14, pady=10)
        self.log.tag_configure("err", foreground="#f7768e")
        self.log.tag_configure("ok", foreground="#9ece6a")
        self.log.tag_configure("info", foreground="#7aa2f7")

    def _browse(self):
        p = filedialog.askdirectory()
        if p: self.folder_var.set(p)

    def _print(self, msg, tag=""):
        self.log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n", tag if tag else ())
        self.log.see("end")

    def _stop(self):
        self._running = False
        self._print("[!!!] ABORTING ALL LANES...", "err")

    def _start(self):
        url = self.url_var.get().strip()
        out = self.folder_var.get().strip()
        if not url or not out: return
        self._running = True
        self.go_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self._master_control, args=(url, out), daemon=True).start()

    def _master_control(self, url, out_root):
        try:
            self._do_harvest(url, out_root)
        except Exception as e:
            self.after(0, self._print, f"CRITICAL FAILURE: {e}", "err")
        finally:
            self.after(0, self.go_btn.configure, {"state": "normal"})
            self.after(0, self.stop_btn.configure, {"state": "disabled"})
            self._running = False

    def process_video(self, entry, work_dir, out_root):
        if not self._running: return None
        title = re.sub(r'[\\/*?:"<>|]', "", entry['title'])
        video_id = entry['id']
        self.after(0, self._print, f"[*] Lane engaged: {title}", "info")
        
        # 1. Try Subtitles
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
            self.after(0, self._print, f"  [+] {video_id}: Subs extracted.", "ok")
            text = clean_vtt(str(vtt_files[0]))
        else:
            # 2. Whisper Fallback
            self.after(0, self._print, f"  [!] {video_id}: No subs. Firing Whisper...", "err")
            audio_path = work_dir / "audio" / f"{video_id}.mp3"
            audio_path.parent.mkdir(exist_ok=True)
            dl_cmd = [
                YTDLP_EXE, "-x", "--audio-format", "mp3",
                "--output", str(audio_path),
                f"https://www.youtube.com/watch?v={video_id}"
            ]
            subprocess.run(dl_cmd, capture_output=True)
            
            # Transcription lock to prevent model collision in memory
            with threading.Lock():
                res = self.model.transcribe(str(audio_path))
                text = res["text"].strip()

        txt_path = Path(out_root) / "transcripts_txt" / f"{title}.txt"
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        self.after(0, self._print, f"  [🏁] {video_id}: Saved.", "ok")
        return txt_path

    def _do_harvest(self, url, out_root):
        work_dir = Path(out_root) / "harvest_temp"
        work_dir.mkdir(parents=True, exist_ok=True)
        
        self.after(0, self._print, f"[*] Initializing Whisper ({WHISPER_MODEL})...", "info")
        if not self.model: self.model = whisper.load_model(WHISPER_MODEL)

        self.after(0, self._print, "[*] Pulling Playlist Manifest...", "info")
        cmd = [YTDLP_EXE, "--get-id", "--get-title", "--flat-playlist", url]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        lines = res.stdout.strip().split("\n")
        
        entries = []
        for i in range(0, len(lines), 2):
            if i+1 < len(lines):
                entries.append({"id": lines[i+1], "title": lines[i]})

        self.after(0, self._print, f"[+] {len(entries)} videos discovered. Spinning up {MAX_WORKERS} lanes.", "ok")

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(self.process_video, entry, work_dir, out_root) for entry in entries]
            for future in concurrent.futures.as_completed(futures):
                if not self._running: break
                
        self.after(0, self._print, "\n[✨] ALL LANES CLEAR. HARVEST COMPLETE.", "ok")

if __name__ == "__main__":
    ParallelHarvester().mainloop()
