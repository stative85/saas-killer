"""
Transcript Harvester - YouTube Playlist Edition
Download YouTube playlist subtitles (.vtt) and convert to clean .txt files.
Single-file Tkinter app for Windows. No ffmpeg needed.
"""

import glob
import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLgpLRpgo3hFxUkt_9jlgAWeF6g9qHRH3p"
YTDLP_EXE = r"C:\Users\cleve\OneDrive\Pictures\yt-dlp.exe"
DEFAULT_OUTPUT = r"C:\Users\cleve\OneDrive\Pictures"


def vtt_to_clean_text(vtt_path: str) -> str:
    with open(vtt_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    out: list[str] = []
    prev = ""

    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("WEBVTT"):
            continue
        if s.startswith("Kind:") or s.startswith("Language:"):
            continue
        if s.startswith("NOTE"):
            continue
        if re.match(r"^\d{2}:\d{2}", s) and "-->" in s:
            continue
        if re.match(r"^\d+$", s):
            continue

        text = re.sub(r"<[^>]+>", "", s).strip()
        if not text or text == prev:
            continue

        out.append(text)
        prev = text

    return "\n".join(out)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("YouTube Transcript Harvester")
        self.geometry("740x580")
        self.configure(bg="#1a1b26")
        self._running = False
        self._proc: subprocess.Popen[str] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        sty = ttk.Style(self)
        sty.theme_use("clam")
        sty.configure("TLabel", background="#1a1b26", foreground="#c0caf5", font=("Segoe UI", 10))
        sty.configure("H.TLabel", background="#1a1b26", foreground="#e0af68", font=("Segoe UI", 18, "bold"))
        sty.configure("TButton", font=("Segoe UI", 10, "bold"))
        sty.configure("TCheckbutton", background="#1a1b26", foreground="#c0caf5", font=("Segoe UI", 10))
        sty.configure("TEntry", font=("Segoe UI", 10))

        ttk.Label(self, text="YouTube Playlist Harvester", style="H.TLabel").pack(pady=(12, 2))
        ttk.Label(self, text="YouTube playlist subtitles → clean text files").pack()

        f1 = ttk.Frame(self)
        f1.pack(fill="x", padx=14, pady=6)
        ttk.Label(f1, text="Playlist URL:").pack(side="left")
        self.url_var = tk.StringVar(value=PLAYLIST_URL)
        ttk.Entry(f1, textvariable=self.url_var, width=80).pack(side="left", fill="x", expand=True, padx=(8, 0))

        f2 = ttk.Frame(self)
        f2.pack(fill="x", padx=14, pady=4)
        ttk.Label(f2, text="Output folder:").pack(side="left")
        self.folder_var = tk.StringVar(value=DEFAULT_OUTPUT)
        ttk.Entry(f2, textvariable=self.folder_var, width=64).pack(side="left", fill="x", expand=True, padx=(8, 8))
        ttk.Button(f2, text="Browse", command=self._browse).pack(side="left")

        f3 = ttk.Frame(self)
        f3.pack(fill="x", padx=14, pady=4)
        self.autosub_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f3, text="Include auto-generated subs", variable=self.autosub_var).pack(side="left")
        self.merge_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f3, text="Merge all into one .txt", variable=self.merge_var).pack(side="left", padx=(20, 0))

        f4 = ttk.Frame(self)
        f4.pack(fill="x", padx=14, pady=6)
        self.go_btn = ttk.Button(f4, text="Harvest", command=self._start)
        self.go_btn.pack(side="left")
        self.stop_btn = ttk.Button(f4, text="Stop", command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))

        ttk.Label(self, text="Log:").pack(anchor="w", padx=14)
        lf = ttk.Frame(self)
        lf.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.log = tk.Text(
            lf,
            bg="#16161e",
            fg="#9aa5ce",
            font=("Consolas", 9),
            wrap="word",
            state="disabled",
            relief="flat",
        )
        sb = ttk.Scrollbar(lf, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.log.tag_configure("err", foreground="#f7768e")
        self.log.tag_configure("ok", foreground="#9ece6a")
        self.log.tag_configure("info", foreground="#7aa2f7")

    def _browse(self) -> None:
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.folder_var.set(path)

    def _print(self, msg: str, tag: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n", tag if tag else ())
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_running(self, value: bool) -> None:
        self._running = value
        self.go_btn.configure(state="disabled" if value else "normal")
        self.stop_btn.configure(state="normal" if value else "disabled")

    def _stop(self) -> None:
        self._running = False
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
        self._print("Stopping...", "err")

    def _start(self) -> None:
        url = self.url_var.get().strip()
        out = self.folder_var.get().strip()

        if not url:
            messagebox.showwarning("URL required", "Paste a YouTube playlist URL.")
            return
        if not out:
            messagebox.showwarning("Folder required", "Pick an output folder.")
            return
        if not os.path.isfile(YTDLP_EXE):
            messagebox.showerror("yt-dlp not found", f"Not found at:\n{YTDLP_EXE}")
            return

        self._set_running(True)
        threading.Thread(target=self._run, args=(url, out), daemon=True).start()

    def _run(self, url: str, out_root: str) -> None:
        try:
            self._do_run(url, out_root)
        except Exception as exc:
            self.after(0, self._print, f"Fatal: {exc}", "err")
        finally:
            self.after(0, self._set_running, False)

    def _do_run(self, url: str, out_root: str) -> None:
        vtt_dir = os.path.join(out_root, "transcripts_vtt")
        txt_dir = os.path.join(out_root, "transcripts_txt")
        os.makedirs(vtt_dir, exist_ok=True)
        os.makedirs(txt_dir, exist_ok=True)

        self.after(0, self._print, f"VTT folder: {vtt_dir}", "info")
        self.after(0, self._print, f"TXT folder: {txt_dir}", "info")
        self.after(0, self._print, "Downloading subtitles...\n", "info")

        cmd = [
            YTDLP_EXE,
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", "en.*",
            "--sub-format", "vtt",
            "--convert-subs", "vtt",
            "--output", os.path.join(vtt_dir, "%(playlist_index)03d_%(title)s.%(ext)s"),
            "--no-overwrites",
            "--ignore-errors",
            "--encoding", "utf-8",
            url,
        ]

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=0x08000000,
            )
            assert self._proc.stdout is not None
            for line in self._proc.stdout:
                if not self._running:
                    self._proc.terminate()
                    self.after(0, self._print, "Stopped.", "err")
                    return
                line = line.rstrip()
                if line:
                    self.after(0, self._print, line)

            self._proc.wait()
            rc = self._proc.returncode
            self._proc = None
            if rc != 0 and self._running:
                self.after(0, self._print, f"yt-dlp exited with code {rc}", "err")
        except Exception as exc:
            self.after(0, self._print, f"yt-dlp error: {exc}", "err")
            return

        if not self._running:
            return

        vtts = sorted(glob.glob(os.path.join(vtt_dir, "**", "*.vtt"), recursive=True))
        if not vtts:
            self.after(0, self._print, "\nNo .vtt files downloaded. Playlist may lack English subs.", "err")
            return

        self.after(0, self._print, f"\nFound {len(vtts)} subtitle files. Converting...\n", "info")

        txt_paths: list[str] = []
        for vtt in vtts:
            if not self._running:
                return

            base = os.path.splitext(os.path.basename(vtt))[0]
            base = re.sub(r"\.[a-zA-Z]{2}(-[a-zA-Z]{2,})?$", "", base)
            txt_path = os.path.join(txt_dir, base + ".txt")

            try:
                clean = vtt_to_clean_text(vtt)
                if not clean.strip():
                    self.after(0, self._print, f"  SKIP (empty): {os.path.basename(vtt)}", "err")
                    continue

                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(clean)

                txt_paths.append(txt_path)
                self.after(0, self._print, f"  OK: {base}.txt", "ok")
            except Exception as exc:
                self.after(0, self._print, f"  ERR: {os.path.basename(vtt)} - {exc}", "err")

        if not txt_paths:
            self.after(0, self._print, "\nNo transcripts converted.", "err")
            return

        self.after(0, self._print, f"\nConverted {len(txt_paths)} files.", "ok")

        if self.merge_var.get() and len(txt_paths) > 1:
            merge_path = os.path.join(out_root, "merged_transcript.txt")
            try:
                with open(merge_path, "w", encoding="utf-8") as out:
                    for index, tp in enumerate(txt_paths, start=1):
                        name = os.path.splitext(os.path.basename(tp))[0]
                        out.write(f"{'=' * 60}\n")
                        out.write(f"  {index}. {name}\n")
                        out.write(f"{'=' * 60}\n\n")
                        with open(tp, "r", encoding="utf-8") as inp:
                            out.write(inp.read())
                        out.write("\n\n")
                self.after(0, self._print, f"Merged: {merge_path}", "ok")
            except Exception as exc:
                self.after(0, self._print, f"Merge error: {exc}", "err")

        self.after(0, self._print, f"\nDone!\n  VTT: {vtt_dir}\n  TXT: {txt_dir}", "ok")


if __name__ == "__main__":
    App().mainloop()
