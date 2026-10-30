#!/usr/bin/env python3
"""Basic TCP connection-table monitor for a controlled Ubuntu/Mininet lab."""
import argparse, csv, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

def read_tcp_connections():
    result = subprocess.run(["ss", "-H", "-tn"], capture_output=True, text=True, check=True)
    rows = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[-1] not in ("*", "*:*"):
            rows.append({"state": fields[0], "local_endpoint": fields[-2], "peer_endpoint": fields[-1]})
    return rows

def main():
    parser = argparse.ArgumentParser(description="Log visible TCP connection metadata.")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--output", default="traffic_log.csv")
    args = parser.parse_args()
    if args.interval <= 0: parser.error("--interval must be positive")
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    new_file = not output.exists() or output.stat().st_size == 0
    with output.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp_utc","state","local_endpoint","peer_endpoint"])
        if new_file: writer.writeheader()
        print(f"Monitoring TCP metadata. Output: {output.resolve()}. Press Ctrl+C to stop.")
        try:
            while True:
                timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
                connections = read_tcp_connections()
                if not connections: print(f"[{timestamp}] No peer TCP connections visible.")
                for c in connections:
                    writer.writerow({"timestamp_utc":timestamp, **c}); f.flush()
                    print(f"[{timestamp}] {c['state']} | {c['local_endpoint']} <-> {c['peer_endpoint']}")
                time.sleep(args.interval)
        except KeyboardInterrupt: print("\nMonitor stopped.")
if __name__ == "__main__": main()
