import subprocess
import os
import sys
import time

def boot():
    print("[WENDIGO-BRIDGE] Infiltrating PowerShell execution blocks...")
    
    env = os.environ.copy()
    env["DATABASE_URL"] = "mock://localhost"
    env["REDIS_URL"] = "mock://localhost"
    
    # Path to the actual node.exe to bypass .ps1 wrappers
    node_exe = "node.exe" 
    # Path to tsx entry point - we'll find it in node_modules
    tsx_path = "wendigo-cis/node_modules/tsx/dist/cli.mjs"

    def start_service(name, path):
        print(f"[WENDIGO-BRIDGE] Booting {name}...")
        return subprocess.Popen(
            [node_exe, tsx_path, path],
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )

    try:
        ingress = start_service("INGRESS", "wendigo-cis/apps/ingress-api/src/index.ts")
        time.sleep(2)
        orchestrator = start_service("ORCHESTRATOR", "wendigo-cis/apps/orchestrator/src/index.ts")
        time.sleep(2)
        worker = start_service("WORKER", "wendigo-cis/apps/worker/src/index.ts")

        print("[WENDIGO-BRIDGE] Cluster is breathing. Awaiting trapdoor...")
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[WENDIGO-BRIDGE] Shutting down...")
        ingress.terminate()
        orchestrator.terminate()
        worker.terminate()

if __name__ == "__main__":
    boot()
