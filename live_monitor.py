import argparse,csv,ipaddress,json,subprocess,time
from collections import defaultdict,deque
from datetime import datetime,timezone
from pathlib import Path
def get_ip(endpoint):
    try: return str(ipaddress.ip_address(endpoint.rsplit(":",1)[0]))
    except ValueError: return None
def main():
    p=argparse.ArgumentParser(description="Person 3: live TCP monitor and rate detector")
    p.add_argument("--interval",type=float,default=.2); p.add_argument("--threshold",type=int,default=5); p.add_argument("--window",type=float,default=10); p.add_argument("--csv",default="/tmp/sdn_traffic.csv"); p.add_argument("--alerts",default="/tmp/sdn_alerts.jsonl"); a=p.parse_args()
    if a.interval<=0 or a.window<=0 or a.threshold<1: p.error("interval/window must be positive; threshold must be >=1")
    cp,ap=Path(a.csv),Path(a.alerts); cp.parent.mkdir(parents=True,exist_ok=True); ap.parent.mkdir(parents=True,exist_ok=True)
    queues=defaultdict(deque); seen=set(); alerted={}
    with cp.open("a",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["timestamp_utc","state","local_endpoint","peer_endpoint"])
        if cp.stat().st_size==0: w.writeheader()
        print("[PERSON 3] Monitoring started",flush=True)
        try:
            while True:
                out=subprocess.run(["ss","-H","-tn"],capture_output=True,text=True,check=True).stdout
                current={}
                for line in out.splitlines():
                    x=line.split()
                    if len(x)>=4 and x[-1] not in ("*","*:*"): current[(x[-2],x[-1])]=(x[0],x[-2],x[-1])
                now=time.time(); stamp=datetime.now(timezone.utc).isoformat(timespec="seconds")
                for key,(state,local,peer) in current.items():
                    w.writerow({"timestamp_utc":stamp,"state":state,"local_endpoint":local,"peer_endpoint":peer})
                    if key not in seen:
                        src=get_ip(local)
                        if src:
                            q=queues[src]; q.append(now)
                            while q and now-q[0]>a.window: q.popleft()
                            if len(q)>=a.threshold and now-alerted.get(src,0)>=a.window:
                                event={"timestamp_utc":stamp,"event":"HIGH_CONNECTION_RATE","source":src,"connection_count":len(q),"threshold":a.threshold,"window_seconds":a.window,"severity":"warning"}
                                with ap.open("a",encoding="utf-8") as af: af.write(json.dumps(event)+"\n"); af.flush()
                                print("[PERSON 3] ALERT "+json.dumps(event),flush=True); alerted[src]=now; q.clear()
                f.flush(); seen=set(current); time.sleep(a.interval)
        except KeyboardInterrupt: print("[PERSON 3] Monitoring stopped",flush=True)
if __name__=="__main__": main()
