#!/usr/bin/env python3
import argparse
import csv
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from detector import ConnectionRateDetector


def read_connections():
    result = subprocess.run(
        ["ss", "-H", "-tn"],
        capture_output=True,
        text=True,
        check=True
    )

    connections = {}

    for line in result.stdout.splitlines():
        fields = line.split()

        if len(fields) < 4 or fields[-1] in ("*", "*:*"):
            continue

        state, local, peer = fields[0], fields[-2], fields[-1]

        connections[(local, peer)] = {
            "state": state,
            "local_endpoint": local,
            "peer_endpoint": peer
        }

    return connections


def source_ip(endpoint):
    if endpoint.startswith("[") and "]:" in endpoint:
        return endpoint[1:endpoint.rfind("]:")]

    return endpoint.rsplit(":", 1)[0] if ":" in endpoint else endpoint


def main():
    parser = argparse.ArgumentParser(
        description="Monitor TCP metadata and detect high connection rates."
    )
    parser.add_argument("--interval", type=float, default=1)
    parser.add_argument("--threshold", type=int, default=5)
    parser.add_argument("--window", type=float, default=10)
    parser.add_argument("--output", default="/tmp/traffic_log.csv")
    parser.add_argument("--alerts", default="/tmp/alerts.jsonl")
    args = parser.parse_args()

    if args.interval <= 0 or args.threshold < 1 or args.window <= 0:
        parser.error(
            "interval and window must be positive; threshold must be at least 1"
        )

    csv_path = Path(args.output)
    alert_path = Path(args.alerts)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    alert_path.parent.mkdir(parents=True, exist_ok=True)

    new_file = not csv_path.exists() or csv_path.stat().st_size == 0

    detector = ConnectionRateDetector(
        args.threshold,
        args.window,
        alert_path
    )

    seen = set()

    with csv_path.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "timestamp_utc",
                "state",
                "local_endpoint",
                "peer_endpoint"
            ]
        )

        if new_file:
            writer.writeheader()

        print(
            f"Live monitor + detector started. "
            f"CSV: {csv_path}; alerts: {alert_path}"
        )
        print("Press Ctrl+C to stop.")

        try:
            while True:
                now = time.time()
                timestamp_utc = datetime.now(
                    timezone.utc
                ).isoformat(timespec="seconds")

                current = read_connections()

                for key, connection in current.items():
                    writer.writerow({
                        "timestamp_utc": timestamp_utc,
                        **connection
                    })

                    if key not in seen:
                        detector.process({
                            "timestamp": now,
                            "source": source_ip(
                                connection["local_endpoint"]
                            )
                        })

                csvfile.flush()
                seen = set(current)

                time.sleep(args.interval)

        except KeyboardInterrupt:
            print(
                f"\nMonitoring stopped. "
                f"Alerts generated this run: {detector.alert_count}"
            )


if __name__ == "__main__":
    main()
