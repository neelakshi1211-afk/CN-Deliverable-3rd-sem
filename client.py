
import socket
import time

HOST = "127.0.0.1"
PORT = 9999


def main():
    print("Starting normal traffic generator...")

    try:
        for number in range(1, 11):
            message = f"Normal test message {number}"

            with socket.create_connection(
                (HOST, PORT), timeout=3
            ) as client:
                client.sendall(message.encode("utf-8"))
                print("Sent:", message)

            time.sleep(1)

        print("Traffic generation completed.")

    except OSError as error:
        print("Connection failed:", error)
        print("Make sure server.py is running first.")


if __name__ == "__main__":
    main()
