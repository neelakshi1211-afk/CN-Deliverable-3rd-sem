import argparse,socket,time
def main():
    p=argparse.ArgumentParser(); p.add_argument("--host",default="10.0.0.3"); p.add_argument("--port",type=int,default=9000); p.add_argument("--count",type=int,default=8); p.add_argument("--hold",type=float,default=.7); p.add_argument("--delay",type=float,default=.15); a=p.parse_args()
    for i in range(1,a.count+1):
        try:
            with socket.create_connection((a.host,a.port),timeout=3) as s:
                s.sendall(f"demo-connection-{i}".encode()); s.settimeout(3); print(f"Connection {i}/{a.count}: {s.recv(1024).decode()}",flush=True); time.sleep(a.hold)
        except OSError as e: print(f"Connection failed: {e}",flush=True); break
        time.sleep(a.delay)
if __name__=="__main__": main()
