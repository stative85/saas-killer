# local_critic.py
import argparse
import json
import re
from pathlib import Path
from typing import Any
import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
DEFAULT_MODEL = "local-model"

def simulate_feedback(script_path: Path, model: str, timeout: int) -> dict[str, Any]:
    print(f"[*] Executing Synthetic Preflight for: {script_path.name}")
    
    if not script_path.exists():
        return {"status": "error", "critical_flaw": "File not found"}

    script_text = script_path.read_text(encoding="utf-8")

    system_prompt = (
        "You are a highly critical content analyst and audience retention expert. "
        "Evaluate scripts for human texture, creator voice strength, and emotional resonance. "
        "Aggressively identify and reject AI slop (overused corporate buzzwords, generic transitions). "
        "Output valid JSON only."
    )

    user_prompt = f"""
UNII DOCTRINE:
- No AI slop (e.g., 'unlock', 'leverage', 'dive in').
- Strong creator voice (texture, not noise).
- High resonance (concepts that stick).

SCRIPT TO ANALYZE:
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
        "temperature": 0.3, # Low temperature for consistent scoring
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

        # Robust JSON extraction (removes markdown fences if present)
        if "```" in content:
            content = re.search(r"\{(?:.|\n)*\}", content).group(0)

        parsed = json.loads(content)

        return {
            "status": "ok",
            "predicted_watch_ratio": float(parsed.get("predicted_watch_ratio", 0.0)),
            "slop_detected": bool(parsed.get("slop_detected", False)),
            "critical_flaw": str(parsed.get("critical_flaw", "Unknown")),
            "winning_line": str(parsed.get("winning_line", "None")),
        }
    except Exception as e:
        return {
            "status": "error",
            "predicted_watch_ratio": 0.0,
            "slop_detected": True,
            "critical_flaw": f"{type(e).__name__}: {e}",
            "winning_line": "",
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic Preflight Audience Simulator")
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    result = simulate_feedback(args.script, args.model, args.timeout)
    print(json.dumps(result, indent=2))
