import eventlet
import os
import sys
import subprocess
from io import StringIO
import socketio
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
app.secret_key = os.urandom(24)
sio = socketio.Server(cors_allowed_origins="*", logger=False, max_http_buffer_size=1e8)


class LogEmitter(StringIO):
    def __init__(self):
        super().__init__()

    def write(self, text):
        if text.strip():
            sio.start_background_task(sio.emit, 'log_output', {'data': text})
        super().write(text)

    def flush(self):
        pass


def is_running_under_systemd():
    return os.getenv('INVOCATION_ID') is not None

# Store scoreboard state in memory
scoreboard_data = [
    {"team": "Team 1", "services": [True, False, True]},
    {"team": "Team 2", "services": [False, True, False]},
    {"team": "Team 3", "services": [True, True, True]},
]

@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")
    # Send current scoreboard state to new client
    sio.emit('scoreboard_update', {'scoreboard': scoreboard_data}, to=sid)


@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")


@sio.on('server_action')
def server_action(sid, data):
    sio.emit('server_error', {'message': "testing"})
    print(f"Received action from {sid}: {data}")
    action = data.get('action')
    if action:
        try:
            if action == 'reboot':
                subprocess.run(['sudo', 'reboot', '-r', 'now'], check=True)
            elif action == 'shutdown':
                subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
            elif action == 'restart_service':
                print("Restarting service...")
                if is_running_under_systemd():
                    print("Detected systemd — restarting via systemctl")
                    subprocess.run(['sudo', 'systemctl', 'restart', 'evilengine.service'], check=True)
                else:
                    print("Not running under systemd — restarting Python process")
                    python = sys.executable
                    os.execv(python, [python] + sys.argv)
        except Exception as e:
            print(f"Error executing {action}: {e}")


@sio.on('toggle_service')
def toggle_service(sid, data):
    team_idx = data.get('team_idx')
    service_idx = data.get('service_idx')
    if team_idx is not None and service_idx is not None:
        try:
            scoreboard_data[team_idx]['services'][service_idx] = not scoreboard_data[team_idx]['services'][service_idx]
            # Broadcast updated scoreboard to all clients
            sio.emit('scoreboard_update', {'scoreboard': scoreboard_data})
        except Exception as e:
            print(f"Error toggling service: {e}")


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    #log_emitter = LogEmitter()
    #sys.stdout = log_emitter
    #sys.stderr = log_emitter

    flaskApp = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), flaskApp)
