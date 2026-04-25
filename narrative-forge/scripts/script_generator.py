import json
import argparse
import random
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

@dataclass
class ScriptPhase:
    name: str
    content: str
    source_title: str
    arcs: List[str]

class ScriptCompiler:
    def __init__(self, chunks_path: Path):
        self.chunks = []
        self.used_ids = set()
        # THE AD-BREAKER BLACKLIST
        self.blacklist = {
            'infowarstore', 'store.com', 'dvd', 't-shirt', 'limited edition', 'fundraiser',
            'checkout', 'shipping', 'discount', 'price', 'product', 'buy', 'purchase',
            'class', 'next week', 'lecture', 'exam', 'student', 'semester', 'course',
            'thank you', 'watching', 'listening', 'subscribe', 'follow', 'visit'
        }
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            for line in f:
                j = json.loads(line)
                text_low = j['text'].lower()
                if not any(w in text_low for w in self.blacklist):
                    self.chunks.append(j)

    def get_source_title(self, chunk: Dict) -> str:
        return chunk.get('title') or chunk.get('source') or "Unknown Signal"

    def select_unique_chunk(self, candidates: List[Dict]) -> Dict:
        # Filter out used
        fresh = [c for c in candidates if c['text'] not in self.used_ids]
        if not fresh: return random.choice(candidates)
        
        # Selection
        target = random.choice(fresh[:min(3, len(fresh))])
        self.used_ids.add(target['text'])
        return target

    def select_hook(self, mode: str = "retention") -> Dict:
        target_arcs = ['threat', 'truth'] if mode == "fracture" else ['human', 'future']
        candidates = [c for c in self.chunks if any(a in c.get('arcs', []) for a in target_arcs)]
        candidates = [c for c in candidates if 100 < len(c['text']) < 400]
        if not candidates: candidates = self.chunks[:10]
        candidates.sort(key=lambda x: x.get('quality_score', 0.5) * len(x.get('arcs', [])), reverse=True)
        return self.select_unique_chunk(candidates)

    def select_build(self, arc: str, max_len: int = 800) -> Dict:
        candidates = [c for c in self.chunks if arc in c.get('arcs', [])]
        # Handle cases where arc classification might be missing in scout_signals
        if not candidates: candidates = self.chunks
        
        candidates = [c for c in candidates if 300 < len(c['text']) < max_len]
        if not candidates: candidates = self.chunks[:20]
        candidates.sort(key=lambda x: x.get('quality_score', 0.5), reverse=True)
        return self.select_unique_chunk(candidates)

    def compile(self, mode: str = "retention", style: str = "aggressive") -> Tuple[str, Dict]:
        self.used_ids = set() # Reset for each script
        phases = []
        
        # 1. HOOK
        hook = self.select_hook(mode=mode)
        phases.append(ScriptPhase("HOOK", hook['text'], self.get_source_title(hook), hook.get('arcs', [])))

        # 2. BUILD 1 (Truth or Control)
        b1 = self.select_build('truth' if style == "aggressive" else "human")
        phases.append(ScriptPhase("BUILD_TRUTH", b1['text'], self.get_source_title(b1), b1.get('arcs', [])))

        # 3. BUILD 2 (Science or Future)
        b2 = self.select_build('future' if mode == "retention" else "science")
        phases.append(ScriptPhase("BUILD_FUTURE", b2['text'], self.get_source_title(b2), b2.get('arcs', [])))

        # 4. COLLISION (The Peak)
        col = self.select_build('threat' if style == "aggressive" else "human", max_len=1000)
        phases.append(ScriptPhase("COLLISION", col['text'], self.get_source_title(col), col.get('arcs', [])))

        # 5. RESOLUTION
        res = self.select_build('future', max_len=400)
        phases.append(ScriptPhase("RESOLUTION", res['text'], self.get_source_title(res), res.get('arcs', [])))

        script = f"--- WENDIGO NARRATIVE COMPILATION [Mode: {mode.upper()} | Style: {style.upper()}] ---\n\n"
        for p in phases:
            script += f"[{p.name}] (Source: {p.source_title})\n"
            script += f"Arcs: {', '.join(p.arcs)}\n"
            script += f"> {p.content.strip()}\n\n"

        diags = { "mode": mode, "total_script_chars": len(script) }
        return script, diags

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--mode", choices=["retention", "fracture"], default="retention")
    parser.add_argument("--style", choices=["aggressive", "humanist"], default="aggressive")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    compiler = ScriptCompiler(args.chunks)
    script, diags = compiler.compile(mode=args.mode, style=args.style)
    script += f"\n\n[DIAGNOSTICS]\n{json.dumps(diags, indent=2)}"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(script, encoding="utf-8")
    print(f"[OK] Script saved to: {args.out}")

if __name__ == "__main__":
    main()
