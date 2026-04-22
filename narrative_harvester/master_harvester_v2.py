import os
import re
import subprocess
import threading
import glob
import json
import whisper
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

# --- CONFIGURATION ---
YTDLP_EXE = r"C:\Users\cleve\OneDrive\Pictures\yt-dlp.exe"
DEFAULT_OUTPUT = r"C:\Users\cleve\OneDrive\Pictures"
WHISPER_MODEL = "base" # Options: tiny, base, small, medium, large

def clean_vtt(vtt_path):
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

class MasterHarvester(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MASTER HARVESTER V2 - HYBRID ENGINE")
        self.geometry("800x650")
        self.configure(bg="#1a1b26")
        self._running = False
        self._proc = None
        self.model = None
        self._build_ui()

    def _build_ui(self):
        sty = ttk.Style(self)
        sty.theme_use("clam")
        sty.configure("TLabel", background="#1a1b26", foreground="#c0caf5", font=("Segoe UI", 10))
        sty.configure("H.TLabel", background="#1a1b26", foreground="#e0af68", font=("Segoe UI", 18, "bold"))
        sty.configure("TButton", font=("Segoe UI", 10, "bold"))
        sty.configure("TCheckbutton", background="#1a1b26", foreground="#c0caf5", font=("Segoe UI", 10))
        sty.configure("TEntry", font=("Segoe UI", 10))

        ttk.Label(self, text="MASTER HARVESTER V2", style="H.TLabel").pack(pady=(12, 2))
        ttk.Label(self, text="Hybrid Subtitle + Whisper fallback engine").pack()

        # URL
        f1 = ttk.Frame(self)
        f1.pack(fill="x", padx=14, pady=6)
        ttk.Label(f1, text="URL (Video or Playlist):").pack(side="left")
        self.url_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.url_var, width=80).pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Output folder
        f2 = ttk.Frame(self)
        f2.pack(fill="x", padx=14, pady=4)
        ttk.Label(f2, text="Output folder:").pack(side="left")
        self.folder_var = tk.StringVar(value=DEFAULT_OUTPUT)
        ttk.Entry(f2, textvariable=self.folder_var, width=64).pack(side="left", fill="x", expand=True, padx=(8, 8))
        ttk.Button(f2, text="Browse", command=self._browse).pack(side="left")

        # Buttons
        f4 = ttk.Frame(self)
        f4.pack(fill="x", padx=14, pady=6)
        self.go_btn = ttk.Button(f4, text="Engage Harvest", command=self._start)
        self.go_btn.pack(side="left")
        self.stop_btn = ttk.Button(f4, text="Kill Process", command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))

        # Log
        self.log = tk.Text(self, bg="#16161e", fg="#9aa5ce", font=("Consolas", 9), wrap="word", relief="flat")
        self.log.pack(fill="both", expand=True, padx=14, pady=10)
        self.log.tag_configure("err", foreground="#f7768e")
        self.log.tag_configure("ok", foreground="#9ece6a")
        self.log.tag_configure("info", foreground="#7aa2f7")

    def _browse(self):
        p = filedialog.askdirectory(title="Choose output folder")
        if p: self.folder_var.set(p)

    def _print(self, msg, tag=""):
        self.log.insert("end", msg + "\n", tag if tag else ())
        self.log.see("end")

    def _stop(self):
        self._running = False
        if self._proc: self._proc.terminate()
        self._print("[!] Stopping...", "err")

    def _start(self):
        url = self.url_var.get().strip()
        out = self.folder_var.get().strip()
        if not url or not out: return
        self._running = True
        self.go_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self._run, args=(url, out), daemon=True).start()

    def _run(self, url, out_root):
        try:
            self._do_run(url, out_root)
        except Exception as e:
            self.after(0, self._print, f"Fatal: {e}", "err")
        finally:
            self.after(0, self.go_btn.configure, {"state": "normal"})
            self.after(0, self.stop_btn.configure, {"state": "disabled"})
            self._running = False

    def _do_run(self, url, out_root):
        work_dir = Path(out_root) / "harvest_temp"
        work_dir.mkdir(parents=True, exist_ok=True)
        self.after(0, self._print, f"[*] Initializing Whisper ({WHISPER_MODEL})...", "info")
        if not self.model: self.model = whisper.load_model(WHISPER_MODEL)

        self.after(0, self._print, "[*] Scanning for subtitles/audio...", "info")
        # Step 1: Attempt to get IDs and metadata
        cmd = [YTDLP_EXE, "--get-id", "--get-title", "--flat-playlist", url]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        lines = res.stdout.strip().split("\n")
        
        # Simple parser for flat playlist output
        entries = []
        for i in range(0, len(lines), 2):
            if i+1 < len(lines):
                entries.append({"id": lines[i+1], "title": lines[i]})

        self.after(0, self._print, f"[+] Found {len(entries)} targets.", "ok")

        for entry in entries:
            if not self._running: break
            title = re.sub(r'[\\/*?:"<>|]', "", entry['title'])
            self.after(0, self._print, f"\n[#] Processing: {title}", "info")
            
            # Step 2: Try to grab existing subs first
            vtt_dir = work_dir / "vtt"
            vtt_dir.mkdir(exist_ok=True)
            sub_cmd = [
                YTDLP_EXE, "--skip-download", "--write-subs", "--write-auto-subs",
                "--sub-lang", "en.*", "--sub-format", "vtt",
                "--output", str(vtt_dir / f"{title}.%(ext)s"),
                f"https://www.youtube.com/watch?v={entry['id']}"
            ]
            subprocess.run(sub_cmd, capture_output=True)
            
            vtt_files = list(vtt_dir.glob(f"{title}.*.vtt"))
            if vtt_files:
                self.after(0, self._print, f"  [+] Subs found. Cleaning...", "ok")
                text = clean_vtt(vtt_files[0])
            else:
                self.after(0, self._print, f"  [!] No subs. Firing Whisper Hammer...", "err")
                audio_dir = work_dir / "audio"
                audio_dir.mkdir(exist_ok=True)
                audio_path = audio_dir / f"{title}.mp3"
                
                # Download audio only
                dl_cmd = [
                    YTDLP_EXE, "-x", "--audio-format", "mp3",
                    "--output", str(audio_path),
                    f"https://www.youtube.com/watch?v={entry['id']}"
                ]
                subprocess.run(dl_cmd, capture_output=True)
                
                # Whisper Transcribe
                res = self.model.transcribe(str(audio_path))
                text = res["text"].strip()
            
            # Save individual TXT
            txt_dir = Path(out_root) / "transcripts_txt"
            txt_dir.mkdir(parents=True, exist_ok=True)
            with open(txt_dir / f"{title}.txt", "w", encoding="utf-8") as f:
                f.write(text)
            
            self.after(0, self._print, f"  [+] Transcript saved: {title}.txt", "ok")

        self.after(0, self._print, "\n[🏁] MASTER HARVEST COMPLETE.", "ok")

if __name__ == "__main__":
    MasterHarvester().mainloop()
