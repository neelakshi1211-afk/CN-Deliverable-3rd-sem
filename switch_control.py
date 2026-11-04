import argparse,ipaddress,subprocess,sys
def run(cmd):
    r=subprocess.run(cmd,text=True,capture_output=True)
    if r.returncode: raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r.stdout.strip()
def main():
    p=argparse.ArgumentParser(description="Person 2: OVS flow-rule control (no Ryu)")
    p.add_argument("action",choices=["init","block","unblock","show"]); p.add_argument("--bridge",default="s1"); p.add_argument("--source"); a=p.parse_args()
    try:
        if a.action=="init":
            run(["ovs-ofctl","-O","OpenFlow13","del-flows",a.bridge])
            run(["ovs-ofctl","-O","OpenFlow13","add-flow",a.bridge,"priority=0,actions=NORMAL"])
            print(f"[PERSON 2] {a.bridge} initialized with NORMAL forwarding")
        elif a.action=="show": print(run(["ovs-ofctl","-O","OpenFlow13","dump-flows",a.bridge]))
        else:
            if not a.source: p.error("--source is required")
            ip=str(ipaddress.IPv4Address(a.source))
            if a.action=="block":
                run(["ovs-ofctl","-O","OpenFlow13","add-flow",a.bridge,f"priority=200,ip,nw_src={ip},actions=drop"])
                print(f"[PERSON 2] Drop rule installed for {ip}")
            else:
                run(["ovs-ofctl","-O","OpenFlow13","del-flows",a.bridge,f"ip,nw_src={ip}"])
                print(f"[PERSON 2] Source rules removed for {ip}")
    except (RuntimeError,ValueError) as e: print(f"[PERSON 2] ERROR: {e}",file=sys.stderr); sys.exit(1)
if __name__=="__main__": main()
