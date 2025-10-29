# server_threaded.py - threaded echo server
import socket
import threading

HOST = '127.0.0.1'
PORT = 5001

def handle_client(conn, addr):
    print("Handle:", addr)
    try:
        data = conn.recv(1024)
        if not data:
            return
        print("Received from", addr, ":", data.decode())
        conn.sendall(b"ACK: " + data)
    finally:
        conn.close()
        print("Closed", addr)

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print("Threaded server listening on", HOST, PORT)
    try:
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    finally:
        s.close()

if __name__ == '__main__':
    main()
