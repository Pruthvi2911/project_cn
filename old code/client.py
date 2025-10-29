# client_with_upload.py
import socket, threading, json, time, os

HOST = '127.0.0.1'
PORT = 5001
MAX_UPLOAD = 1_048_576  # 1 MB

def listener(s):
    buf = b''
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                print("\n[info] disconnected")
                return
            buf += chunk
            while b'\n' in buf:
                line, buf = buf.split(b'\n',1)
                try:
                    obj = json.loads(line.decode('utf-8'))
                    if obj.get('action') == 'chat':
                        print(f"\n[{obj.get('user')}] {obj.get('text')}")
                    elif obj.get('action') == 'file':
                        print(f"\n[upload] {obj.get('user')} uploaded {obj.get('filename')}")
                    else:
                        # ack or other status responses
                        if obj.get('status'):
                            print(f"\n[server] {obj.get('status')}: {obj.get('msg','')}")
                except Exception:
                    pass
                print("> ", end='', flush=True)
    except Exception:
        return

def send_chat(s, user, text):
    header = {"action":"chat","user":user,"text":text}
    s.sendall((json.dumps(header)+'\n').encode('utf-8'))

def send_file(s, user, filepath):
    if not os.path.exists(filepath):
        print("file not found")
        return
    size = os.path.getsize(filepath)
    if size > MAX_UPLOAD:
        print("file too large (limit 1 MB)")
        return
    filename = os.path.basename(filepath)
    header = {"action":"file","user":user,"filename":filename,"size":size}
    s.sendall((json.dumps(header)+'\n').encode('utf-8'))
    # then send raw bytes
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            s.sendall(chunk)
    # wait for server ack line (newline-terminated)
    resp = b''
    while b'\n' not in resp:
        chunk = s.recv(4096)
        if not chunk:
            break
        resp += chunk
    try:
        obj = json.loads(resp.decode('utf-8').split('\n',1)[0])
        if obj.get('status') == 'ok':
            print("Upload OK")
        else:
            print("Upload failed:", obj.get('msg'))
    except Exception:
        print("No proper server response")

def main():
    user = input("Your name: ").strip() or "me"
    s = socket.socket()
    try:
        s.connect((HOST, PORT))
    except Exception as e:
        print("connect failed:", e); return
    t = threading.Thread(target=listener, args=(s,), daemon=True)
    t.start()
    try:
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ('/quit','/exit'):
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                break
            if cmd.startswith('/upload '):
                path = cmd.split(' ',1)[1].strip()
                send_file(s, user, path)
                continue
            # sending chat
            send_chat(s, user, cmd)
    finally:
        try:
            s.close()
        except Exception:
            pass
        time.sleep(0.1)
        print("client closed")

if __name__ == '__main__':
    main()
