# affiliate_mapper.py
import json
import argparse
import re
from pathlib import Path

# --- THE REVENUE WHITELIST ---
# Maps keywords found in tech/civ/biotech signal to high-payout anchors
AFFILIATE_MAP = {
    "openai": {"link": "https://openai.com/api", "label": "Build with OpenAI API"},
    "genetic": {"link": "https://www.23andme.com/", "label": "Decode Your DNA"},
    "brain": {"link": "https://www.neuralink.com/", "label": "The Neural Frontier"},
    "crypto": {"link": "https://www.coinbase.com/join", "label": "Sovereign Finance Start"},
    "bio": {"link": "https://www.insidetracker.com/", "label": "Optimize Your Biology"},
    "aging": {"link": "https://blueprint.bryanjohnson.com/", "label": "Reversal Protocol"},
    "compute": {"link": "https://www.nvidia.com/en-us/data-center/", "label": "Enterprise GPU Compute"}
}

def map_revenue_anchors(script_text: str):
    anchors = []
    text_low = script_text.lower()
    
    for key, data in AFFILIATE_MAP.items():
        if key in text_low:
            anchors.append(f"{data['label']}: {data['link']}")
            
    return list(set(anchors))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    # Paths
    run_dir = Path("narrative-forge/outputs/runs") / args.run_id
    pack_path = run_dir / "deploy_pack.json"
    
    if not pack_path.exists():
        print(f"[!] Deploy pack missing for {args.run_id}")
        return

    with open(pack_path, "r") as f:
        pack = json.load(f)

    # Extract anchors from the primary hook and script
    anchors = map_revenue_anchors(pack.get("primary_hook", "") + " " + pack.get("title", ""))
    
    if anchors:
        print(f"[*] Revenue Anchors Found: {len(anchors)}")
        # Inject into pinned comment
        pack["pinned_comment"] = "\n".join(anchors) + "\n\n" + pack.get("pinned_comment", "")
        
        with open(pack_path, "w") as f:
            json.dump(pack, f, indent=2)
        print(f"[✅] Deploy Pack Weaponized for Arbitrage: {args.run_id}")
    else:
        print("[*] No high-intent anchors detected.")

if __name__ == "__main__":
    main()
