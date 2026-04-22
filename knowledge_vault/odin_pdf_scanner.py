import os
import PyPDF2
from pathlib import Path

# --- CONFIG ---
SOURCE_DIR = r"D:\terryyu"
VAULT_DIR = Path("knowledge_vault")
ESOTERIC_FILE = VAULT_DIR / "esoteric_essence.txt"

TARGET_PDFS = [
    "the-geometry-of-proton-and-the-tetryen-shape-v1-1+(1).pdf",
    "Living_Energies_Viktor_Schauberger_Callum_Coats.pdf",
    "hyperbolic+curvilinear+lattice+space1.pdf",
    "vACUUM_FLUX.pdf"
]

def scan_pdfs():
    print(f"[*] ODIN Scanning Esoteric PDFs in {SOURCE_DIR}...")
    
    with open(ESOTERIC_FILE, 'w', encoding='utf-8') as out:
        out.write("# ODIN ESOTERIC PHYSICS DISTILLATION\n\n")
        
        for pdf_name in TARGET_PDFS:
            pdf_path = os.path.join(SOURCE_DIR, pdf_name)
            if not os.path.exists(pdf_path):
                print(f"[!] PDF not found: {pdf_name}")
                continue
                
            print(f"[*] Ripping: {pdf_name}")
            out.write(f"## SOURCE: {pdf_name}\n\n")
            
            try:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    # We grab first 20 pages to get the core concepts/abstracts
                    limit = min(20, len(reader.pages))
                    for i in range(limit):
                        text = reader.pages[i].extract_text()
                        if text:
                            # Filter for high-value keywords
                            # (Heuristic: search for equations, geometric terms, or definitions)
                            out.write(text.strip() + "\n")
                        if i % 5 == 0:
                            print(f"    - Page {i} complete")
            except Exception as e:
                print(f"[!] Error reading {pdf_name}: {e}")
                
            out.write("\n---\n")

    print(f"[+] ESOTERIC SCAN COMPLETE. Secrets saved to: {ESOTERIC_FILE}")

if __name__ == "__main__":
    scan_pdfs()
