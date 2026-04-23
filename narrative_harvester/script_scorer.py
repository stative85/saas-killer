# script_scorer.py
import argparse, json, re, math
from pathlib import Path
from collections import Counter

def get_lines(t): return [l.strip() for l in t.splitlines() if l.strip()]
def get_toks(t): return re.findall(r"[a-zA-Z0-9']+", t.lower())

def hook_strength(ls):
    first = " ".join(ls[:5]) # look at the first few lines
    strong_terms = ["truth","system","control","future","death","ai","power","reality"]
    strong = sum(w in first.lower() for w in strong_terms)
    brev = 1.0 if sum(len(l) for l in ls[:3]) < 350 else 0.6
    return min(1.0, 0.5 * (strong / 3) + 0.5 * brev)

def arc_balance(t):
    need = ["[HOOK]","[BUILD","[COLLISION]","[RESOLUTION]"]
    count = sum(1 for k in need if k in t)
    return count / len(need)

def novelty(t):
    words = get_toks(t)
    if len(words) < 3: return 0.0
    grams = [tuple(words[i:i+3]) for i in range(len(words)-2)]
    c = Counter(grams)
    rep = sum(v-1 for v in c.values() if v > 1)
    return max(0.0, 1.0 - min(1.0, rep / 150))

def coherence(ls):
    lens = [len(l) for l in ls]
    if not lens: return 0.0
    mean = sum(lens) / len(lens)
    var = sum((x - mean)**2 for x in lens) / len(lens)
    # Penalize extreme variance (chaotic structure) or zero variance (repetitive robot)
    return max(0.0, 1.0 - min(1.0, var / (mean * mean + 1)))

def punch_density(ls):
    punchy = sum(1 for l in ls if 20 <= len(l) <= 180 and l.count(",") <= 2)
    return punchy / max(len(ls), 1)

def compute_score(text):
    ls = get_lines(text)
    s = {
        "hook": hook_strength(ls),
        "arc_balance": arc_balance(text),
        "novelty": novelty(text),
        "coherence": coherence(ls),
        "punch_density": punch_density(ls),
    }
    s["total"] = (
        0.25 * s["hook"] + 
        0.20 * s["arc_balance"] + 
        0.20 * s["novelty"] + 
        0.15 * s["coherence"] + 
        0.20 * s["punch_density"]
    )
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    p = Path(args.in_dir)
    results = []
    for f in sorted(p.glob("*.txt")):
        try:
            txt = f.read_text(encoding="utf-8")
            s = compute_score(txt)
            results.append({"file": str(f), "score": s})
        except Exception as e:
            print(f"Error scoring {f}: {e}")

    if not results:
        print("No candidates to score.")
        return

    results.sort(key=lambda x: x["score"]["total"], reverse=True)
    
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    
    print(f"Ranked {len(results)} candidates.")
    print(f"Best: {results[0]['file']} (Score: {results[0]['score']['total']:.2f})")

if __name__ == "__main__":
    main()
