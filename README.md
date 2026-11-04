# SDN / Mininet D2 — Complete Four-Person Demo

This package is organized by the four team members and connects their D2 modules.

## Architecture choice

This runnable version uses **Mininet + Open vSwitch + ovs-ofctl**, without Ryu. Person 3's monitoring/detection code remains controller-independent. Person 2 installs switch flow rules through OVS commands. Person 4 connects Person 3's alert file to Person 2's switch-control command.

## Who does what

| Person | D2 responsibility | Files | Evidence |
|---|---|---|---|
| 1 | TCP server and traffic generation | `person1_traffic/server.py`, `client.py` | h3 listens on TCP 9000; h1 creates repeated connections |
| 2 | SDN switch control and flow rules | `person2_switch_control/switch_control.py` | OVS forwarding flow, drop rule, flow-table output |
| 3 | Traffic monitoring and rate detection | `person3_monitor_detection/live_monitor.py`, `detector.py` | CSV connection log and JSONL high-rate alert |
| 4 | Integration and automated response | `person4_integration/response.py`, `run_demo.py` | Reads Person 3 alerts and asks Person 2 module to install source-IP drop rule |

**Person 3 does not use Ryu.** Person 2's OVS flow-rule code is the switch-control component in this version. Person 4 is the glue between detection and switch action.

## Requirements

Use an Ubuntu VM with Mininet and Open vSwitch installed. The Python code uses only the standard library.
```bash
sudo mn --version
ovs-ofctl --version
python3 --version
```

## Run the entire demo

Extract the ZIP, open a normal Ubuntu terminal in the extracted folder, then run:
```bash
sudo python3 run_demo.py
```
The script creates h1 (`10.0.0.1`), h2 (`10.0.0.2`), h3 (`10.0.0.3`) and s1. It starts the TCP server on h3:9000, starts Person 3's live monitor on h1, starts Person 4's alert watcher, and generates eight TCP connections from h1. It then displays the CSV, alerts and OVS flow table. A live web dashboard is also started at **http://127.0.0.1:8765** inside the Ubuntu VM. Open Firefox/Chromium in the VM and visit that address while the demo is running. The dashboard reads the real CSV, alert, response and OVS flow-table data. Press Enter in the terminal to clean up; this also stops the dashboard.

## Manual run (if needed)

Start Mininet:
```bash
sudo mn -c
sudo mn --topo single,3 --controller none --switch ovsbr
```
In a normal terminal, from the project folder:
```bash
sudo python3 person2_switch_control/switch_control.py init --bridge s1
```
At the `mininet>` prompt, start Person 1's server and Person 3's monitor. Replace `/ABSOLUTE/PATH/sdn_d2_complete` with the actual extracted path:
```text
h3 python3 /ABSOLUTE/PATH/sdn_d2_complete/person1_traffic/server.py --port 9000 &
h1 python3 /ABSOLUTE/PATH/sdn_d2_complete/person3_monitor_detection/live_monitor.py --interval 0.15 --threshold 5 --window 10 --csv /tmp/sdn_traffic.csv --alerts /tmp/sdn_alerts.jsonl &
```
In a second normal terminal, start Person 4:
```bash
sudo python3 /ABSOLUTE/PATH/sdn_d2_complete/person4_integration/response.py --alerts /tmp/sdn_alerts.jsonl --bridge s1
```
At `mininet>` generate traffic:
```text
h1 python3 /ABSOLUTE/PATH/sdn_d2_complete/person1_traffic/client.py --host 10.0.0.3 --port 9000 --count 8 --hold 0.6 --delay 0.1
```
Inspect Person 3 output:
```text
h1 cat /tmp/sdn_traffic.csv
h1 cat /tmp/sdn_alerts.jsonl
```
Inspect Person 2's switch rules in a normal terminal:
```bash
sudo python3 person2_switch_control/switch_control.py show --bridge s1
```
Exit Mininet with `exit`.

## Test detector without Mininet
```bash
python3 -m unittest discover -s tests -v
```
Run sample JSONL:
```bash
python3 person3_monitor_detection/detector.py --input sample_events.jsonl --threshold 5 --window 10 --output sample_alerts.jsonl
cat sample_alerts.jsonl
```

## Dashboard

The `dashboard/` folder contains a standard-library Python web server and the dashboard page. No Flask, Node.js, npm, or extra pip packages are required. It displays the Mininet topology, live TCP observations, threshold alerts, Person 4 response records, OVS flow counters (packets/bytes), and source-IP block/unblock controls. The dashboard listens only on `127.0.0.1` and is intended to be opened in a browser inside the Ubuntu VM. Keep the `sudo python3 run_demo.py` terminal running while viewing it.

## Outputs
- `/tmp/sdn_traffic.csv`: Person 3 TCP metadata log.
- `/tmp/sdn_alerts.jsonl`: Person 3 high-connection-rate alerts.
- `/tmp/sdn_responses.jsonl`: Person 4 records of successful automatic block requests.
- `s1` flow table: Person 2 forwarding/drop rules, with Person 4 initiating the drop rule after an alert.

## Limitations
- `ss` reports TCP socket metadata visible in the network namespace where it runs; it does not inspect packet payloads.
- Polling can miss connections that begin and end between polls; the demo deliberately holds each connection open.
- The detector is a simple connection-rate demonstration, not a general-purpose attack classifier.
- The switch drop rule applies to the source IPv4 address in this isolated Mininet lab.
- The one-command demo requires Mininet and OVS already installed.
