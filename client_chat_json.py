# client_chat_json.py (graceful shutdown)
import socket, threading, json, time

HOST = '127.0.0.1'
PORT = 5001

def listener(s):
    buf = b''
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                print("\n[info] Disconnected from server")
                return
            buf += chunk
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                try:
                    obj = json.loads(line.decode('utf-8'))
                    if obj.get('action') == 'chat':
                        print(f"\n[{obj.get('user')}] {obj.get('text')}")
                        print("> ", end='', flush=True)
                except Exception:
                    pass
    except Exception as e:
        # listener ended
        # print only short message to avoid noisy finalization errors
        # (don't re-raise)
        return

def main():
    user = input("Your name: ").strip() or "me"
    s = socket.socket()
    try:
        s.connect((HOST, PORT))
    except Exception as e:
        print("Could not connect:", e); return

    t = threading.Thread(target=listener, args=(s,), daemon=True)
    t.start()

    try:
        while True:
            msg = input("> ").strip()
            if not msg:
                continue
            if msg.lower() in ('/quit','/exit'):
                # request clean shutdown
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                break
            header = {"action":"chat","user":user,"text":msg}
            try:
                s.sendall((json.dumps(header) + '\n').encode('utf-8'))
            except Exception:
                print("[error] failed to send message")
                break
    except KeyboardInterrupt:
        try:
            s.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
    finally:
        try:
            s.close()
        except Exception:
            pass
        # small pause to let listener thread exit cleanly
        time.sleep(0.1)
        print("Client closed")

if __name__ == '__main__':
    main()
