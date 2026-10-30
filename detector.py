#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


class ConnectionRateDetector:
    def __init__(self, threshold, window, output):
        if threshold < 1 or window <= 0:
            raise ValueError("threshold must be >= 1 and window > 0")
        self.threshold = threshold
        self.window = window
        self.output = Path(output)
        self.recent = defaultdict(deque)
        self.alert_count = 0

    def process(self, event):
        try:
            timestamp = float(event["timestamp"])
            source = str(event["source"])
        except (KeyError, TypeError, ValueError):
            return False

        queue = self.recent[source]
        queue.append(timestamp)

        while queue and timestamp - queue[0] > self.window:
            queue.popleft()

        if len(queue) < self.threshold:
            return False

        alert = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": "HIGH_CONNECTION_RATE",
            "source": source,
            "connection_count": len(queue),
            "threshold": self.threshold,
            "window_seconds": self.window,
            "severity": "warning"
        }

        self.output.parent.mkdir(parents=True, exist_ok=True)

        with self.output.open("a", encoding="utf-8") as f:
            f.write(json.dumps(alert) + "\n")

        print("ALERT:", json.dumps(alert))
        self.alert_count += 1
        queue.clear()
        return True


def detect_events(events, threshold, window, output):
    detector = ConnectionRateDetector(threshold, window, output)

    for event in events:
        detector.process(event)

    return detector.alert_count


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    print("Skipping invalid JSON line:", line.rstrip())


def main():
    parser = argparse.ArgumentParser(
        description="Detect high connection-event rates from JSONL."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--threshold", type=int, default=10)
    parser.add_argument("--window", type=float, default=10)
    parser.add_argument("--output", default="alerts.jsonl")
    args = parser.parse_args()

    if args.threshold < 1 or args.window <= 0:
        parser.error("threshold must be >=1 and window >0")

    count = detect_events(
        read_jsonl(Path(args.input)),
        args.threshold,
        args.window,
        Path(args.output)
    )

    print(f"Finished. Alerts written: {count}")


if __name__ == "__main__":
    main()
