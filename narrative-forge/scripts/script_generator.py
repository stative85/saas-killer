import json
import argparse
import random
import os
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

# ---------------------------------------------------------------------------
# WRITE STAGE (opt-in, --write)
#
# Without it this file SELECTS chunks and labels them. It does not write. The
# output is "here are the best passages from your archive", which is a clipping
# tool, not the 30-scripts deliverable MONETIZE.md sells.
#
# With --write, each selected chunk is handed to a local OpenAI-compatible
# model (LM Studio, llama.cpp, Ollama) and rewritten as spoken short-form copy.
# Local by default: no API key, no per-call cost, and the client's archive never
# leaves the machine — which is the thing an agency client actually cares about.
#
# PROVENANCE IS PRESERVED. Every written beat keeps the source chunk it came
# from, appended verbatim. A buyer can check any line against their own tape.
# The model is told to use only what is in the passage, so the deliverable is
# compression, not invention.
# ---------------------------------------------------------------------------

BEAT_BRIEF = {
    "HOOK": "an opening hook, 2 sentences max, that makes someone stop scrolling",
    "BUILD_TRUTH": "the setup, 3-4 sentences, plain and concrete",
    "BUILD_FUTURE": "the escalation, 3-4 sentences, raising the stakes",
    "COLLISION": "the turn, 3-4 sentences, where the idea pays off",
    "RESOLUTION": "the closing line or two, landing it",
}


def _llm_models(base):
    req = urllib.request.Request(base + "/models")
    with urllib.request.urlopen(req, timeout=20) as r:
        return [m["id"] for m in json.loads(r.read().decode("utf-8")).get("data", [])]


def _llm_write(base, model, beat, text):
    brief = BEAT_BRIEF.get(beat, "a short spoken beat")
    # The brief goes in the SYSTEM role, never the user turn. A small model
    # given "WRITE: an opening hook" in the user message reliably answers with
    # "An opening hook..." as its first line -- it reads the instruction as
    # content to paraphrase. Keeping the user turn as nothing but the passage
    # removes the thing it was echoing.
    system = (
        "You rewrite raw transcript into spoken short-form video narration.\n"
        "The user message is a transcript passage. Rewrite it as %s.\n\n"
        "RULES:\n"
        "- Use ONLY facts present in the passage. Invent nothing.\n"
        "- Strip filler: 'okay', 'does that make sense', 'guys', 'um', 'so again'.\n"
        "- Strip anything about a class, lecture, exam, book title or audience.\n"
        "- Short declarative sentences.\n"
        "- Never describe what you are writing. Never restate these "
        "instructions. Never open with 'The hook' or 'This passage'.\n"
        "- Output the narration text and nothing else." % brief
    )
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": text[:2400]}],
        "temperature": 0.7,
        "max_tokens": 320,
    }).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer local"})
    with urllib.request.urlopen(req, timeout=180) as r:
        doc = json.loads(r.read().decode("utf-8"))
    return (doc["choices"][0]["message"]["content"] or "").strip()

@dataclass
class ScriptPhase:
    name: str
    content: str
    source_title: str
    arcs: List[str]

class ScriptCompiler:
    def __init__(self, chunks_path: Path, write_base=None, write_model=None):
        self.chunks = []
        self.used_ids = set()
        self.write_base = write_base
        self.write_model = write_model
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

        if self.write_base:
            return self._compile_written(phases, mode, style)

        script = f"--- WENDIGO NARRATIVE COMPILATION [Mode: {mode.upper()} | Style: {style.upper()}] ---\n\n"
        for p in phases:
            script += f"[{p.name}] (Source: {p.source_title})\n"
            script += f"Arcs: {', '.join(p.arcs)}\n"
            script += f"> {p.content.strip()}\n\n"

        diags = { "mode": mode, "total_script_chars": len(script) }
        return script, diags

    def _compile_written(self, phases, mode, style):
        """Selected beats, rewritten as narration. Sources kept for audit."""
        written = []
        failed = 0
        for p in phases:
            try:
                out = _llm_write(self.write_base, self.write_model, p.name, p.content)
            except Exception as exc:
                out = ""
                failed += 1
                print("[!] %s: write failed (%s)" % (p.name, exc))
            # An empty rewrite falls back to the raw passage rather than
            # silently shipping a gap the buyer would find.
            written.append((p, out or p.content.strip(), bool(out)))

        script = "--- NARRATIVE SCRIPT [%s / %s] ---\n\n" % (
            mode.upper(), style.upper())
        for p, text, ok in written:
            script += "[%s]%s\n%s\n\n" % (
                p.name, "" if ok else "  (RAW - rewrite failed)", text)

        script += "\n--- SOURCE PROVENANCE ---\n"
        script += "Every beat above is compressed from the passage below it.\n"
        script += "Check any line against your own tape.\n\n"
        for p, _, _ in written:
            script += "[%s] source: %s\n> %s\n\n" % (
                p.name, p.source_title, p.content.strip())

        diags = {"mode": mode, "written_by": self.write_model,
                 "beats": len(written), "rewrite_failures": failed,
                 "total_script_chars": len(script)}
        return script, diags

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--mode", choices=["retention", "fracture"], default="retention")
    parser.add_argument("--style", choices=["aggressive", "humanist"], default="aggressive")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write", action="store_true",
                        help="Rewrite selected beats into narration with a local model")
    parser.add_argument("--llm-url", default=os.environ.get(
        "LOCAL_LLM_URL", "http://127.0.0.1:1234/v1"))
    parser.add_argument("--llm-model", default=os.environ.get("LOCAL_LLM_MODEL", ""))
    parser.add_argument("--count", type=int, default=1,
                        help="How many scripts to produce")
    args = parser.parse_args()

    base = model = None
    if args.write:
        base = args.llm_url.rstrip("/")
        model = args.llm_model
        if not model:
            try:
                avail = _llm_models(base)
            except Exception as exc:
                raise SystemExit(
                    "[X] --write needs an OpenAI-compatible server at %s (%s).\n"
                    "    Start LM Studio, or pass --llm-url / --llm-model."
                    % (base, exc))
            if not avail:
                raise SystemExit("[X] %s reports no models loaded." % base)
            model = avail[0]
        print("[*] writing with %s" % model)

    if args.count > 1:
        compiler = ScriptCompiler(args.chunks, base, model)
        outs = []
        for i in range(1, args.count + 1):
            s, d = compiler.compile(mode=args.mode, style=args.style)
            p = args.out.parent / ("%s_%02d%s" % (args.out.stem, i, args.out.suffix))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(s + "\n\n[DIAGNOSTICS]\n" + json.dumps(d, indent=2),
                         encoding="utf-8")
            outs.append(p)
            print("[OK] %d/%d -> %s" % (i, args.count, p))
        print("[DONE] %d scripts" % len(outs))
        return

    compiler = ScriptCompiler(args.chunks, base, model)
    script, diags = compiler.compile(mode=args.mode, style=args.style)
    script += f"\n\n[DIAGNOSTICS]\n{json.dumps(diags, indent=2)}"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(script, encoding="utf-8")
    print(f"[OK] Script saved to: {args.out}")

if __name__ == "__main__":
    main()
