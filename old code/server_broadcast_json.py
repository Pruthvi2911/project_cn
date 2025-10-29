# server_broadcast_json_with_log.py
import socket, threading, json, os, csv
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5001
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

connections = []
connections_lock = threading.Lock()

def today_chat_file():
    return os.path.join(LOG_DIR, f"chat_{datetime.utcnow().strftime('%Y%m%d')}.csv")

def append_chat_log(timestamp, user, text):
    fname = today_chat_file()
    write_header = not os.path.exists(fname)
    with open(fname, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(['timestamp','user','text'])
        w.writerow([timestamp, user, text])

def broadcast(msg_obj, exclude=None):
    data = (json.dumps(msg_obj) + '\n').encode('utf-8')
    dead = []
    with connections_lock:
        for c in list(connections):
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
    print("Connected:", addr)
    with connections_lock:
        connections.append(conn)
    buffer = b''
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                try:
                    msg = json.loads(line.decode('utf-8'))
                except Exception:
                    continue
                action = msg.get('action')
                if action == 'chat':
                    user = msg.get('user','unknown')
                    text = msg.get('text','')
                    timestamp = datetime.utcnow().isoformat()
                    print(f"[{user}] {text}")
                    # write to CSV log
                    append_chat_log(timestamp, user, text)
                    # broadcast to others
                    broadcast({"action":"chat","user":user,"text":text,"timestamp":timestamp}, exclude=conn)
                # other actions (file) will be added later
    except Exception as e:
        print("Client error:", e)
    finally:
        with connections_lock:
            try:
                connections.remove(conn)
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass
        print("Disconnected:", addr)

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(50)
    print("Broadcast JSON server with logging listening on", HOST, PORT)
    try:
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    finally:
        s.close()

if __name__ == '__main__':
    main()
