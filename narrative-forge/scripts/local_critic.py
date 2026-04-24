# local_critic.py
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
DEFAULT_MODEL = "local-model"

def simulate_feedback(script_path: Path, model: str, timeout: int, out_path: Path = None) -> dict[str, Any]:
    print(f"[*] Executing Synthetic Preflight for: {script_path.name}")
    
    if not script_path.exists():
        return {"status": "error", "critical_flaw": "File not found"}

    script_text = script_path.read_text(encoding="utf-8")

    system_prompt = (
        "You are a highly critical content analyst. "
        "Evaluate scripts for human texture, creator voice, resonance, and attention retention. "
        "Reject AI slop. Output valid JSON only."
    )

    user_prompt = f"""
UNII DOCTRINE:
- No AI slop.
- Strong creator voice.
- High resonance.

SCRIPT:
{script_text}

Return JSON with exactly these keys:
{{
  "predicted_watch_ratio": 0.0,
  "slop_detected": false,
  "critical_flaw": "identify the weakest point",
  "winning_line": "extract the highest-impact quote"
}}
""".strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }

    result = {
        "status": "error",
        "predicted_watch_ratio": 0.0,
        "slop_detected": True,
        "critical_flaw": "Unknown Error",
        "winning_line": ""
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

        if "```" in content:
            content = re.search(r"\{(?:.|\n)*\}", content).group(0)

        parsed = json.loads(content)
        result = {
            "status": "ok",
            "critic_model": model,
            "predicted_watch_ratio": float(parsed.get("predicted_watch_ratio", 0.0)),
            "slop_detected": bool(parsed.get("slop_detected", False)),
            "critical_flaw": str(parsed.get("critical_flaw", "None")),
            "winning_line": str(parsed.get("winning_line", "None")),
        }
    except Exception as e:
        result["critical_flaw"] = f"{type(e).__name__}: {e}"

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"[OK] Preflight Artifact Saved: {out_path}")

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    result = simulate_feedback(args.script, args.model, args.timeout, args.out)
    if not args.out:
        print(json.dumps(result, indent=2))
