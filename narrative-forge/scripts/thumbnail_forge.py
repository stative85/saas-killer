# thumbnail_forge.py
import json
import argparse
from pathlib import Path

def generate_prompts(metadata_path: Path):
    print(f"[*] Generating visual hooks for: {metadata_path.name}")
    with open(metadata_path, "r") as f:
        meta = json.load(f)
    
    hook = meta['primary_hook']
    arcs = ", ".join(meta['tags'][:3])

    # Visual Styles: Hyper-realistic, Esoteric, Technocratic, Dark
    prompts = [
        f"Hyper-realistic cinematic shot, {hook}, neon technocratic atmosphere, 8k, depth of field --ar 16:9",
        f"Esoteric geometric representation of {arcs}, tetrahedral structures, golden ratio, dark background, sacred geometry --v 6.0",
        f"Surrealist collage representing {hook}, human mind meeting AI lattice, high contrast, industrial grit --ar 16:9"
    ]
    
    return prompts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", type=Path, required=True)
    args = parser.parse_args()
    
    prompts = generate_prompts(args.meta)
    
    out_file = args.meta.parent / "thumbnail_prompts.txt"
    with open(out_file, "w") as f:
        for i, p in enumerate(prompts, 1):
            f.write(f"PROMPT {i}: {p}\n\n")
            
    print(f"[✅] Visual Hooks generated: {out_file}")

if __name__ == "__main__":
    main()
