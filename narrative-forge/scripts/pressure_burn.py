import requests
import concurrent.futures
import time

URL = "http://127.0.0.1:8000/api/run"
TOTAL = 100
CONCURRENCY = 10

def strike(i):
    try:
        start = time.time()
        # Use multipart/form-data as expected by FastAPI Form(...)
        r = requests.post(URL, data={'mode':'retention_aggressive', 'path': 'demo'}, timeout=20)
        end = time.time()
        return r.status_code, end - start
    except Exception as e:
        return 500, 0.0

def run_burn():
    print(f"[*] Igniting Phase 1 Burn ({TOTAL} strikes, C={CONCURRENCY})...")
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(strike, i): i for i in range(TOTAL)}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            if len(results) % 20 == 0:
                print(f"  [>] Progress: {len(results)}/{TOTAL}...")
            
    status_codes = [r[0] for r in results]
    latencies = [r[1] for r in results if r[0] == 200]
    
    p95 = sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0
    print(f"\n[💎] PHASE 1 BURN COMPLETE")
    print(f"  - 200 OK: {status_codes.count(200)}/{TOTAL}")
    print(f"  - 5xx Fail: {status_codes.count(500)}/{TOTAL}")
    print(f"  - p95 Latency: {p95:.2f}s")
    
if __name__ == "__main__":
    run_burn()
