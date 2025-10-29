import socket, threading, json

HOST = '127.0.0.1'
PORT = 5001

def handle_client(conn, addr):
    print("Connected:", addr)
    try:
        data = conn.recv(4096)
        if not data:
            return
        # decode bytes → string → dict
        message = json.loads(data.decode())
        user = message.get("user")
        text = message.get("text")
        print(f"[{user}] {text}")
        # send confirmation back
        reply = {"status": "ok", "echo": text}
        conn.sendall(json.dumps(reply).encode())
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print("JSON server listening on", HOST, PORT)
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
