# hook_ranker.py
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any

def tokenize(t: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9']+", t.lower())

def score_hook(text: str, source: str, novelty_base: float = 0.8) -> Dict[str, Any]:
    t = text.strip()
    words = tokenize(t)
    word_count = len(words)
    char_count = len(t)
    
    # Heuristics
    # 1. Brevity (Target: 10-25 words)
    if word_count < 5: brevity = 0.4
    elif 10 <= word_count <= 25: brevity = 1.0
    else: brevity = max(0.0, 1.0 - (word_count - 25) * 0.05)
    
    # 2. Punch Density (strong verbs/nouns, low stop words)
    strong_terms = {"truth", "system", "control", "future", "death", "freedom", "memory", "ai", "power", "reality", "secret"}
    hits = sum(1 for w in words if w in strong_terms)
    punch = min(1.0, hits / 2.0) if hits > 0 else 0.3
    
    # 3. Curiosity Gap
    curiosity = 0.8 if any(w in words for w in ["how", "why", "secret", "hidden", "unexpected"]) else 0.5
    
    # 4. Emotional Charge / Tension
    emotion = 0.8 if any(w in words for w in ["threat", "danger", "love", "fear", "lie", "kill"]) else 0.5
    tension = 0.9 if any(w in words for w in ["but", "instead", "against", "collision"]) else 0.5
    
    # 5. Clarity
    clarity = 1.0 if t.count(",") <= 1 and t.count(".") <= 1 else 0.7
    
    total = (0.2 * brevity + 0.2 * punch + 0.15 * curiosity + 0.15 * emotion + 0.15 * tension + 0.1 * novelty_base + 0.05 * clarity)
    
    return {
        "text": t,
        "score_total": round(total, 2),
        "metrics": {
            "brevity": round(brevity, 2),
            "punch": round(punch, 2),
            "curiosity": round(curiosity, 2),
            "emotion": round(emotion, 2),
            "tension": round(tension, 2),
            "novelty": round(novelty_base, 2),
            "clarity": round(clarity, 2)
        },
        "source": source
    }

def extract_candidates(script_path: Path, quotes_path: Path, chunks_path: Path) -> List[Dict[str, str]]:
    candidates = []
    
    # 1. From Script Opening
    if script_path.exists():
        text = script_path.read_text(encoding="utf-8")
        # Find first quoted section
        match = re.search(r"^>\s*(.+)$", text, re.MULTILINE)
        if match:
            candidates.append({"text": match.group(1).strip(), "source": "script_opening"})

    # 2. From Top Quotes
    if quotes_path.exists():
        text = quotes_path.read_text(encoding="utf-8")
        # Quotes are formatted as [score] [id] title \n text \n\n
        quote_blocks = re.findall(r"\]\s+.+\n(.+)\n", text)
        for q in quote_blocks[:50]:
            if len(q.strip()) > 30:
                candidates.append({"text": q.strip(), "source": "top_quotes"})

    # 3. From Chunks (Short high-pressure fragments)
    if chunks_path.exists():
        with open(chunks_path, 'r', encoding='utf-8') as f:
            for line in f:
                j = json.loads(line)
                if j.get('quality_score', 0) > 0.7 and 50 < len(j['text']) < 250:
                    candidates.append({"text": j['text'].strip(), "source": "chunks"})
                    
    return candidates

def main():
    parser = argparse.ArgumentParser(description="HOOK RANKER")
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--quotes", type=Path, required=True)
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--export-text", type=Path, help="Export top 5 hooks as plain text")
    args = parser.parse_args()

    raw_candidates = extract_candidates(args.script, args.quotes, args.chunks)
    
    # Score and Dedupe
    seen = set()
    ranked = []
    for c in raw_candidates:
        if c['text'] in seen: continue
        seen.add(c['text'])
        ranked.append(score_hook(c['text'], c['source']))
        
    ranked.sort(key=lambda x: x['score_total'], reverse=True)
    top_results = ranked[:args.top]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(top_results, f, indent=2)

    if args.export_text:
        with open(args.export_text, "w", encoding="utf-8") as f:
            for i, h in enumerate(top_results[:5], 1):
                f.write(f"{i}. {h['text']}\n\n")

    print(f"[OK] Hook Ranking Complete. Ranked {len(ranked)} candidates. Results: {args.out}")

if __name__ == "__main__":
    main()
