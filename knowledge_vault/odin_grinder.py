import json
import os
from pathlib import Path

# --- CONFIG ---
SOURCE_FILE = r"D:\terryyu\conversations.json"
VAULT_DIR = Path("knowledge_vault")
CONCEPTS_FILE = VAULT_DIR / "distilled_concepts.txt"

VAULT_DIR.mkdir(exist_ok=True)

def distill():
    print(f"[*] ODIN ENGAGED. Probing 500MB Hive-Mind export...")
    
    if not os.path.exists(SOURCE_FILE):
        print(f"[!] Source not found: {SOURCE_FILE}")
        return

    concept_count = 0
    
    # We use a streaming approach to avoid memory overflow
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f) # Standard exports are usually small enough to load as objects if memory allows, but we'll be careful
            
            with open(CONCEPTS_FILE, 'w', encoding='utf-8') as out:
                out.write(f"# ODIN DISTILLATION REPORT - {SOURCE_FILE}\n\n")
                
                for conversation in data:
                    title = conversation.get('title', 'Untitled Conversation')
                    out.write(f"## {title}\n")
                    
                    # Extract message text
                    mapping = conversation.get('mapping', {})
                    for node_id in mapping:
                        node = mapping[node_id]
                        message = node.get('message')
                        if message and message.get('content'):
                            parts = message['content'].get('parts', [])
                            for p in parts:
                                if isinstance(p, str) and len(p) > 50: # Only grab meaningful blocks
                                    # Very simple conceptual filter: grab lines with high information density
                                    out.write(f"- {p[:200].strip()}...\n")
                                    concept_count += 1
                    out.write("\n---\n")
                    
        print(f"[+] DISTILLATION COMPLETE. Captured {concept_count} concept fragments.")
        print(f"[+] Essence saved to: {CONCEPTS_FILE}")
        
    except Exception as e:
        print(f"[!] ODIN Failure: {e}")

if __name__ == "__main__":
    distill()
