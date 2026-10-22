
import socket
from datetime import datetime

HOST = "127.0.0.1"
PORT = 9999


def main():
    print(f"Traffic server listening on {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)

        print("Waiting for client connections...")

        while True:
            conn, address = server.accept()

            with conn:
                print(
                    f"\n[{datetime.now():%H:%M:%S}] "
                    f"Connected: {address}"
                )

                while True:
                    data = conn.recv(4096)

                    if not data:
                        break

                    message = data.decode(
                        "utf-8", errors="replace"
                    )
                    print("Received:", message)

                print("Client disconnected.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer stopped.")
