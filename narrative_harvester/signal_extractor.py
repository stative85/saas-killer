# signal_extractor.py
import json, re, argparse
from pathlib import Path
from collections import Counter

def tokenize(t): return re.findall(r"[a-zA-Z0-9']+", t.lower())

def is_punchy(t):
    # quick heuristics for “hits”
    return (
        40 < len(t) < 220 and
        any(w in t.lower() for w in ["truth","system","control","future","death","freedom","memory","ai"]) and
        (t.count(",") + t.count(";") + t.count(":") <= 2)
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks.jsonl")
    ap.add_argument("--out-dir", default=r"C:\Users\cleve\OneDrive\Pictures\corpus_run\exports")
    args = ap.parse_args()

    chunks_p = Path(args.chunks)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    quotes = []
    term_df = Counter()
    term_tf = Counter()

    if not chunks_p.exists():
        print(f"Error: {chunks_p} not found")
        return

    with chunks_p.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                j = json.loads(line)
                text = j["text"]
                toks = tokenize(text)
                tok_set = set(toks)
                for t in tok_set: term_df[t] += 1
                for t in toks: term_tf[t] += 1
                if is_punchy(text):
                    quotes.append((j["quality_score"], j["doc_id"], j["title"], text.strip()))
            except: continue

    # top quotes
    quotes.sort(key=lambda x: x[0], reverse=True)
    with (out / "top_quotes.txt").open("w", encoding="utf-8") as w:
        for q, doc, title, txt in quotes[:200]:
            w.write(f"[{q:.2f}] [{doc}] {title}\n{txt}\n\n")

    # obsession terms (spread > count)
    obs = []
    for t, df in term_df.items():
        if df >= 10 and len(t) > 3:
            obs.append((df, term_tf[t], t))
    obs.sort(key=lambda x: x[0], reverse=True)

    with (out / "obsession_terms.txt").open("w", encoding="utf-8") as w:
        for df, tf, t in obs[:200]:
            w.write(f"{t}\tDF={df}\tTF={tf}\n")

    print("Wrote exports to:", out)

if __name__ == "__main__":
    main()
