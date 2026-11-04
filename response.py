import argparse,ipaddress,json,subprocess,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description="Person 4: alert-to-OVS integration"); p.add_argument("--alerts",default="/tmp/sdn_alerts.jsonl"); p.add_argument("--bridge",default="s1"); p.add_argument("--poll",type=float,default=.2); p.add_argument("--log",default="/tmp/sdn_responses.jsonl"); a=p.parse_args()
    path=Path(a.alerts); offset=0; handled=set(); script=Path(__file__).resolve().parents[1]/"person2_switch_control"/"switch_control.py"
    print("[PERSON 4] Waiting for Person 3 alerts",flush=True)
    while True:
        if path.exists():
            with path.open(encoding="utf-8") as f:
                f.seek(offset)
                for line in f:
                    try:
                        e=json.loads(line)
                        if e.get("event")!="HIGH_CONNECTION_RATE": continue
                        src=str(ipaddress.IPv4Address(e["source"])); ident=(src,e.get("timestamp_utc"))
                        if ident in handled: continue
                        r=subprocess.run(["python3",str(script),"block","--bridge",a.bridge,"--source",src],text=True,capture_output=True)
                        if r.returncode==0:
                            record={"timestamp_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"action":"BLOCK","source":src,"alert_timestamp_utc":e.get("timestamp_utc")}
                            with open(a.log,"a",encoding="utf-8") as log: log.write(json.dumps(record)+"\n"); log.flush()
                            print(f"[PERSON 4] Alert received; requested switch block for {src}",flush=True); handled.add(ident)
                        else: print("[PERSON 4] Switch command failed: "+r.stderr.strip(),flush=True)
                    except (ValueError,KeyError,json.JSONDecodeError) as ex: print(f"[PERSON 4] Ignored invalid alert: {ex}",flush=True)
                offset=f.tell()
        time.sleep(a.poll)
if __name__=="__main__": main()
