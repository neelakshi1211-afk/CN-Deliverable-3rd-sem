import argparse, csv, json, ipaddress, subprocess
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = Path(__file__).with_name('index.html')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HTML.parent), **kwargs)

    def send_json(self, obj, status=200):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith('/api/status'):
            self.status_api(); return
        if self.path == '/' or self.path.startswith('/index.html'):
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/block' and self.path != '/api/unblock':
            self.send_json({'ok': False, 'error': 'Unknown action'}, 404); return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            payload = json.loads(self.rfile.read(length) or b'{}')
            source = str(ipaddress.IPv4Address(payload.get('source', '')))
            cmd = ['python3', str(ROOT/'person2_switch_control'/'switch_control.py'),
                   'block' if self.path.endswith('block') and not self.path.endswith('unblock') else 'unblock',
                   '--bridge', self.server.bridge, '--source', source]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if result.returncode:
                self.send_json({'ok': False, 'error': result.stderr.strip() or result.stdout.strip()}, 500)
            else:
                self.send_json({'ok': True, 'message': result.stdout.strip()})
        except Exception as exc:
            self.send_json({'ok': False, 'error': str(exc)}, 400)

    def status_api(self):
        csv_path, alerts_path, response_path = self.server.csv_path, self.server.alerts_path, self.server.response_path
        rows, alerts, responses = [], [], []
        try:
            if csv_path.exists():
                with csv_path.open(newline='', encoding='utf-8') as f:
                    rows = list(csv.DictReader(f))[-100:]
        except Exception: pass
        for path, target in ((alerts_path, alerts), (response_path, responses)):
            try:
                if path.exists():
                    target.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip())
            except Exception: pass
        flows, flow_error = [], None
        try:
            raw = subprocess.run(['ovs-ofctl','-O','OpenFlow13','dump-flows',self.server.bridge], capture_output=True, text=True, timeout=3)
            if raw.returncode: flow_error = raw.stderr.strip()
            else:
                import re
                for line in raw.stdout.splitlines():
                    if 'n_packets=' not in line: continue
                    def val(key):
                        m = re.search(r'(?:^|[, ])'+key+r'=([^, ]+)', line)
                        return m.group(1) if m else '-'
                    flows.append({'packets': val('n_packets'), 'bytes': val('n_bytes'), 'priority': val('priority'),
                                  'source': val('nw_src'), 'action': line.split('actions=',1)[-1].strip() if 'actions=' in line else '-'})
        except Exception as exc: flow_error = str(exc)
        self.send_json({'connections': rows, 'alerts': alerts[-30:], 'responses': responses[-30:], 'flows': flows,
                        'flow_error': flow_error, 'connection_count': len(rows), 'alert_count': len(alerts)})

    def log_message(self, fmt, *args):
        pass

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1'); p.add_argument('--port', type=int, default=8765)
    p.add_argument('--bridge', default='s1'); p.add_argument('--csv', default='/tmp/sdn_traffic.csv')
    p.add_argument('--alerts', default='/tmp/sdn_alerts.jsonl'); p.add_argument('--responses', default='/tmp/sdn_responses.jsonl')
    a = p.parse_args()
    server = ThreadingHTTPServer((a.host, a.port), Handler)
    server.bridge = a.bridge; server.csv_path = Path(a.csv); server.alerts_path = Path(a.alerts); server.response_path = Path(a.responses)
    print(f'[DASHBOARD] Open http://{a.host}:{a.port}', flush=True)
    server.serve_forever()

if __name__ == '__main__': main()
