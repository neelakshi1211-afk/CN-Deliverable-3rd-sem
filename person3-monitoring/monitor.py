import argparse
import csv
import os
import subprocess
import time
from datetime import datetime


def get_tcp_connections():
    """
    Read the current TCP connection table using the system's `ss` command.
    This reports socket connection metadata, not packet contents.
    Intended for use on the Ubuntu VM/Mininet environment.
    """
    try:
        result = subprocess.run(
            ["ss", "-tn"],
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        raise RuntimeError("The 'ss' command was not found. Install iproute2.")
    except subprocess.CalledProcessError as error:
        raise RuntimeError(error.stderr.strip() or "Could not read TCP connections.")

    connections = []

    for line in result.stdout.splitlines()[1:]:
        fields = line.split()
        if len(fields) < 4:
            continue

        state = fields[0]
        local_address = fields[-2]
        peer_address = fields[-1]

        # Ignore rows without a useful peer endpoint.
        if peer_address in ("*", "*:*"):
            continue

        connections.append({
            "state": state,
            "local": local_address,
            "peer": peer_address
        })

    return connections


def main():
    parser = argparse.ArgumentParser(
        description="Log TCP connection metadata visible on this machine."
    )
    parser.add_argument(
        "--interval", type=float, default=2.0,
        help="Seconds between checks (default: 2)"
    )
    parser.add_argument(
        "--output", default="traffic_log.csv",
        help="CSV output filename (default: traffic_log.csv)"
    )
    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    file_exists = os.path.exists(args.output)

    with open(args.output, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["timestamp", "state", "local_endpoint", "peer_endpoint"]
        )
        if not file_exists or os.path.getsize(args.output) == 0:
            writer.writeheader()

        print("TCP connection monitor started.")
        print("Checking connections visible to this machine.")
        print("Press Ctrl+C to stop.")
        print("Output file:", args.output)

        try:
            while True:
                timestamp = datetime.now().isoformat(timespec="seconds")
                connections = get_tcp_connections()

                if not connections:
                    print(f"[{timestamp}] No TCP connections currently listed.")
                else:
                    for connection in connections:
                        row = {
                            "timestamp": timestamp,
                            "state": connection["state"],
                            "local_endpoint": connection["local"],
                            "peer_endpoint": connection["peer"]
                        }
                        writer.writerow(row)
                        print(
                            f"[{timestamp}] {row['state']} | "
                            f"{row['local_endpoint']} <-> {row['peer_endpoint']}"
                        )
                    csv_file.flush()

                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
