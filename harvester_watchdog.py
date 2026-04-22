import os
import time
import json
import whisper
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = Path("narrative_harvester")
AUDIO_DIR = BASE_DIR / "audio"
TRANSCRIPT_DIR = BASE_DIR / "transcripts"
MASTER_REPORT = BASE_DIR / "MASTER_HARVEST_REPORT.md"
WHISPER_MODEL = "base"

for d in [AUDIO_DIR, TRANSCRIPT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def update_master_report(data):
    meta = data['metadata']
    with open(MASTER_REPORT, "a", encoding="utf-8") as f:
        f.write(f"## 🆕 HARVESTED: {meta['filename']}\n")
        f.write(f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("### 📝 Transcript\n")
        f.write(f"> {data['text']}\n\n")
        f.write("---\n\n")

def transcribe_file(model, file_path):
    print(f"\n[!] TARGET SPOTTED: {file_path.name}")
    try:
        # Check if already transcribed
        json_path = TRANSCRIPT_DIR / (file_path.stem + ".json")
        if json_path.exists():
            print(f"[-] Skipping (Already harvested)")
            return

        print(f"[*] Hammering down on transcription...")
        result = model.transcribe(str(file_path))
        
        data = {
            "metadata": {"filename": file_path.name},
            "text": result["text"].strip(),
            "harvest_date": datetime.now().isoformat()
        }
        
        # Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # Save TXT
        with open(TRANSCRIPT_DIR / (file_path.stem + ".txt"), "w", encoding="utf-8") as f:
            f.write(data["text"])
            
        # Update Master
        update_master_report(data)
        
        print(f"[+] HARVEST SUCCESSFUL: {file_path.stem}.txt")
        print(f"[+] Master Report Updated.")
        
    except Exception as e:
        print(f"[!] Transcription failed: {e}")

def main():
    print(f"[*] Initializing {WHISPER_MODEL.upper()} Whisper Model...")
    model = whisper.load_model(WHISPER_MODEL)
    
    print(f"\n[🥷] NINJA WATCHDOG ACTIVE.")
    print(f"[🥷] Watching: {AUDIO_DIR}")
    print(f"[🥷] DROP YOUR FILES IN AND WATCH THE MAGIC.")
    print("-" * 50)

    known_files = set(os.listdir(AUDIO_DIR))
    
    try:
        while True:
            current_files = set(os.listdir(AUDIO_DIR))
            new_files = current_files - known_files
            
            for f in new_files:
                file_path = AUDIO_DIR / f
                # Wait a second to ensure file is fully copied
                time.sleep(1)
                transcribe_file(model, file_path)
                
            known_files = current_files
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[!] Ninja retiring to the shadows.")

if __name__ == "__main__":
    main()
