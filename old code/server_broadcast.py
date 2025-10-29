# server_broadcast.py - threaded JSON chat server with broadcast
import socket, threading, json
HOST='127.0.0.1'; PORT=5001

connections = []            # list of conn sockets
connections_lock = threading.Lock()

def broadcast(msg_json, exclude=None):
    data = (json.dumps(msg_json) + '\n').encode('utf-8')
    dead = []
    with connections_lock:
        for c in connections:
            if c is exclude:
                continue
            try:
                c.sendall(data)
            except Exception:
                dead.append(c)
        for d in dead:
            try:
                connections.remove(d)
                d.close()
            except Exception:
                pass

def handle_client(conn, addr):
    with connections_lock:
        connections.append(conn)
    try:
        # keep reading newline-terminated JSON lines
        buffer = b''
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n',1)
                try:
                    obj = json.loads(line.decode('utf-8'))
                except Exception:
                    # ignore malformed
                    continue
                action = obj.get('action')
                if action == 'chat':
                    user = obj.get('user','unknown')
                    text = obj.get('text','')
                    # broadcast to others
                    broadcast({"action":"chat","user":user,"text":text}, exclude=conn)
                # (we'll add file handling later)
    finally:
        with connections_lock:
            try:
                connections.remove(conn)
            except ValueError:
                pass
        conn.close()

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(50)
    print("Broadcast server listening on", HOST, PORT)
    try:
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    finally:
        s.close()

if __name__ == '__main__':
    main()
