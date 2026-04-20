import argparse
import concurrent.futures
import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
QUERIES = Path("data/sample_queries.jsonl")


import random

def send_request(client: httpx.Client, payload: dict) -> None:
    try:
        # Chaos engineering: Thêm độ trễ bất kỳ từ 0.1s - 1.5s để giả lập mạng lag
        jitter = random.uniform(0.1, 1.5)
        time.sleep(jitter)
        
        start = time.perf_counter()
        r = client.post(f"{BASE_URL}/chat", json=payload)
        latency = (time.perf_counter() - start) * 1000
        
        status = r.status_code
        color = "\033[92m" if status == 200 else "\033[91m"
        reset = "\033[0m"
        
        print(f"{color}[HTTP {status}]{reset} | req_id: {r.json().get('correlation_id', 'N/A')} | {payload['feature']} | latency: {latency:.1f}ms | jitter: {jitter*1000:.0f}ms")
    except Exception as e:
        print(f"\033[91m[ERROR]\033[0m Request failed: {e}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent requests")
    args = parser.parse_args()

    lines = [line for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]
    
    with httpx.Client(timeout=30.0) as client:
        if args.concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = [executor.submit(send_request, client, json.loads(line)) for line in lines]
                concurrent.futures.wait(futures)
        else:
            for line in lines:
                send_request(client, json.loads(line))


if __name__ == "__main__":
    main()
