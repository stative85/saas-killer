import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Dict

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
    """Fixes 'the future is prediction\nprediction not treatment' -> 'the future is prediction not treatment'"""
    lines = text.split("\n")
    if not lines: return text, 0
    
    repaired = [lines[0]]
    fixes = 0
    
    for i in range(1, len(lines)):
        prev = repaired[-1].strip().split()
        curr = lines[i].strip().split()
        
        found_overlap = False
        # Look for suffix/prefix overlap
        for length in range(min(len(prev), len(curr)), min_words - 1, -1):
            if prev[-length:] == curr[:length]:
                # Merge: take prev line + unique part of curr line
                merged = " ".join(prev) + " " + " ".join(curr[length:])
                repaired[-1] = merged
                fixes += 1
                found_overlap = True
                break
        
        if not found_overlap:
            repaired.append(lines[i])
            
    return "\n".join(repaired), fixes

def repair_stutters(text: str) -> Tuple[str, int]:
    """Fixes 'I I I think we we should' -> 'I think we should'"""
    # 3+ repetitions
    repaired, count3 = re.subn(r"\b(\w+)(?:\s+\1){2,}\b", r"\1", text, flags=re.IGNORECASE)
    # 2 repetitions (conservative)
    repaired, count2 = re.subn(r"\b(\w{3,})\s+\1\b", r"\1", repaired, flags=re.IGNORECASE)
    return repaired, count3 + count2

def purge_artifacts(text: str) -> Tuple[str, int]:
    """Removes [Music], (Laughter), etc."""
    pattern = r"\[.*?\]|\(.*?\)"
    count = len(re.findall(pattern, text))
    repaired = re.sub(pattern, "", text)
    return repaired, count

def join_broken_lines(text: str) -> Tuple[str, int]:
    """Joins lines that don't end in punctuation with the next line if it starts lowercase."""
    lines = text.split("\n")
    if not lines: return text, 0
    
    repaired = [lines[0]]
    fixes = 0
    
    for i in range(1, len(lines)):
        prev = repaired[-1].strip()
        curr = lines[i].strip()
        
        if not prev or not curr:
            repaired.append(lines[i])
            continue
            
        # If prev doesn't end in [.!?] and curr starts lowercase
        if not re.search(r"[.!?]$", prev) and curr[0].islower():
            repaired[-1] = prev + " " + curr
            fixes += 1
        else:
            repaired.append(lines[i])
            
    return "\n".join(repaired), fixes

def repair_pipeline(text: str, aggression: str) -> Tuple[str, Dict[str, int]]:
    stats = {}
    
    text, stats['invisible'] = strip_invisible(text)
    text, stats['duplicates'] = collapse_duplicates(text)
    
    if aggression in ['medium', 'high']:
        text, stats['overlaps'] = repair_overlap_scars(text)
        text, stats['stutters'] = repair_stutters(text)
        text, stats['broken_joins'] = join_broken_lines(text)
        
    if aggression == 'high':
        text, stats['artifacts'] = purge_artifacts(text)
        
    # Final normalization
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    
    return text, stats

def main():
    parser = argparse.ArgumentParser(description="REPAIR FORGE")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--aggression", choices=['low', 'medium', 'high'], default='medium')
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = list(args.input_dir.glob("*.txt"))
    
    overall_stats = {'files': 0, 'fixes': 0}

    print(f"[*] Hammering {len(files)} files at {args.aggression.upper()} aggression...")

    for f_path in files:
        with open(f_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
            
        repaired, file_stats = repair_pipeline(raw, args.aggression)
        
        out_path = args.output_dir / f"{f_path.stem}.repaired.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(repaired)
            
        overall_stats['files'] += 1
        overall_stats['fixes'] += sum(file_stats.values())
        
    print(f"[+] Forge Complete. {overall_stats['files']} files repaired, {overall_stats['fixes']} scars removed.")

if __name__ == "__main__":
    main()
