# run_all.py — starts both Flask and the socket server
import subprocess, webbrowser, time

# Start the socket server
socket_process = subprocess.Popen(["python", "server.py"])

# Give it 1 second to start up
time.sleep(1)

# Start the Flask app
flask_process = subprocess.Popen(["python", "flask_app.py"])

# Open the browser automatically
time.sleep(2)
webbrowser.open("http://127.0.0.1:8000/")

print("🔥 Both Flask and Socket Server are running.")
print("Press CTRL+C to stop both.")

try:
    socket_process.wait()
    flask_process.wait()
except KeyboardInterrupt:
    print("\nStopping servers...")
    socket_process.terminate()
    flask_process.terminate()
