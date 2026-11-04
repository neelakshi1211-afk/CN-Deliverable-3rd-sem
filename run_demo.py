import os,subprocess,sys,time
from pathlib import Path
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.log import setLogLevel,info
ROOT=Path(__file__).resolve().parent
def ctl(action,source=None):
    cmd=[sys.executable,str(ROOT/"person2_switch_control"/"switch_control.py"),action,"--bridge","s1"]
    if source: cmd += ["--source",source]
    subprocess.run(cmd,check=True)
def main():
    setLogLevel("info")
    csv="/tmp/sdn_traffic.csv"; alerts="/tmp/sdn_alerts.jsonl"; responses="/tmp/sdn_responses.jsonl"
    for x in (csv,alerts,responses):
        try: os.remove(x)
        except FileNotFoundError: pass
    net=Mininet(controller=None,switch=OVSSwitch,build=False,autoSetMacs=True)
    h1=net.addHost("h1",ip="10.0.0.1/24"); h2=net.addHost("h2",ip="10.0.0.2/24"); h3=net.addHost("h3",ip="10.0.0.3/24")
    s1=net.addSwitch("s1",failMode="standalone",protocols="OpenFlow13")
    net.addLink(h1,s1); net.addLink(h2,s1); net.addLink(h3,s1)
    procs=[]; response=None; dashboard=None
    try:
        info("*** Starting three-host Mininet topology\\n"); net.start()
        ctl("init"); info("*** Person 2: OVS forwarding initialized\\n")
        server=h3.popen(["python3",str(ROOT/"person1_traffic"/"server.py"),"--port","9000"]); procs.append(server); time.sleep(1)
        response=subprocess.Popen([sys.executable,str(ROOT/"person4_integration"/"response.py"),"--alerts",alerts,"--bridge","s1","--log",responses],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        dashboard=subprocess.Popen([sys.executable,str(ROOT/"dashboard"/"server.py"),"--host","127.0.0.1","--port","8765","--bridge","s1","--csv",csv,"--alerts",alerts,"--responses",responses],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        time.sleep(0.5)
        info("*** DASHBOARD: open http://127.0.0.1:8765 in the Ubuntu VM browser\n")
        monitor=h1.popen(["python3",str(ROOT/"person3_monitor_detection"/"live_monitor.py"),"--interval",".15","--threshold","5","--window","10","--csv",csv,"--alerts",alerts],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); procs.append(monitor); time.sleep(1)
        client=h1.popen(["python3",str(ROOT/"person1_traffic"/"client.py"),"--host","10.0.0.3","--port","9000","--count","8","--hold",".6","--delay",".1"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); procs.append(client)
        client.wait(timeout=25); time.sleep(2)
        info("*** PERSON 3 CSV LOG\\n"); print(Path(csv).read_text() if Path(csv).exists() else "No CSV created")
        info("*** PERSON 3 ALERTS\\n"); print(Path(alerts).read_text() if Path(alerts).exists() else "No alerts created")
        info("*** PERSON 2 SWITCH FLOW TABLE\\n"); ctl("show")
        if response and response.poll() is None:
            info("*** PERSON 4 response watcher is running; alert handling is active\\n")
        input("Press Enter to stop and clean up Mininet...")
    except KeyboardInterrupt: info("*** Interrupted\\n")
    finally:
        for proc in procs:
            if proc.poll() is None: proc.terminate()
        if response and response.poll() is None: response.terminate()
        if dashboard and dashboard.poll() is None: dashboard.terminate()
        net.stop()
if __name__=="__main__": main()
