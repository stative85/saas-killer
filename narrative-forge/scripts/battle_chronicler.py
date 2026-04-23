# battle_chronicler.py
import json
import argparse
from pathlib import Path
from datetime import datetime

def chronicle(log_path: Path, history_path: Path):
    print(f"[*] Chronicling battle: {log_path.name}")
    
    events = []
    with open(log_path, "r") as f:
        for line in f:
            events.append(json.loads(line))

    if not events:
        print("[!] Empty log.")
        return

    # ANALYSIS
    start_time = events[0]['timestamp']
    end_time = events[-1]['timestamp']
    
    # Track HP changes
    initial_hp = {a['id']: a['hp'] for a in events[0]['state']['agents']}
    final_hp = {a['id']: a['hp'] for a in events[-1]['state']['agents']}
    
    total_attacks = sum(1 for e in events if e['action'].get('attack', False))
    
    # FIND PEAK COMBAT (Largest HP drop in a single step)
    max_damage = 0
    peak_moment = ""
    for i in range(1, len(events)):
        for j, agent in enumerate(events[i]['state']['agents']):
            prev_hp = events[i-1]['state']['agents'][j]['hp']
            curr_hp = agent['hp']
            if prev_hp - curr_hp > max_damage:
                max_damage = prev_hp - curr_hp
                peak_moment = f"Agent {agent['id']} ({agent['type']}) suffered a massive hit."

    # NARRATIVE GENERATION
    report = f"""
## ⚔️ BATTLE REPORT: {log_path.stem}
- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Duration:** {len(events)} ticks
- **Intensity:** {total_attacks} attacks exchanged

### 🔬 Combat Analysis
- **The Crucible:** {peak_moment or "Stable maneuvering observed."}
- **Casualties:** {sum(1 for hp in final_hp.values() if hp <= 0)} fallen gladiators.

### 📝 Eternal Archive
> The silicon sands shifted as {total_attacks} elemental blasts illuminated the grid. 
> At the peak of resonance, {max_damage} units of structural integrity were stripped from the field.
> The session concluded at {end_time}.

---
"""
    
    with open(history_path, "a", encoding="utf-8") as f:
        f.write(report)
        
    print(f"[✅] BATTLE CHRONICLED TO: {history_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--history", type=Path, default="ARENA_HISTORY.md")
    args = parser.parse_args()
    
    chronicle(args.log, args.history)
