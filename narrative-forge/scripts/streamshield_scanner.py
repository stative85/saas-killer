# streamshield_scanner.py
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class RiskSignal:
    timestamp: str
    signal_type: str
    evidence: str
    severity: str

class StreamShield:
    def __init__(self, srt_path: Path):
        self.srt_path = srt_path
        self.signals = []
        # Detection Targets from Spec
        self.music_patterns = [r"\[Music\]", r"\[Song\]", r"♪", r"\(Music Playing\)"]
        self.panic_keywords = ["DMCA", "STRIKE", "RIP VOD", "MUTE", "COPYRIGHT"]
        self.self_report = ["turn that off", "copyrighted"]

    def parse_srt(self):
        print(f"[*] Scanning VOD Armor: {self.srt_path.name}")
        content = self.srt_path.read_text(encoding="utf-8", errors="replace")
        
        # Split into SRT blocks
        blocks = content.split("\n\n")
        
        for block in blocks:
            lines = block.splitlines()
            if len(lines) < 3: continue
            
            timestamp_range = lines[1]
            text = " ".join(lines[2:])
            
            # Check for Convergence
            current_signals = []
            
            if any(re.search(p, text, re.I) for p in self.music_patterns):
                current_signals.append("MUSIC_CUE")
            
            if any(k in text.upper() for k in self.panic_keywords):
                current_signals.append("CHAT_PANIC")
                
            if any(s in text.lower() for s in self.self_report):
                current_signals.append("SELF_REPORT")

            # Severity Logic from v0.2 Spec
            if current_signals:
                sev = "LOW"
                if len(current_signals) == 2: sev = "MEDIUM"
                if len(current_signals) >= 3: sev = "HIGH"
                
                self.signals.append(RiskSignal(
                    timestamp=timestamp_range,
                    signal_type="|".join(current_signals),
                    evidence=text.strip(),
                    severity=sev
                ))

    def generate_report(self, out_path: Path):
        report = f"# 🛡️ STREAMSHIELD RISK REPORT - {self.srt_path.name}\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        high_risk = [s for s in self.signals if s.severity == "HIGH"]
        report += f"## 🚨 CRITICAL CONVERGENCE: {len(high_risk)} zones\n"
        for s in high_risk:
            report += f"- **{s.timestamp}**: {s.evidence} (Signals: {s.signal_type})\n"
            
        report += "\n## 📊 FULL SCAN LOG\n"
        for s in self.signals:
            report += f"| {s.severity} | {s.timestamp} | {s.signal_type} |\n"
            
        out_path.write_text(report, encoding="utf-8")
        print(f"[✅] Risk Report Generated: {out_path}")

def main():
    # Target the Gemini Workspace VODs
    ws_path = Path(r"C:\Users\cleve\Downloads\CLI\GEMINI WORKSPACE")
    vods = list(ws_path.glob("*.srt"))
    
    for vod in vods:
        shield = StreamShield(vod)
        shield.parse_srt()
        
        report_p = Path(f"outputs/risk/report_{vod.stem}.md")
        report_p.parent.mkdir(parents=True, exist_ok=True)
        shield.generate_report(report_p)

if __name__ == "__main__":
    main()
