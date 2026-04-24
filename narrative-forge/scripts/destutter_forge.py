import re
import argparse
from pathlib import Path

def destutter_text(text: str) -> str:
    """Collapses rhythmic word-level stutters (echo anomaly)."""
    # 1. Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    
    # 2. Sequential N-Gram Collapse (Word-level)
    # We look for [A B C] [A B C] and replace with [A B C]
    # We test window sizes from 12 words down to 2
    words = text.split()
    for size in range(12, 1, -1):
        i = 0
        while i < len(words) - size * 2:
            chunk1 = words[i:i+size]
            chunk2 = words[i+size:i+size*2]
            if chunk1 == chunk2:
                # Remove the stuttering chunk
                del words[i+size:i+size*2]
                # Stay at same i to check for triple/quadruple stutters
            else:
                i += 1
    
    return " ".join(words)

def main():
    parser = argparse.ArgumentParser(description="FORENSIC DE-STUTTER FORGE")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    print(f"[*] Infiltrating Echo Chamber: {args.input.name}")
    raw = args.input.read_text(encoding="utf-8", errors="replace")
    
    clean = destutter_text(raw)
    
    # Final cleanup: sentence boundaries
    clean = re.sub(r'([.!?])', r'\1\n', clean)
    
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(clean, encoding="utf-8")
    print(f"[✅] Echo Chamber Neutralized: {args.output.name}")

if __name__ == "__main__":
    main()
