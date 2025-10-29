import socket, json

HOST = '127.0.0.1'
PORT = 5001

s = socket.socket()
s.connect((HOST, PORT))

user = input("Your name: ")
text = input("Type message: ")

msg = {"action": "chat", "user": user, "text": text}
s.sendall(json.dumps(msg).encode())

resp = s.recv(4096)
print("Server replied:", resp.decode())

s.close()
