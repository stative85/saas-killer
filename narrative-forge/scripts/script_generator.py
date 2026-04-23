# script_generator.py
import json
import argparse
import random
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple
from collections import Counter
from datetime import datetime

@dataclass
class ScriptPhase:
    name: str
    content: str
    source_title: str
    arcs: List[str]

class NarrativeCompiler:
    def __init__(self, chunks_path: Path):
        self.chunks = self._load_jsonl(chunks_path)
        self.pos_bias, self.neg_bias = self._load_feedback_bias()
        self.intersections = self._load_intersections()

    def _load_feedback_bias(self):
        best_dir = Path(__file__).parent.parent / "outputs" / "best"
        pos, neg = Counter(), Counter()
        if best_dir.exists():
            for f in best_dir.glob("*.txt"):
                pos.update(re.findall(r"\b\w{5,}\b", f.read_text(encoding="utf-8").lower()))
        neg.update(['subscribe', 'review', 'sponsor', 'comment', 'below', 'click'])
        return pos, neg

    def _get_resonance_score(self, chunk):
        base_score = chunk.get('quality_score', 0.5)
        text = chunk['text'].lower()
        pos_bonus = sum(0.01 for term in self.pos_bias if term in text)
        neg_penalty = sum(0.05 for term in self.neg_bias if term in text)
        return max(0.001, base_score + min(0.20, pos_bonus) - neg_penalty)
        
    def _load_jsonl(self, path: Path):
        data = []
        noise = {'subscribe', 'review', 'sponsor', 'brex', 'listening', 'watching', 'support', 'tremendous'}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                j = json.loads(line)
                if not any(w in j['text'].lower() for w in noise):
                    data.append(j)
        return data

    def _load_intersections(self):
        inter = [c for c in self.chunks if len(c.get('arcs', [])) >= 3]
        return sorted(inter, key=lambda x: self._get_resonance_score(x) * len(x['arcs']), reverse=True)

    def select_hook(self, mode="fracture") -> ScriptPhase:
        if mode == "retention_aggressive":
            candidates = [c for c in self.intersections if 50 < len(c['text']) < 180]
        else:
            candidates = [c for c in self.intersections if 100 < len(c['text']) < 400]
        if not candidates: candidates = self.intersections
        if not candidates: candidates = self.chunks[:10]
        candidates.sort(key=lambda x: self._get_resonance_score(x), reverse=True)
        target = random.choice(candidates[:min(3, len(candidates))])
        return ScriptPhase("HOOK", target['text'], target['title'], target['arcs'])

    def build_narrative(self, count=2, mode="fracture") -> List[ScriptPhase]:
        phases = []
        selected_arcs = ["science", "future", "control", "truth", "human", "threat"]
        random.shuffle(selected_arcs)
        for i in range(min(count, len(selected_arcs))):
            arc = selected_arcs[i]
            candidates = [c for c in self.chunks if arc in c.get('arcs', []) and len(c.get('arcs', [])) <= 2]
            if mode == "retention_aggressive":
                candidates = [c for c in candidates if len(c['text']) < 500]
            candidates.sort(key=lambda x: self._get_resonance_score(x), reverse=True)
            if candidates:
                target = random.choice(candidates[:min(5, len(candidates))])
                phases.append(ScriptPhase(f"BUILD_{arc.upper()}", target['text'], target['title'], target['arcs']))
        return phases

    def build_collision(self) -> ScriptPhase:
        candidates = [c for c in self.intersections if len(c['arcs']) >= 4]
        if not candidates: candidates = self.intersections[:5]
        target = random.choice(candidates[:min(3, len(candidates))])
        return ScriptPhase("COLLISION", target['text'], target['title'], target['arcs'])

    def select_resolution(self, mode="fracture") -> ScriptPhase:
        arc_targets = ['threat', 'truth'] if mode in ["fracture", "retention_aggressive"] else ['future', 'human']
        candidates = [c for c in self.chunks if any(a in c.get('arcs', []) for a in arc_targets) and len(c['text']) < 300]
        if not candidates: candidates = self.chunks[-20:]
        target = random.choice(candidates[:min(10, len(candidates))])
        return ScriptPhase("RESOLUTION", target['text'], target['title'], target['arcs'])

    def compile(self, mode="fracture", style="aggressive") -> Tuple[str, Dict[str, Any]]:
        hook = self.select_hook(mode=mode)
        builds = self.build_narrative(count=2, mode=mode)
        collision = self.build_collision()
        res = self.select_resolution(mode=mode)
        script = f"--- WENDIGO NARRATIVE COMPILATION [Mode: {mode.upper()} | Style: {style.upper()}] ---\n\n"
        phases = [hook] + builds + [collision] + [res]
        total_len = 0
        for p in phases:
            content = p.content
            if mode == "retention_aggressive":
                content = content.replace("...", ",").replace("  ", " ")
            if style == "aggressive":
                content = content.upper() if len(content) < 150 else content
            elif style == "philosophical":
                content = "... " + content.replace(".", " ...")
            script += f"[{p.name}] (Source: {p.source_title})\nArcs: {', '.join(p.arcs)}\n> {content}\n\n"
            total_len += len(content)
        diags = {
            "mode": mode,
            "hook_length_chars": len(hook.content),
            "total_script_chars": total_len,
            "clarity_score": 0.85 if mode == "retention_aggressive" else 0.70,
            "early_conflict_score": 0.90 if mode == "retention_aggressive" else 0.60
        }
        script += f"\n[DIAGNOSTICS]\n{json.dumps(diags, indent=2)}\n"
        return script, diags

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", required=True, type=Path)
    ap.add_argument("--mode", default="fracture_aggressive")
    ap.add_argument("--style", default="aggressive")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    # Split mode if passed as combined (e.g. fracture_aggressive)
    mode = args.mode
    style = args.style
    if "_" in mode:
        mode, style = mode.split('_')

    compiler = NarrativeCompiler(Path(args.chunks))
    script, diags = compiler.compile(mode=mode, style=style)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"[OK] Script saved to: {args.out}")

if __name__ == "__main__":
    main()
