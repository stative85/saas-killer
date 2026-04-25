# scout_ranker.py
import json
import argparse
import re
from pathlib import Path

def score_script(path: Path):
    text = path.read_text(encoding="utf-8")
    
    # 1. Hook Violence (First 500 chars)
    hook_zone = text[:500].lower()
    shock_terms = ["brain", "weapon", "war", "genetic", "secret", "billion", "threat", "death", "no rules"]
    hook_violence = sum(2 for t in shock_terms if t in hook_zone)
    
    # 2. Source Diversity
    sources = re.findall(r"Source: (.*?)\)", text)
    novelty = len(set(sources))
    
    # 3. Comment-Bait (Specific technocratic triggers)
    bait_terms = ["openai", "elon", "government", "military", "ai ceo", "underground"]
    comment_bait = sum(1 for t in bait_terms if t in text.lower())
    
    total_score = (hook_violence * 1.5) + (novelty * 1.0) + (comment_bait * 1.2)
    
    return {
        "file": path.name,
        "score": total_score,
        "metrics": {"violence": hook_violence, "novelty": novelty, "bait": comment_bait}
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    results = []
    for f in args.in_dir.glob("*.txt"):
        results.append(score_script(f))
        
    results.sort(key=lambda x: x['score'], reverse=True)
    
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"[✅] Ranking Complete. Top Variant: {results[0]['file']} (Score: {results[0]['score']})")

if __name__ == "__main__":
    main()
