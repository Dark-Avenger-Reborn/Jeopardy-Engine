import eventlet
import os
import sys
import subprocess
from io import StringIO
import socketio
from flask import Flask, render_template, jsonify, request
from trigger_break import break_management

app = Flask(__name__)
app.secret_key = os.urandom(24)
sio = socketio.Server(cors_allowed_origins="*", logger=False, max_http_buffer_size=1e8)
break_manager = break_management()


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

# System and protocol definitions
SYSTEMS = [
    {"name": "Ubuntu1", "ip": "10.x.1.10", "os": "Ubuntu 24.02", "protocols": ["ICMP", "SSH"]},
    {"name": "Ubuntu2", "ip": "10.x.1.40", "os": "Ubuntu 24.02", "protocols": ["ICMP", "SSH"]},
    {"name": "UbuntuServer", "ip": "10.x.1.90", "os": "Ubuntu 24.02", "protocols": ["HTTP", "MySQL"]},
    {"name": "WebApp Server", "ip": "TBD", "os": "", "protocols": ["FTP", "ICMP"]},
    {"name": "Comm Server", "ip": "TBD", "os": "", "protocols": []},
    {"name": "AD", "ip": "10.x.1.60", "os": "Server 2022", "protocols": ["DNS", "LDAP"]},
    {"name": "Windows1", "ip": "10.x.1.70", "os": "Windows 10", "protocols": ["WinRM", "ICMP"]},
    {"name": "Windows2", "ip": "10.x.1.80", "os": "Windows 10", "protocols": ["WinRM", "ICMP"]},
    {"name": "pfSense", "ip": "10.x.1.1", "os": "pfSense", "protocols": ["Firewall"]},
]

# Simple configuration: add all teams here
TEAM_NAMES = [
    "Team 1",
    "Team 2",
    "Team 3",
    "Team 4",
    "Team 5",
    "Team 6",
    "Team 7",
    "Team 8",
    "Team 9",
    "Team 10",
    "Team 11",
    "Team 12",
    "Team 13",
    "Team 14",
    "Team 15",
]

SERVICE_NAMES = break_manager.get_service_names()

# Create a flat list of all system:protocol combinations for the service status
ALL_SERVICES = []
for system in SYSTEMS:
    for protocol in system["protocols"]:
        ALL_SERVICES.append(f"{system['name']}:{protocol}")

DEFAULT_SERVICE_STATUS = [False] * len(ALL_SERVICES)

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
        {
            'scoreboard': scoreboard_data,
            'systems': SYSTEMS,
            'all_services': ALL_SERVICES,
            'service_names': [f"{s['name']}" for s in SYSTEMS]
        },
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
            if service_idx < 0 or service_idx >= len(ALL_SERVICES):
                return
            scoreboard_data[team_idx]['services'][service_idx] = (
                not scoreboard_data[team_idx]['services'][service_idx]
            )
            break_manager.trigger_break(team_idx, service_idx) if scoreboard_data[team_idx]['services'][service_idx] else break_manager.trigger_unbreak(team_idx, service_idx)
            sio.emit(
                'scoreboard_update',
                {
                    'scoreboard': scoreboard_data,
                    'systems': SYSTEMS,
                    'all_services': ALL_SERVICES,
                    'service_names': [f"{s['name']}" for s in SYSTEMS]
                },
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
