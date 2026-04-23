# search_shell.py
import argparse, json, math, re
from pathlib import Path
from collections import Counter

def tokenize(t: str):
    return re.findall(r"[a-zA-Z0-9']+", t.lower())

class BM25:
    def __init__(self, docs):
        self.docs = docs
        self.N = len(docs)
        self.avgdl = sum(len(d["tokens"]) for d in docs) / max(self.N, 1)
        self.df = Counter()
        for d in docs:
            for tok in set(d["tokens"]):
                self.df[tok] += 1
        self.idf = {
            t: math.log(1 + (self.N - df + 0.5) / (df + 0.5))
            for t, df in self.df.items()
        }
        self.k1, self.b = 1.5, 0.75

    def score(self, query_tokens, d):
        score = 0.0
        tf = Counter(d["tokens"])
        dl = len(d["tokens"])
        for t in query_tokens:
            if t not in tf: continue
            idf = self.idf.get(t, 0.0)
            num = tf[t] * (self.k1 + 1)
            den = tf[t] + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            score += idf * (num / den)
        # slight boosts
        title_hits = sum(1 for t in query_tokens if t in d["title_lc"])
        score *= (1.0 + 0.05 * title_hits)
        score *= (0.8 + 0.2 * d["quality"])  # prefer better chunks
        return score

def load_chunks(p: Path):
    docs = []
    if not p.exists():
        print(f"Error: {p} not found")
        return []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                j = json.loads(line)
                toks = tokenize(j["text"])
                docs.append({
                    "chunk_id": j["chunk_id"],
                    "doc_id": j["doc_id"],
                    "title": j["title"],
                    "title_lc": j["title"].lower(),
                    "text": j["text"],
                    "tokens": toks,
                    "quality": float(j.get("quality_score", 0.5))
                })
            except: continue
    return docs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--chunks", default=r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks.jsonl")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--min-quality", type=float, default=0.0)
    args = ap.parse_args()

    docs = load_chunks(Path(args.chunks))
    if not docs: return
    bm25 = BM25(docs)
    q = tokenize(args.query)

    scored = []
    for d in docs:
        if d["quality"] < args.min_quality: continue
        s = bm25.score(q, d)
        if s > 0:
            scored.append((s, d))
    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\n--- SEARCH RESULTS FOR: '{args.query}' ---")
    for i, (s, d) in enumerate(scored[:args.top], 1):
        print(f"\n[{i}] score={s:.2f} | {d['doc_id']} | {d['chunk_id']} | {d['title']}")
        print(d["text"][:600], "...")

if __name__ == "__main__":
    main()
