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
    def __init__(self, stream):
        super().__init__()
        self._stream = stream

    def write(self, text):
        if text.strip():
            # Write to the original stream to avoid recursion.
            self._stream.write(text)
            self._stream.flush()
            sio.start_background_task(sio.emit, 'log_output', {'data': text})
        super().write(text)

    def flush(self):
        self._stream.flush()


def is_running_under_systemd():
    return os.getenv('INVOCATION_ID') is not None

# Simple configuration: add all teams and services here
TEAM_NAMES = [
    "Team 1",
    "Team 2",
    "Team 3",
]

SERVICE_NAMES = [
    "Service 1",
    "Service 2",
    "Service 3",
]

DEFAULT_SERVICE_STATUS = [False] * len(SERVICE_NAMES)

# Store scoreboard state in memory
scoreboard_data = [
    {"team": team_name, "services": DEFAULT_SERVICE_STATUS.copy()}
    for team_name in TEAM_NAMES
]

@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")
    # Send current scoreboard state to new client
    sio.emit(
        'scoreboard_update',
        {'scoreboard': scoreboard_data, 'service_names': SERVICE_NAMES},
        to=sid,
    )


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
            if team_idx < 0 or team_idx >= len(scoreboard_data):
                return
            if service_idx < 0 or service_idx >= len(SERVICE_NAMES):
                return
            scoreboard_data[team_idx]['services'][service_idx] = (
                not scoreboard_data[team_idx]['services'][service_idx]
            )
            # Broadcast updated scoreboard to all clients
            sio.emit(
                'scoreboard_update',
                {'scoreboard': scoreboard_data, 'service_names': SERVICE_NAMES},
            )
        except Exception as e:
            print(f"Error toggling service: {e}")


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    original_stdout = sys.__stdout__
    original_stderr = sys.__stderr__

    sys.stdout = LogEmitter(original_stdout)
    sys.stderr = LogEmitter(original_stderr)

    flaskApp = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), flaskApp)
