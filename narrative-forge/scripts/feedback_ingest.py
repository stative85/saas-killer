# feedback_ingest.py
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# --- CONFIGURATION ---
MAX_BIAS_TERMS = 300
DECAY_RATE = 0.9 # Factor to multiply current resonance by before update

def compute_engagement_score(views: int, watch_ratio: float, like_ratio: float) -> float:
    # Watch ratio is prioritized heavily
    return (0.6 * watch_ratio + 0.3 * (min(views, 5000) / 5000) + 0.1 * like_ratio)

def extract_patterns(text: str) -> List[str]:
    # Extract recurring strong nouns/verbs (len > 5)
    return list(set(re.findall(r"\b\w{6,}\b", text.lower())))

def update_bias(current: Dict[str, float], new_terms: List[str], weight: float):
    # Decay existing
    for t in current:
        current[t] *= DECAY_RATE
        
    # Add/Update new
    for t in new_terms:
        current[t] = current.get(t, 0.0) + weight
    
    # Cap and Clean
    sorted_terms = sorted(current.items(), key=lambda x: x[1], reverse=True)[:MAX_BIAS_TERMS]
    return {k: round(v, 3) for k, v in sorted_terms if v > 0.01}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", type=Path, required=True)
    parser.add_argument("--positive", type=Path, required=True)
    parser.add_argument("--negative", type=Path, required=True)
    parser.add_argument("--hook-patterns", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    # Load Inputs
    with open(args.feedback, "r") as f:
        fb = json.load(f)
    
    pos_bias = json.loads(args.positive.read_text()) if args.positive.exists() else {}
    neg_bias = json.loads(args.negative.read_text()) if args.negative.exists() else {}
    hook_patterns = json.loads(args.hook_patterns.read_text()) if args.hook_patterns.exists() else []

    # Process Performance
    likes = fb.get('likes', 0)
    views = fb.get('views', 1)
    like_ratio = likes / views
    engagement = compute_engagement_score(views, fb.get('avg_watch_ratio', 0.0), like_ratio)
    
    # Determine Class
    if engagement > 0.5:
        mode = "WINNER"
        weight = 0.2
    elif engagement < 0.2:
        mode = "FAILURE"
        weight = -0.2
    else:
        mode = "NEUTRAL"
        weight = 0.0

    print(f"[*] Ingesting {fb['run_id']} | Mode: {mode} | Engagement: {engagement:.2f}")

    # Extract Text for Bias
    script_path = Path(fb['script_path'])
    if script_path.exists():
        text = script_path.read_text(encoding="utf-8")
        terms = extract_patterns(text)
        
        if mode == "WINNER":
            pos_bias = update_bias(pos_bias, terms, weight)
            # Add hook to memory
            hook_patterns.append({
                "run_id": fb['run_id'],
                "hook": fb['hook_used'],
                "score": engagement,
                "date": datetime.now().isoformat()
            })
        elif mode == "FAILURE":
            neg_bias = update_bias(neg_bias, terms, abs(weight))

    # Save Outputs
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "positive_bias_updated.json", "w") as f: json.dump(pos_bias, f, indent=2)
    with open(args.out_dir / "negative_bias_updated.json", "w") as f: json.dump(neg_bias, f, indent=2)
    with open(args.out_dir / "hook_patterns_updated.json", "w") as f: json.dump(hook_patterns[:100], f, indent=2)
    
    summary = {
        "run_id": fb['run_id'],
        "engagement_score": engagement,
        "performance_class": mode,
        "terms_processed": len(terms) if 'terms' in locals() else 0
    }
    with open(args.out_dir / "feedback_summary.json", "w") as f: json.dump(summary, f, indent=2)

    print(f"[✅] Feedback Ingestion Complete. Performance: {mode}. Updates in: {args.out_dir}")

if __name__ == "__main__":
    main()
