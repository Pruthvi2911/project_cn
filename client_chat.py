# client_chat.py - interactive client with listener thread
import socket, threading, json

HOST='127.0.0.1'; PORT=5001

def listener(s):
    buf = b''
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                print("Disconnected from server")
                return
            buf += chunk
            while b'\n' in buf:
                line, buf = buf.split(b'\n',1)
                try:
                    obj = json.loads(line.decode('utf-8'))
                    if obj.get('action') == 'chat':
                        print(f"\n[{obj.get('user')}] {obj.get('text')}")
                except Exception:
                    pass
    except Exception as e:
        print("Listener error:", e)

def main():
    user = input("Your name: ").strip() or "me"
    s = socket.socket()
    s.connect((HOST, PORT))
    t = threading.Thread(target=listener, args=(s,), daemon=True)
    t.start()
    try:
        while True:
            msg = input("> ")
            if msg.lower() in ('/quit','/exit'):
                break
            header = {"action":"chat","user":user,"text":msg}
            s.sendall((json.dumps(header)+'\n').encode('utf-8'))
    finally:
        s.close()
        print("Client closed")

if __name__ == '__main__':
    main()
