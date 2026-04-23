import json
from pathlib import Path

types = {
    'sprint_run_001': 'declarative',
    'sprint_run_002': 'declarative',
    'sprint_run_003': 'declarative',
    'sprint_run_004': 'confrontational',
    'sprint_run_005': 'question'
}

for rid, htype in types.items():
    p = Path(f'narrative-forge/outputs/feedback/{rid}_feedback.json')
    if p.exists():
        data = json.loads(p.read_text())
        # Apply strict schema update
        data['hook_type'] = htype
        data['avg_watch_time'] = 0
        data['impressions'] = 0
        data['ctr'] = 0.0
        with open(p, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[OK] Updated schema for {rid}")
