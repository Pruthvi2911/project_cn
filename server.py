# server_with_file.py
import socket, threading, json, os, csv, time
from datetime import datetime
import os, csv
from datetime import datetime

LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

def log_chat(user, text):
    """Append chat message to daily CSV file."""
    fname = os.path.join(LOG_DIR, f"chat_{datetime.utcnow().strftime('%Y%m%d')}.csv")
    new = not os.path.exists(fname)
    with open(fname, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['timestamp','user','text'])
        w.writerow([datetime.utcnow().isoformat(), user, text])


HOST = '127.0.0.1'
PORT = 5001
LOG_DIR = 'logs'
UPLOAD_DIR = 'uploads'
MAX_UPLOAD = 1_048_576  # 1 MB

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

connections = []
connections_lock = threading.Lock()

def today_upload_file():
    return os.path.join(LOG_DIR, f"uploads_{datetime.utcnow().strftime('%Y%m%d')}.csv")

def append_upload_log(timestamp, user, orig_name, size, saved_path):
    fname = today_upload_file()
    write_header = not os.path.exists(fname)
    with open(fname, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(['timestamp','user','original_filename','size','path'])
        w.writerow([timestamp, user, orig_name, size, saved_path])

def broadcast(obj, exclude=None):
    data = (json.dumps(obj) + '\n').encode('utf-8')
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

def safe_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (' ','.','_','-')).rstrip()

def handle_client(conn, addr):
    with connections_lock:
        connections.append(conn)
    buffer = b''
    try:
        while True:
            # read incoming bytes; process newline-terminated JSON headers
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                try:
                    header = json.loads(line.decode('utf-8'))
                except Exception:
                    # ignore malformed header
                    continue

                action = header.get('action')
                if action == 'chat':
                    user = header.get('user','unknown')
                    text = header.get('text','')
                    ts = datetime.utcnow().isoformat()
                    print(f"[{user}] {text}")
                    log_chat(user, text)

                    # broadcast chat
                    broadcast({"action":"chat","user":user,"text":text,"timestamp":ts}, exclude=conn)

                elif action == 'file':
                    user = header.get('user','unknown')
                    filename = header.get('filename')
                    size = int(header.get('size',0))
                    if not filename or size <= 0:
                        try:
                            conn.sendall((json.dumps({"status":"error","msg":"invalid file header"})+'\n').encode())
                        except Exception:
                            pass
                        continue
                    if size > MAX_UPLOAD:
                        try:
                            conn.sendall((json.dumps({"status":"error","msg":"file too large"})+'\n').encode())
                        except Exception:
                            pass
                        continue

                    # `buffer` may already contain start of file payload
                    received = buffer
                    buffer = b''  # we take all from buffer as payload start
                    remaining = size - len(received)
                    while remaining > 0:
                        chunk2 = conn.recv(min(65536, remaining))
                        if not chunk2:
                            break
                        received += chunk2
                        remaining -= len(chunk2)
                    if len(received) != size:
                        try:
                            conn.sendall((json.dumps({"status":"error","msg":"incomplete upload"})+'\n').encode())
                        except Exception:
                            pass
                        continue

                    saved_name = f"{int(time.time())}_{safe_filename(user)}_{safe_filename(filename)}"
                    path = os.path.join(UPLOAD_DIR, saved_name)
                    try:
                        with open(path, 'wb') as f:
                            f.write(received)
                    except Exception as e:
                        try:
                            conn.sendall((json.dumps({"status":"error","msg":"save failed"})+'\n').encode())
                        except Exception:
                            pass
                        continue

                    ts = datetime.utcnow().isoformat()
                    append_upload_log(ts, user, filename, size, path)
                    try:
                        conn.sendall((json.dumps({"status":"ok","msg":"file received","path":path})+'\n').encode())
                    except Exception:
                        pass
                    # broadcast a short upload event
                    broadcast({"action":"file","user":user,"filename":filename,"timestamp":ts}, exclude=conn)

                else:
                    # unknown action: ignore
                    continue
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

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(50)
    print("Server with file support listening on", HOST, PORT)
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    finally:
        s.close()

if __name__ == '__main__':
    main()
