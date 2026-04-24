# contradiction_miner.py
import json
import argparse
from pathlib import Path
from collections import defaultdict

def mine_contradictions(chunks_path: Path):
    print(f"[*] ODIN-CRUCIBLE ENGAGED. Mining contradictions in {chunks_path.name}...")
    
    # Bucket chunks by ARC to find opposing views
    arc_buckets = defaultdict(list)
    
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            j = json.loads(line)
            for arc in j.get('arcs', []):
                arc_buckets[arc].append(j)

    report = "# 🏮 NARRATIVE CONTRADICTION REPORT\n\n"
    
    # HEURISTIC: Find 'Future' arc chunks with high contrast keywords
    positive_future = ["innovation", "progress", "new", "better", "solution"]
    negative_future = ["death", "collapse", "crisis", "end", "destruction"]
    
    report += "## ⚡ THE FUTURE PARADOX\n"
    report += "> Innovation through Destruction.\n\n"
    
    future_chunks = arc_buckets.get('future', [])
    
    # Sample some high-resonance contrasts
    for c in future_chunks:
        text = c['text'].lower()
        if any(p in text for p in positive_future) and any(n in text for n in negative_future):
            report += f"### [Resonance: {c['quality_score']}] {c['title']}\n"
            report += f"> {c['text'].strip()}\n\n"

    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    report = mine_contradictions(args.chunks)
    args.out.write_text(report, encoding="utf-8")
    print(f"[✅] Contradictions Mined: {args.out}")

if __name__ == "__main__":
    main()
