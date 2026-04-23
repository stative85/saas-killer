# script_generator.py
import json
import argparse
import random
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
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
        self.intersections = self._load_intersections()
        self.pos_bias, self.neg_bias = self._load_feedback_bias()

    def _load_feedback_bias(self):
        """Extracts positive and negative linguistic patterns."""
        best_dir = Path(__file__).parent.parent / "outputs" / "best"
        failed_dir = Path(__file__).parent.parent / "outputs" / "failed"
        
        pos = Counter()
        neg = Counter()

        if best_dir.exists():
            for f in best_dir.glob("*.txt"):
                pos.update(re.findall(r"\b\w{5,}\b", f.read_text(encoding="utf-8").lower()))
        
        # Manual negative bias for v0 filler suppression
        neg.update(['subscribe', 'review', 'sponsor', 'comment', 'below', 'click'])
        
        return pos, neg

    def _get_resonance_score(self, chunk):
        """Weights a chunk based on quality, positive resonance, and negative suppression."""
        base_score = chunk['quality_score']
        text = chunk['text'].lower()
        
        # Steering Logic
        pos_bonus = sum(0.01 for term in self.pos_bias if term in text)
        neg_penalty = sum(0.05 for term in self.neg_bias if term in text)
        
        bias_cap = 0.20
        steered_score = base_score + min(bias_cap, pos_bonus) - neg_penalty
        
        return max(0.001, steered_score)
        
    def _load_jsonl(self, path: Path):
        data = []
        noise_words = {'subscribe', 'review', 'sponsor', 'brex', 'listening', 'watching', 'support', 'tremendous'}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                j = json.loads(line)
                if not any(w in j['text'].lower() for w in noise_words):
                    data.append(j)
        return data

    def _load_intersections(self):
        intersections = [c for c in self.chunks if len(c.get('arcs', [])) >= 3]
        return sorted(intersections, key=lambda x: x['quality_score'] * len(x['arcs']), reverse=True)

    def select_hook(self) -> ScriptPhase:
        candidates = [c for c in self.intersections if 100 < len(c['text']) < 400]
        if not candidates: candidates = self.intersections
        if not candidates: candidates = self.chunks[:10]
        target = random.choice(candidates[:min(5, len(candidates))])
        return ScriptPhase("HOOK", target['text'], target['title'], target['arcs'])

    def build_narrative(self, count=2) -> List[ScriptPhase]:
        phases = []
        selected_arcs = ["science", "future", "control", "truth", "human", "threat"]
        random.shuffle(selected_arcs)
        for i in range(min(count, len(selected_arcs))):
            arc = selected_arcs[i]
            candidates = [c for c in self.chunks if arc in c.get('arcs', []) and len(c.get('arcs', [])) <= 2]
            candidates.sort(key=lambda x: x['quality_score'], reverse=True)
            if candidates:
                target = random.choice(candidates[:10])
                phases.append(ScriptPhase(f"BUILD_{arc.upper()}", target['text'], target['title'], target['arcs']))
        return phases

    def build_collision(self) -> ScriptPhase:
        candidates = [c for c in self.intersections if len(c['arcs']) >= 4]
        if not candidates: candidates = self.intersections[:5]
        if not candidates: candidates = self.chunks[:5]
        target = random.choice(candidates[:min(3, len(candidates))])
        return ScriptPhase("COLLISION", target['text'], target['title'], target['arcs'])

    def select_resolution(self, mode="fracture") -> ScriptPhase:
        if mode == "fracture":
            candidates = [c for c in self.chunks if any(a in c.get('arcs', []) for a in ['threat', 'truth']) and len(c['text']) < 250]
        else:
            candidates = [c for c in self.chunks if any(a in c.get('arcs', []) for a in ['future', 'human']) and len(c['text']) < 400]
        if not candidates: candidates = self.chunks[-20:]
        target = random.choice(candidates[:min(20, len(candidates))])
        return ScriptPhase("RESOLUTION", target['text'], target['title'], target['arcs'])

    def compile(self, mode="fracture", style="aggressive") -> str:
        hook = self.select_hook()
        builds = self.build_narrative(count=2)
        collision = self.build_collision()
        res = self.select_resolution(mode=mode)
        
        script = f"--- WENDIGO NARRATIVE COMPILATION [Mode: {mode.upper()} | Style: {style.upper()}] ---\n\n"
        phases = [hook] + builds + [collision] + [res]
        for p in phases:
            content = p.content
            if style == "aggressive":
                content = content.upper() if len(content) < 150 else content
            elif style == "philosophical":
                content = "... " + content.replace(".", " ...")
            script += f"[{p.name}] (Source: {p.source_title})\n"
            script += f"Arcs: {', '.join(p.arcs)}\n"
            script += f"> {content}\n\n"
        return script

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=r"C:\Users\cleve\OneDrive\Pictures\corpus_run\index\chunks_with_arcs.jsonl")
    ap.add_argument("--mode", choices=["fracture", "closed"], default="fracture")
    ap.add_argument("--style", choices=["documentary", "aggressive", "philosophical", "lyrical"], default="documentary")
    args = ap.parse_args()

    compiler = NarrativeCompiler(Path(args.chunks))
    script = compiler.compile(mode=args.mode, style=args.style)
    print(script)
    
    out_dir = Path(r"C:\Users\cleve\OneDrive\Pictures\corpus_run\exports\scripts")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"generated_script_{args.mode}_{args.style}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"\n[+] Script saved to: {out_file}")

if __name__ == "__main__":
    main()
