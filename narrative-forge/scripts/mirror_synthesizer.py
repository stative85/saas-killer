# mirror_synthesizer.py
import json
import argparse
import random
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

@dataclass
class ScriptPhase:
    name: str
    content: str
    source_title: str
    arcs: List[str]
    origin: str

class MirrorCompiler:
    def __init__(self, modern_path: Path, historical_path: Path):
        # THE AD-BREAKER BLACKLIST - MUST BE INIT BEFORE LOADING
        self.blacklist = {
            'infowarstore', 'store', 'bottle', 'sale', 'percent', 'off', 'checkout', 
            'shipping', 'discount', 'price', 'product', 'buy', 'purchase',
            'class', 'next week', 'lecture', 'exam', 'student', 'semester', 'course',
            'thank you', 'watching', 'listening', 'subscribe', 'follow'
        }
        self.modern_chunks = self._load_jsonl(modern_path)
        self.historical_chunks = self._load_jsonl(historical_path)

    def _load_jsonl(self, path: Path):
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                j = json.loads(line)
                # DYNAMIC FILTERING
                text_low = j['text'].lower()
                if not any(w in text_low for w in self.blacklist):
                    data.append(j)
        return data

    def select_chunk(self, source_pool: List[Dict], arcs: List[str] = None, max_len: int = 500) -> Dict:
        candidates = source_pool
        if arcs:
            candidates = [c for c in source_pool if any(a in c.get('arcs', []) for a in arcs)]
        
        candidates = [c for c in candidates if 100 < len(c['text']) < max_len]
        if not candidates: candidates = source_pool[:20]
        
        # RESONANCE FILTER: Chunks must have strong arc density
        candidates.sort(key=lambda x: x.get('quality_score', 0.5) * len(x.get('arcs', [])), reverse=True)
        
        return random.choice(candidates[:min(10, len(candidates))])

    def compile(self, ratio_modern: float = 0.5, mode="fusion") -> str:
        phases = []
        # HOOK
        hook_source = self.historical_chunks if ratio_modern > 0.5 else self.modern_chunks
        hook_origin = 'historical' if ratio_modern > 0.5 else 'modern'
        hook = self.select_chunk(hook_source, arcs=['threat', 'truth'], max_len=300)
        phases.append(ScriptPhase("HOOK", hook['text'], hook['title'], hook['arcs'], hook_origin))

        # BUILD
        build_source = self.modern_chunks if ratio_modern >= 0.5 else self.historical_chunks
        build_origin = 'modern' if ratio_modern >= 0.5 else 'historical'
        build = self.select_chunk(build_source, arcs=['control', 'science'], max_len=600)
        phases.append(ScriptPhase("BUILD", build['text'], build['title'], build['arcs'], build_origin))

        # COLLISION
        collision_source = self.historical_chunks if ratio_modern >= 0.5 else self.modern_chunks
        collision_origin = 'historical' if ratio_modern >= 0.5 else 'modern'
        collision = self.select_chunk(collision_source, arcs=['future', 'human'], max_len=600)
        phases.append(ScriptPhase("COLLISION", collision['text'], collision['title'], collision['arcs'], collision_origin))

        # RESOLUTION
        res = self.select_chunk(self.historical_chunks, arcs=['truth', 'future'], max_len=400)
        phases.append(ScriptPhase("RESOLUTION", res['text'], res['title'], res['arcs'], 'historical'))

        script = f"--- THE TITANIUM MIRROR [{mode.upper()}] ---\n"
        script += f"Temporal Balance: {ratio_modern*100}% Modern / {(1-ratio_modern)*100}% Historical\n\n"
        
        for p in phases:
            script += f"[{p.name}] ({p.origin.upper()} | {p.source_title})\n"
            script += f"Arcs: {', '.join(p.arcs)}\n"
            script += f"> {p.content.strip()}\n\n"
            
        return script

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modern", required=True, type=Path)
    ap.add_argument("--historical", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    compiler = MirrorCompiler(args.modern, args.historical)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    v1 = compiler.compile(ratio_modern=0.2, mode="historical_heavy")
    (args.out_dir / "mirror_historical_heavy.txt").write_text(v1, encoding="utf-8")

    v2 = compiler.compile(ratio_modern=0.8, mode="modern_heavy")
    (args.out_dir / "mirror_modern_heavy.txt").write_text(v2, encoding="utf-8")

    v3 = compiler.compile(ratio_modern=0.5, mode="balanced_fusion")
    (args.out_dir / "mirror_balanced_fusion.txt").write_text(v3, encoding="utf-8")

    print(f"[✅] Titanium Mirror Synthesis Complete. All variants purified.")

if __name__ == "__main__":
    main()
