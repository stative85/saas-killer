import os
import re
import json
import argparse
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import datetime

@dataclass
class QualityMetrics:
    length_score: float
    repetition_score: float
    diversity_score: float
    punctuation_score: float
    structure_score: float
    quality_score: float
    quality_band: str

@dataclass
class TranscriptDocument:
    doc_id: str
    playlist_index: Optional[int]
    title: str
    source_path: Path
    raw_text: str

@dataclass
class ProcessedDocument:
    doc_id: str
    playlist_index: Optional[int]
    title: str
    source_path: Path
    clean_path: Path
    raw_text: str
    clean_text: str
    char_count: int
    word_count: int
    line_count: int
    quality: QualityMetrics

@dataclass
class ChunkRecord:
    chunk_id: str
    doc_id: str
    playlist_index: Optional[int]
    title: str
    text: str
    char_count: int
    word_count: int
    quality_score: float

def discover_transcripts(input_dir: Path) -> List[Path]:
    files = list(input_dir.glob("*.txt"))
    def sort_key(p: Path):
        # Sort by 001_ prefix if present
        match = re.match(r"^(\d+)_", p.name)
        if match: return (0, int(match.group(1)))
        return (1, p.name)
    return sorted(files, key=sort_key)

def parse_metadata(path: Path) -> Tuple[str, Optional[int], str]:
    # Match "001_Title.txt"
    match = re.match(r"^(\d+)[_-](.+)$", path.stem)
    if match:
        idx = int(match.group(1))
        title = match.group(2).replace("_", " ").strip()
        return (f"{idx:03d}", idx, title)
    return (path.stem, None, path.stem.replace("_", " "))

def clean_baseline(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[\u200b-\u200d\ufeff]", "", text) # Invisible chars
    text = re.sub(r"\n{3,}", "\n\n", text) # Collapse blank lines
    
    # Remove identical adjacent lines
    lines = text.split("\n")
    cleaned_lines = []
    prev = None
    for line in lines:
        curr = line.strip()
        if curr == prev and curr != "": continue
        cleaned_lines.append(line)
        prev = curr
    return "\n".join(cleaned_lines).strip()

def compute_quality(text: str) -> QualityMetrics:
    char_count = len(text)
    words = text.split()
    total_words = len(words)
    lines = [l for l in text.split("\n") if l.strip()]
    
    l_score = min(char_count / 8000.0, 1.0)
    
    # Repetition check
    repeat_count = 0
    for i in range(len(lines)-1):
        if lines[i].strip() == lines[i+1].strip(): repeat_count += 1
    rep_ratio = repeat_count / max(len(lines), 1)
    rep_score = 1.0 - min(rep_ratio * 2.0, 1.0)
    
    # Diversity
    unique = len(set(words))
    div_score = min(unique / max(total_words, 1) / 0.6, 1.0)
    
    # Punctuation
    puncs = len(re.findall(r'[.!?]', text))
    p_density = puncs / max(char_count, 1)
    p_score = min(p_density / 0.03, 1.0)
    
    # Structure (Avg line length heuristic)
    avg_line = char_count / max(len(lines), 1)
    s_score = min(avg_line / 100.0, 1.0)
    
    final = (0.3*l_score + 0.25*rep_score + 0.2*div_score + 0.15*p_score + 0.1*s_score)
    
    band = "trash"
    if final >= 0.8: band = "gold"
    elif final >= 0.65: band = "silver"
    elif final >= 0.45: band = "bronze"
    
    return QualityMetrics(l_score, rep_score, div_score, p_score, s_score, round(final, 2), band)

def chunk_document(doc: ProcessedDocument, size: int, overlap: int) -> List[ChunkRecord]:
    chunks = []
    text = doc.clean_text
    # Simple word-safe chunking for v0 skeleton
    words = text.split()
    step = size // 6 # rough word count
    over = overlap // 6
    
    for i in range(0, len(words), step - over):
        window = words[i : i + step]
        if not window: break
        chunk_text = " ".join(window)
        chunk_id = f"{doc.doc_id}_{(len(chunks)+1):04d}"
        chunks.append(ChunkRecord(
            chunk_id, doc.doc_id, doc.playlist_index, doc.title, 
            chunk_text, len(chunk_text), len(window), doc.quality.quality_score
        ))
    return chunks

def main():
    parser = argparse.ArgumentParser(description="POST HARVEST INDEXER")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--chunk-overlap", type=int, default=150)
    parser.add_argument("--min-chars", type=int, default=200)
    args = parser.parse_args()

    # Prep Dirs
    (args.output_dir / "cleaned").mkdir(parents=True, exist_ok=True)
    (args.output_dir / "merged").mkdir(parents=True, exist_ok=True)
    (args.output_dir / "index").mkdir(parents=True, exist_ok=True)
    (args.output_dir / "reports").mkdir(parents=True, exist_ok=True)

    files = discover_transcripts(args.input_dir)
    processed_docs = []
    all_chunks = []

    print(f"[*] Indexing {len(files)} files...")

    for f_path in files:
        with open(f_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read().strip()
        
        if len(raw) < args.min_chars:
            print(f"[-] Skipping {f_path.name} (Length: {len(raw)})")
            continue
            
        doc_id, idx, title = parse_metadata(f_path)
        clean = clean_baseline(raw)
        quality = compute_quality(clean)
        
        clean_path = args.output_dir / "cleaned" / f"{f_path.stem}.clean.txt"
        with open(clean_path, "w", encoding="utf-8") as f:
            f.write(clean)
            
        doc = ProcessedDocument(
            doc_id, idx, title, f_path, clean_path, raw, clean,
            len(clean), len(clean.split()), len(clean.split("\n")), quality
        )
        processed_docs.append(doc)
        all_chunks.extend(chunk_document(doc, args.chunk_size, args.chunk_overlap))

    # Writers
    with open(args.output_dir / "index" / "ledger.json", "w", encoding="utf-8") as f:
        json.dump([asdict(d) for d in processed_docs], f, indent=2, default=str)
    
    with open(args.output_dir / "index" / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(asdict(c)) + "\n")

    print(f"[+] Indexing Complete. {len(processed_docs)} indexed, {len(all_chunks)} chunks generated.")

if __name__ == "__main__":
    main()
