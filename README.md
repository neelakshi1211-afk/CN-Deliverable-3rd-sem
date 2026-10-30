# Person 3 — CN/SDN D2 Monitoring and Detection

## Files
- `monitor.py`: reads TCP connection metadata visible in the Linux network namespace where it runs and appends observations to CSV.
- `detector.py`: detects a high rate of events from JSONL input and emits `HIGH_CONNECTION_RATE` alerts.
- `test_monitor.py`: unit tests for the detector.
- `sample_events.jsonl`: synthetic test data.
- `requirements.txt`: no third-party packages.

## Requirements
Python 3 on Ubuntu/Linux. `monitor.py` requires `ss` (usually provided by `iproute2`).

## Test detection logic (simulated events)
```bash
python3 -m unittest -v test_monitor.py
python3 detector.py --input sample_events.jsonl --threshold 5 --window 10 --output alerts.jsonl
```
These are synthetic events, not live Mininet results.

## Run connection monitor
```bash
python3 monitor.py --interval 1 --output traffic_log.csv
```
Stop with Ctrl+C. The script sees only connections visible in its current network namespace. In Mininet CLI, inspect a host's socket table with `h1 ss -tn`.

## Integration status and limitations
The detector expects JSONL events with numeric `timestamp` and a `source` value, e.g. `{"timestamp": 100.0, "source": "10.0.0.1"}`. The current monitor does not yet generate that JSONL stream or call the detector automatically; live integration must be implemented and tested against the team's actual setup. No SDN controller API is assumed because the team's controller is not yet known. An alert alone does not block traffic. Use only in your own Mininet lab; this is metadata monitoring, not packet-payload inspection.
