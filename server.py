import argparse, socket, threading
def serve(conn, addr):
    try:
        data=conn.recv(1024)
        if data:
            print(f"Received from {addr}: {data.decode(errors='replace')}", flush=True)
            conn.sendall(b"ACK")
    finally: conn.close()
def main():
    p=argparse.ArgumentParser(); p.add_argument("--host",default="0.0.0.0"); p.add_argument("--port",type=int,default=9000); a=p.parse_args()
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind((a.host,a.port)); s.listen()
        print(f"TCP server listening on {a.host}:{a.port}",flush=True)
        while True:
            c,addr=s.accept(); threading.Thread(target=serve,args=(c,addr),daemon=True).start()
if __name__=="__main__": main()
