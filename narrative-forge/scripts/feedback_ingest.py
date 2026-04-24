# feedback_ingest.py
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# --- CONFIG ---
MAX_BIAS_TERMS = 300
DECAY_RATE = 0.9
VIEW_FLOOR = 500 # Must have at least 500 views to be a 'Winner'
WATCH_RATIO_THRESHOLD = 0.45 # Must beat 40% watch ratio

# --- PATHS ---
FORGE_DIR = Path(__file__).parent.parent.absolute()
BIAS_CONFIG = FORGE_DIR / "configs" / "bias_store.json"
LEADERBOARD_FILE = FORGE_DIR / "outputs" / "leaderboard.json"

def compute_engagement_score(views: int, watch_ratio: float, like_ratio: float) -> float:
    return (0.6 * watch_ratio + 0.3 * (min(views, 5000) / 5000) + 0.1 * like_ratio)

def extract_patterns(text: str) -> List[str]:
    return list(set(re.findall(r"\b\w{6,}\b", text.lower())))

def update_bias(current: Dict[str, float], new_terms: List[str], weight: float):
    for t in current: current[t] *= DECAY_RATE
    for t in new_terms: current[t] = current.get(t, 0.0) + weight
    sorted_terms = sorted(current.items(), key=lambda x: x[1], reverse=True)[:MAX_BIAS_TERMS]
    return {k: round(v, 3) for k, v in sorted_terms if v > 0.01}

def update_leaderboard(entry):
    leaderboard = []
    if LEADERBOARD_FILE.exists():
        leaderboard = json.loads(LEADERBOARD_FILE.read_text())
    
    # Check if run already exists
    leaderboard = [r for r in leaderboard if r['run_id'] != entry['run_id']]
    leaderboard.append(entry)
    leaderboard.sort(key=lambda x: x.get('avg_watch_ratio', 0), reverse=True)
    
    LEADERBOARD_FILE.write_text(json.dumps(leaderboard, indent=2), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    # 1. LOAD DATA
    with open(args.feedback, "r", encoding="utf-8-sig") as f:
        fb = json.load(f)
    
    pos_path = FORGE_DIR / "configs" / "positive_bias_terms.json"
    neg_path = FORGE_DIR / "configs" / "negative_bias_terms.json"
    
    pos_bias = json.loads(pos_path.read_text()) if pos_path.exists() else {}
    neg_bias = json.loads(neg_path.read_text()) if neg_path.exists() else {}

    # 2. THE WINNER GATE
    views = fb.get('views', 0)
    watch_ratio = fb.get('avg_watch_ratio', 0.0)
    likes = fb.get('likes', 0)
    like_ratio = likes / views if views > 0 else 0
    engagement = compute_engagement_score(views, watch_ratio, like_ratio)

    is_winner = (views >= VIEW_FLOOR and watch_ratio >= WATCH_RATIO_THRESHOLD)
    is_failure = (views >= VIEW_FLOOR and watch_ratio < 0.20)
    
    status = "WINNER" if is_winner else "FAILURE" if is_failure else "NEUTRAL"
    print(f"[*] Analyzing Run: {fb['run_id']} | Status: {status} | Engagement: {engagement:.2f}")

    # 3. MUTATE MEMORY (ONLY ON WINNER/FAILURE GATES)
    bias_applied = False
    script_path = Path(fb['script_path'])
    if script_path.exists() and (is_winner or is_failure):
        text = script_path.read_text(encoding="utf-8")
        terms = extract_patterns(text)
        if is_winner:
            pos_bias = update_bias(pos_bias, terms, 0.2)
        else:
            neg_bias = update_bias(neg_bias, terms, 0.2)
        bias_applied = True

    # 4. UPDATE LEADERBOARD
    leaderboard_entry = {
        "run_id": fb['run_id'],
        "hook": fb['hook_used'],
        "mode": fb.get('mode', 'unknown'),
        "hook_type": fb.get('hook_type', 'unknown'),
        "views": views,
        "avg_watch_ratio": watch_ratio,
        "likes": likes,
        "bias_delta_applied": bias_applied,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    update_leaderboard(leaderboard_entry)

    # 5. PERSIST
    pos_path.write_text(json.dumps(pos_bias, indent=2))
    neg_path.write_text(json.dumps(neg_bias, indent=2))
    
    print(f"[✅] Feedback Loop Closed. Bias Applied: {bias_applied}. Leaderboard Updated.")

if __name__ == "__main__":
    main()
