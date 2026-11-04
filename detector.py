import argparse,json
from collections import defaultdict,deque
from datetime import datetime,timezone
def detect(events,threshold,window):
    qmap=defaultdict(deque); alerts=[]
    for e in events:
        src=e.get("source"); t=e.get("timestamp")
        if not src or t is None: continue
        q=qmap[src]; q.append(float(t))
        while q and float(t)-q[0]>window: q.popleft()
        if len(q)==threshold: alerts.append({"event":"HIGH_CONNECTION_RATE","source":src,"connection_count":len(q),"threshold":threshold,"window_seconds":window,"severity":"warning"})
    return alerts
def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--threshold",type=int,default=5); p.add_argument("--window",type=float,default=10); p.add_argument("--output",default="alerts.jsonl"); a=p.parse_args()
    if a.threshold<1 or a.window<=0: p.error("threshold >=1 and window >0 required")
    events=[json.loads(x) for x in open(a.input,encoding="utf-8") if x.strip()]
    alerts=detect(events,a.threshold,a.window)
    with open(a.output,"w",encoding="utf-8") as f:
        for e in alerts: e["timestamp_utc"]=datetime.now(timezone.utc).isoformat(timespec="seconds"); f.write(json.dumps(e)+"\n")
    print(f"[PERSON 3] {len(events)} events processed; {len(alerts)} alert(s) written to {a.output}")
if __name__=="__main__": main()
