"""Simple CLI for the lab controller REST API (standard library only)."""
import argparse
import json
import urllib.request
import urllib.error


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['status', 'block', 'unblock', 'add-rule', 'remove-rule'])
    p.add_argument('--ip', help='IPv4 source to block/unblock')
    p.add_argument('--dpid', type=int, help='Switch ID for rule')
    p.add_argument('--src-ip', help='Rule source IPv4')
    p.add_argument('--dst-ip', help='Rule destination IPv4')
    p.add_argument('--out-port', type=int, help='Switch output port')
    p.add_argument('--controller', default='http://127.0.0.1:8080')
    a = p.parse_args()
    paths = {'status': '/api/status', 'block': '/api/block', 'unblock': '/api/unblock',
             'add-rule': '/api/rule', 'remove-rule': '/api/rule'}
    payload = None
    if a.action in ('block', 'unblock'):
        if not a.ip:
            p.error('--ip is required')
        payload = {'ip': a.ip}
    elif a.action in ('add-rule', 'remove-rule'):
        if any(x is None for x in (a.dpid, a.src_ip, a.dst_ip, a.out_port)):
            p.error('--dpid, --src-ip, --dst-ip and --out-port are required')
        payload = {'dpid': a.dpid, 'src_ip': a.src_ip, 'dst_ip': a.dst_ip, 'out_port': a.out_port}
    method = 'GET' if a.action == 'status' else 'DELETE' if a.action == 'remove-rule' else 'POST'
    request = urllib.request.Request(a.controller.rstrip('/') + paths[a.action],
       data=json.dumps(payload).encode() if payload is not None else None,
       headers={'Content-Type': 'application/json'}, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            print(response.read().decode())
    except urllib.error.HTTPError as exc:
        print('HTTP error:', exc.code, exc.read().decode())
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print('Connection error:', exc.reason)
        raise SystemExit(1)

if __name__ == '__main__':
    main()
