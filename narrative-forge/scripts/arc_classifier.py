# arc_classifier.py
import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict

# --- ARC DEFINITIONS ---
ARC_RULES = {
    "control": ["system", "control", "power", "authority", "structure", "government", "rule"],
    "science": ["science", "data", "research", "evidence", "method", "biological", "physics"],
    "future": ["future", "ai", "prediction", "evolution", "change", "next", "tomorrow"],
    "truth": ["truth", "real", "illusion", "deception", "fact", "lie", "certainty"],
    "human": ["human", "mind", "body", "self", "identity", "consciousness", "person"],
    "threat": ["danger", "collapse", "death", "risk", "failure", "crisis", "end"]
}

def assign_arcs(text):
    arcs = []
    t = text.lower()
    for arc, keywords in ARC_RULES.items():
        if any(w in t for w in keywords):
            arcs.append(arc)
    return list(set(arcs))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks.jsonl")
    ap.add_argument("--out-dir", default=r"C:\Users\cleve\OneDrive\Pictures\corpus_run\exports\arcs")
    args = ap.parse_args()

    chunks_p = Path(args.chunks)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    index_dir = chunks_p.parent
    output_chunks_p = index_dir / "chunks_with_arcs.jsonl"

    arc_counts = Counter()
    intersections = []
    arc_packs = defaultdict(list)
    
    print(f"[*] Analyzing Arcs in {chunks_p}...")

    with chunks_p.open("r", encoding="utf-8") as f, output_chunks_p.open("w", encoding="utf-8") as out_f:
        for line in f:
            j = json.loads(line)
            text = j["text"]
            found_arcs = assign_arcs(text)
            
            j["arcs"] = found_arcs
            out_f.write(json.dumps(j) + "\n")
            
            for arc in found_arcs:
                arc_counts[arc] += 1
                arc_packs[arc].append((j["quality_score"], j["title"], text))
            
            # Intersection Scoring: quality * number of arcs hit
            if len(found_arcs) >= 2:
                score = j["quality_score"] * len(found_arcs)
                intersections.append((score, found_arcs, j["title"], text))

    # Write Weapon Packs (Top 50 per arc)
    for arc, quotes in arc_packs.items():
        quotes.sort(key=lambda x: x[0], reverse=True)
        pack_p = out_dir / f"{arc}.txt"
        with pack_p.open("w", encoding="utf-8") as w:
            w.write(f"--- {arc.upper()} WEAPON PACK ---\n\n")
            for q_score, title, txt in quotes[:50]:
                w.write(f"[{q_score:.2f}] {title}\n{txt}\n\n")

    # Write Intersections (The high-resonance gold)
    intersections.sort(key=lambda x: x[0], reverse=True)
    with (out_dir / "intersections.txt").open("w", encoding="utf-8") as w:
        w.write("--- HIGH RESONANCE ARC INTERSECTIONS ---\n")
        w.write("Chunks hitting multiple narrative pressure zones.\n\n")
        for score, arcs, title, txt in intersections[:100]:
            w.write(f"[Score: {score:.2f}] Arcs: {', '.join(arcs)} | {title}\n{txt}\n\n")

    # Write Density Map
    with (out_dir / "arc_density_map.json").open("w", encoding="utf-8") as w:
        json.dump(dict(arc_counts), w, indent=2)

    print(f"[+] Arc Classification Complete.")
    print(f"[+] Updated Index: {output_chunks_p}")
    print(f"[+] Density Map: {out_dir}/arc_density_map.json")
    print(f"[+] Weapon Packs: {out_dir}/*.txt")

if __name__ == "__main__":
    main()
