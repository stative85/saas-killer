import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Dict

def strip_artifacts(text: str) -> Tuple[str, int]:
    # 1. Strip Infowars style timestamps: [01:32:38.586 --> 01:32:40.511]
    text, count1 = re.subn(r"\[\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}\]", "", text)
    # 2. Strip standard [Music], (Laughter)
    text, count2 = re.subn(r"\[.*?\]|\(.*?\)", "", text)
    return text.strip(), count1 + count2

def strip_invisible(text: str) -> Tuple[str, int]:
    count = len(re.findall(r"[\u200b-\u200d\ufeff]", text))
    repaired = re.sub(r"[\u200b-\u200d\ufeff]", "", text)
    return repaired, count

def collapse_duplicates(text: str) -> Tuple[str, int]:
    lines = text.split("\n")
    out = []
    fixes = 0
    prev = None
    for line in lines:
        curr = line.strip()
        if curr == prev and curr != "":
            fixes += 1
            continue
        out.append(line)
        prev = curr
    return "\n".join(out), fixes

def repair_overlap_scars(text: str, min_words: int = 3) -> Tuple[str, int]:
    lines = text.split("\n")
    if not lines: return text, 0
    repaired = [lines[0]]
    fixes = 0
    for i in range(1, len(lines)):
        prev = repaired[-1].strip().split()
        curr = lines[i].strip().split()
        found_overlap = False
        for length in range(min(len(prev), len(curr)), min_words - 1, -1):
            if prev[-length:] == curr[:length]:
                merged = " ".join(prev) + " " + " ".join(curr[length:])
                repaired[-1] = merged
                fixes += 1
                found_overlap = True
                break
        if not found_overlap:
            repaired.append(lines[i])
    return "\n".join(repaired), fixes

def repair_pipeline(text: str, aggression: str) -> Tuple[str, Dict[str, int]]:
    stats = {}
    text, stats['artifacts'] = strip_artifacts(text)
    text, stats['invisible'] = strip_invisible(text)
    text, stats['duplicates'] = collapse_duplicates(text)
    
    if aggression in ['medium', 'high']:
        text, stats['overlaps'] = repair_overlap_scars(text)
    
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, stats

def main():
    parser = argparse.ArgumentParser(description="HARDENED REPAIR FORGE")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--aggression", choices=['low', 'medium', 'high'], default='medium')
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = list(args.input_dir.glob("*.txt"))
    print(f"[*] Hammering {len(files)} files at {args.aggression.upper()} aggression...")

    for f_path in files:
        with open(f_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        repaired, _ = repair_pipeline(raw, args.aggression)
        out_path = args.output_dir / f"{f_path.stem}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(repaired)
    print(f"[✅] Hardened Forge Complete.")

if __name__ == "__main__":
    main()
