# scout_extractor.py
import json
import argparse
import re
from pathlib import Path
from collections import defaultdict

def extract_scout_signal(file_path: Path):
    text = file_path.read_text(encoding="utf-8", errors="replace")
    
    # 1. SHOCK KEYWORDS
    shock_patterns = [
        r"\b(billion|trillion|breakthrough|weapon|war|genetic|brain|openai|threat|elite|death|reversal|immortality)\b",
        r"\b(we are built|we just|the first ever|no rules|secret|underground|collapse)\b"
    ]
    
    # 2. DECLARATIVE CLAIMS (I think, we believe, the reality is)
    claim_patterns = [
        r"(the (reality|truth|fact) is .*?[.!?])",
        r"(we (believe|are doing|just built) .*?[.!?])",
        r"(this (is|was|will) .*?[.!?])"
    ]

    signals = []
    lines = text.split('.')
    
    for line in lines:
        line = line.strip()
        if len(line) < 40 or len(line) > 300: continue
        
        score = 0
        reasons = []
        
        # Scoring
        for p in shock_patterns:
            if re.search(p, line, re.I):
                score += 2
                reasons.append("shock")
        
        for p in claim_patterns:
            if re.search(p, line, re.I):
                score += 1
                reasons.append("claim")
        
        if score >= 2:
            signals.append({
                "text": line,
                "source": file_path.name,
                "reasons": list(set(reasons)),
                "resonance": score
            })
            
    return signals

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(list(args.input_dir.glob("*.txt")))[:48]
    print(f"[*] Executing Pressure Pass on {len(files)} target files...")
    
    all_signals = []
    for f in files:
        all_signals.extend(extract_scout_signal(f))
        
    all_signals.sort(key=lambda x: x['resonance'], reverse=True)
    
    # Save as JSONL for the generator
    with open(args.out, "w", encoding="utf-8") as f:
        for s in all_signals:
            f.write(json.dumps(s) + "\n")
            
    print(f"[✅] Scout Pass Complete. {len(all_signals)} signals extracted to {args.out.name}")

if __name__ == "__main__":
    main()
