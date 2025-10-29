# flask_app.py
from flask import Flask, request, jsonify
import socket, json, os
from datetime import datetime
from flask_cors import CORS



SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5001
LOG_DIR = 'logs'

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "react-ui", "dist")
app = Flask(__name__, static_folder=FRONTEND_DIST, template_folder=FRONTEND_DIST)
CORS(app)
from flask import send_from_directory

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # If the requested path exists in the built React `dist` folder, return it.
    # Otherwise return index.html so React Router (if any) can handle the route.
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


def send_to_socket_server(header_dict, file_bytes: bytes = None, timeout=5):
    """Connect to socket server, send header (newline-terminated), then optional raw bytes.
       Returns parsed JSON response or {'status':'ok'} if no valid response."""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((SOCKET_HOST, SOCKET_PORT))
        s.sendall((json.dumps(header_dict) + '\n').encode('utf-8'))
        if file_bytes:
            s.sendall(file_bytes)
        # read one-line response
        resp = b''
        while b'\n' not in resp:
            chunk = s.recv(4096)
            if not chunk:
                break
            resp += chunk
        s.close()
        if not resp:
            return {"status":"ok"}
        try:
            return json.loads(resp.decode('utf-8').split('\n',1)[0])
        except Exception:
            return {"status":"ok"}
    except Exception as e:
        try:
            s.close()
        except:
            pass
        return {"status":"error","msg":str(e)}

@app.route('/send_chat', methods=['POST'])
def send_chat():
    user = request.form.get('user','web')
    text = request.form.get('text','')
    if not text:
        return jsonify({"status":"error","msg":"empty text"}), 400
    header = {"action":"chat","user":user,"text":text}
    resp = send_to_socket_server(header)
    return jsonify(resp)

@app.route('/upload', methods=['POST'])
def upload():
    user = request.form.get('user', 'web')
    f = request.files.get('file')
    if not f:
        return jsonify({"status":"error","msg":"no file"}), 400
    data = f.read()
    header = {"action":"file", "user": user, "filename": f.filename, "size": len(data)}
    # forward header + raw bytes to the socket server
    resp = send_to_socket_server(header, file_bytes=data)
    return jsonify(resp)


@app.route('/messages', methods=['GET'])
def messages():
    """Return last chat lines from today's CSV as JSON for the web UI polling."""
    fname = os.path.join(LOG_DIR, f"chat_{datetime.utcnow().strftime('%Y%m%d')}.csv")
    out = []
    if os.path.exists(fname):
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            # skip header if present
            if lines and 'timestamp' in lines[0].lower():
                rows = lines[1:]
            else:
                rows = lines
            for r in rows:
                # split into 3 parts only (timestamp,user,text) - text may contain commas
                parts = r.split(',', 2)
                if len(parts) == 3:
                    out.append({"timestamp": parts[0], "user": parts[1], "text": parts[2]})
        except Exception:
            pass
    return jsonify(out[-200:])  # last 200 messages

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
