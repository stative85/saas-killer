import os
import json
import re
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
TRANSCRIPT_DIR = Path(r"C:\Users\cleve\OneDrive\Pictures\transcripts_txt")
OUTPUT_DIR = Path(r"C:\Users\cleve\OneDrive\Pictures\intelligence")
INDEX_FILE = OUTPUT_DIR / "archive_index.json"
SIGNAL_FILE = OUTPUT_DIR / "the_signal.txt"
HIVE_REPORT = OUTPUT_DIR / "HIVE_MIND_REPORT.md"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_axioms(text):
    """Pulls high-impact statements using linguistic heuristics."""
    # Split into sentences (simple regex)
    sentences = re.split(r'(?<=[.!?]) +', text)
    axioms = []
    
    # Heuristics for "Signal":
    # 1. Length between 10 and 40 words (not too short, not a ramble)
    # 2. Contains absolute/strong keywords
    strong_keywords = {'must', 'always', 'never', 'truth', 'secret', 'system', 'power', 'control', 'future', 'reality', 'deception'}
    
    for s in sentences:
        words = s.lower().split()
        if 10 < len(words) < 40:
            if any(k in words for k in strong_keywords):
                axioms.append(s.strip())
                
    return list(set(axioms))[:5] # Top 5 per file for the signal

def synthesize():
    print(f"[*] ODIN-SYNTHESIS ENGAGED. Scanning Archive: {TRANSCRIPT_DIR}")
    
    transcripts = list(TRANSCRIPT_DIR.glob("*.txt"))
    if not transcripts:
        print("[!] No transcripts found. Harvest first.")
        return

    index_map = []
    all_signal = []
    
    print(f"[*] Processing {len(transcripts)} sources...")

    for t_path in transcripts:
        with open(t_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            
        lines = content.split("\n")
        word_count = len(content.split())
        
        # 1. Build Index Entry
        entry = {
            "title": t_path.stem,
            "word_count": word_count,
            "line_count": len(lines),
            "density": round(word_count / (len(lines) if len(lines) > 0 else 1), 2),
            "processed_at": datetime.now().isoformat()
        }
        index_map.append(entry)
        
        # 2. Extract Signal (Axioms)
        axioms = extract_axioms(content)
        if axioms:
            all_signal.append(f"--- SOURCE: {t_path.stem} ---")
            all_signal.extend(axioms)
            all_signal.append("")

    # 3. Write Index
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_map, f, indent=2)
    
    # 4. Write Signal File
    with open(SIGNAL_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_signal))
        
    # 5. Build Hive Mind Report
    with open(HIVE_REPORT, "w", encoding="utf-8") as f:
        f.write(f"# 🧠 THE HIVE MIND REPORT - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"## 📊 Archive Statistics\n")
        f.write(f"- **Total Sources:** {len(transcripts)}\n")
        f.write(f"- **Total Word Volume:** {sum(e['word_count'] for e in index_map)}\n")
        f.write(f"- **Highest Density Node:** {max(index_map, key=lambda x: x['density'])['title']}\n\n")
        
        f.write("## ⚡ THE SIGNAL (Distilled Axioms)\n")
        f.write("> Top high-resonance statements extracted from the mass.\n\n")
        f.write("\n".join(all_signal[:50])) # First 50 for the overview
        
    print(f"[+] SYNTHESIS COMPLETE.")
    print(f"[+] Index: {INDEX_FILE}")
    print(f"[+] Signal: {SIGNAL_FILE}")
    print(f"[+] Report: {HIVE_REPORT}")

if __name__ == "__main__":
    synthesize()
