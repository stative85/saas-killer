# cross_source_engine.py
import json
import argparse
from pathlib import Path
from collections import Counter
from arc_classifier import assign_arcs

def load_chunks(jsonl_path: Path):
    data = []
    if not jsonl_path.exists():
        print(f"[!] Path not found: {jsonl_path}")
        return data
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def generate_density_map(chunks):
    counts = Counter()
    for c in chunks:
        text = c.get('text', '')
        arcs = assign_arcs(text)
        for a in arcs:
            counts[a] += 1
    total = sum(counts.values()) or 1
    return counts, {k: round((v / total) * 100, 2) for k, v in counts.items()}

def analyze_cross_source(source_a: Path, source_b: Path, out_path: Path):
    print(f"[*] Analyzing Source A: {source_a.parent.name}")
    chunks_a = load_chunks(source_a)
    counts_a, density_a = generate_density_map(chunks_a)

    print(f"[*] Analyzing Source B: {source_b.parent.name}")
    chunks_b = load_chunks(source_b)
    counts_b, density_b = generate_density_map(chunks_b)

    report = f"# 🌐 MULTI-CORPUS INTELLIGENCE REPORT\n\n"
    
    report += f"## 📊 Source A [{source_a.parent.name}]\n"
    report += f"- Chunks Analyzed: {len(chunks_a)}\n"
    for k, v in sorted(density_a.items(), key=lambda x: x[1], reverse=True):
        report += f"- **{k.upper()}**: {v}% ({counts_a[k]} hits)\n"

    report += f"\n## 📊 Source B [{source_b.parent.name}]\n"
    report += f"- Chunks Analyzed: {len(chunks_b)}\n"
    for k, v in sorted(density_b.items(), key=lambda x: x[1], reverse=True):
        report += f"- **{k.upper()}**: {v}% ({counts_b[k]} hits)\n"

    # CALCULATE DELTA (Divergence Points)
    report += f"\n## ⚔️ NARRATIVE DIVERGENCE (A vs B)\n"
    report += "> Positive Delta means Source A favors the arc. Negative Delta means Source B favors it.\n\n"
    
    all_arcs = set(density_a.keys()).union(set(density_b.keys()))
    deltas = []
    for arc in all_arcs:
        da = density_a.get(arc, 0.0)
        db = density_b.get(arc, 0.0)
        diff = da - db
        deltas.append((arc, diff, da, db))
        
    deltas.sort(key=lambda x: abs(x[1]), reverse=True)
    
    for arc, diff, da, db in deltas:
        direction = "Favors Source A" if diff > 0 else "Favors Source B"
        report += f"- **{arc.upper()}**: {diff:.2f}% | {direction} (A: {da}%, B: {db}%)\n"

    out_path.write_text(report, encoding="utf-8")
    print(f"\n[✅] Contrast Complete. Multi-Corpus Report Generated: {out_path.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-a", type=Path, default=Path(r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks.jsonl"))
    parser.add_argument("--source-b", type=Path, default=Path(r"narrative-forge\outputs\twitch_corpus\index\chunks.jsonl"))
    parser.add_argument("--out", type=Path, default=Path(r"narrative-forge\outputs\MULTI_CORPUS_REPORT.md"))
    args = parser.parse_args()
    
    analyze_cross_source(args.source_a, args.source_b, args.out)
