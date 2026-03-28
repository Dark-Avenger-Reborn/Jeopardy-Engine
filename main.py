import eventlet
import os
import sys
import subprocess
import threading
from io import StringIO
import socketio
from flask import Flask, render_template, jsonify, request
from trigger_break import break_management

app = Flask(__name__)
app.secret_key = os.urandom(24)
sio = socketio.Server(cors_allowed_origins="*", logger=False, max_http_buffer_size=1e8)


class LogEmitter(StringIO):
    def __init__(self, stream):
        super().__init__()
        self._stream = stream
        self._buffer = ""
        self._lock = threading.Lock()

    def _emit_log_line(self, line):
        """Emit a log line to connected web clients.

        Direct emit works from worker threads. If anything fails, fall back to
        a background task so logs are not silently dropped.
        """
        try:
            sio.emit('log_output', {'data': line})
        except Exception:
            sio.start_background_task(sio.emit, 'log_output', {'data': line})

    def write(self, text):
        if not text:
            return 0

        with self._lock:
            # Write to the original stream to avoid recursion.
            self._stream.write(text)
            self._stream.flush()

            self._buffer += text
            lines = self._buffer.splitlines(keepends=True)
            self._buffer = ""

            for line in lines:
                if line.endswith("\n") or line.endswith("\r"):
                    self._emit_log_line(line)
                else:
                    self._buffer = line

            super().write(text)
        return len(text)

    def flush(self):
        with self._lock:
            if self._buffer:
                self._emit_log_line(self._buffer + "\n")
                self._buffer = ""
            self._stream.flush()


def is_running_under_systemd():
    return os.getenv('INVOCATION_ID') is not None

# System and protocol definitions
SYSTEMS = [
    {"name": "Ubuntu1", "ip": "10.x.1.10", "os": "Ubuntu 24.02", "protocols": ["ICMP", "SSH"]},
    {"name": "Ubuntu2", "ip": "10.x.1.40", "os": "Ubuntu 24.02", "protocols": ["ICMP", "SSH"]},
    {"name": "UbuntuServer", "ip": "10.x.1.90", "os": "Ubuntu 24.02", "protocols": ["HTTP", "FTP", "ICMP", "MySQL"]},
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

# Create a flat list of all system:protocol combinations for the service status
ALL_SERVICES = []
for system in SYSTEMS:
    for protocol in system["protocols"]:
        ALL_SERVICES.append(f"{system['name']}:{protocol}")

# Explicit service routing avoids relying on BreakLevels JSON key order.
SERVICE_TARGET_MAP = {
    "Ubuntu1:ICMP": "10.x.1.10",
    "Ubuntu1:SSH": "10.x.1.10:22",
    "Ubuntu2:ICMP": "10.x.1.40",
    "Ubuntu2:SSH": "10.x.1.40:22",
    "UbuntuServer:HTTP": "10.x.2.2:80",
    "UbuntuServer:FTP": "10.x.2.4:21",
    "UbuntuServer:ICMP": "10.x.2.10",
    "UbuntuServer:MySQL": "10.x.2.10:22",
    "AD:DNS": "10.x.1.60",
    "AD:LDAP": "10.x.1.60:389",
    "Windows1:WinRM": "10.x.1.70:5985",
    "Windows1:ICMP": "10.x.1.70",
    "Windows2:WinRM": "10.x.1.80:5985",
    "Windows2:ICMP": "10.x.1.80",
    "pfSense:Firewall": "10.x.1.1",
}

break_manager = break_management(service_keys=ALL_SERVICES, service_target_map=SERVICE_TARGET_MAP)


def _emit_direct_web_log(line):
    if not isinstance(line, str):
        return
    payload = line if line.endswith("\n") else line + "\n"
    try:
        sio.emit('log_output', {'data': payload})
    except Exception:
        pass


break_manager.manager.log_emitter = _emit_direct_web_log

DEFAULT_SERVICE_STATUS = [False] * len(ALL_SERVICES)

# Store scoreboard state in memory
scoreboard_data = [
    {"team": team_name, "services": DEFAULT_SERVICE_STATUS.copy()}
    for team_name in TEAM_NAMES
]


def _scoreboard_payload():
    return {
        'scoreboard': scoreboard_data,
        'systems': SYSTEMS,
        'all_services': ALL_SERVICES,
        'service_names': [f"{s['name']}" for s in SYSTEMS],
    }


def _reset_scoreboard_state():
    for team in scoreboard_data:
        team['services'] = DEFAULT_SERVICE_STATUS.copy()


def _clear_active_breaks_for_current_level():
    """Unbreak active services so backend state matches a level reset."""
    for team_idx, team in enumerate(scoreboard_data):
        for service_idx, is_active in enumerate(team.get('services', [])):
            if is_active:
                break_manager.trigger_unbreak(team_idx, service_idx)

@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")
    # Send current scoreboard state to new client
    sio.emit('scoreboard_update', _scoreboard_payload(), to=sid)


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
            sio.emit('scoreboard_update', _scoreboard_payload())

            desired_state = scoreboard_data[team_idx]['services'][service_idx]
            sio.start_background_task(
                _dispatch_service_action,
                team_idx,
                service_idx,
                desired_state,
            )
        except Exception as e:
            print(f"Error toggling service: {e}")


def _dispatch_service_action(team_idx, service_idx, desired_state):
    """Dispatch break/fix in background without blocking UI updates."""
    try:
        if desired_state:
            break_manager.trigger_break(team_idx, service_idx)
        else:
            break_manager.trigger_unbreak(team_idx, service_idx)
    except Exception as e:
        print(f"Error dispatching service action: {e}")


@app.route('/')
def index():
    return render_template('index.html', admin=False, break_manager=break_manager, scoreboard_data=scoreboard_data, all_services=ALL_SERVICES)


@app.route('/admin')
def admin():
    return render_template('index.html', admin=True, break_manager=break_manager, scoreboard_data=scoreboard_data, all_services=ALL_SERVICES)


@app.route('/set_level', methods=['POST'])
@app.route('/set_level/<level>', methods=['GET'])
def set_level(level=None):
    requested_level = level
    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        requested_level = payload.get('level')

    available_levels = break_manager.manager.breaks_data.get('breaks', {})
    if requested_level not in available_levels:
        return jsonify({'message': 'Invalid level'}), 400

    previous_level = break_manager.level
    _clear_active_breaks_for_current_level()

    break_manager.level = requested_level
    level_breaks = break_manager.manager.breaks_data.get('breaks', {}).get(requested_level, {})
    break_manager.service_targets = list(level_breaks.keys())

    _reset_scoreboard_state()
    payload = _scoreboard_payload()
    sio.emit('scoreboard_update', payload)

    return jsonify({
        'message': f'Break level changed from {previous_level} to {requested_level}. Active table has been reset.',
        'level': requested_level,
        **payload,
    })


@app.route('/redboard')
def redboard():
    import json
    from concurrent.futures import ThreadPoolExecutor, as_completed
    try:
        with open('redboardbreak.txt') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading redboardbreak.txt: {e}")
        return 'Unable to load redboard commands', 500

    linux_command = data.get('linux', '').strip()
    windows_command = data.get('windows', '').strip()
    router_command = data.get('router', '').strip()

    # Team-scoped device templates. `x` is replaced with team number.
    linux_targets = ['10.x.1.10', '10.x.1.40', '10.x.2.10']
    windows_targets = ['10.x.1.60', '10.x.1.70', '10.x.1.80']
    router_targets = ['10.x.1.1']

    team_count = len(TEAM_NAMES)
    jobs = []

    def queue_jobs(command, targets, sender):
        if not command:
            return
        for team_number in range(1, team_count + 1):
            for target in targets:
                ip = break_manager.manager.apply_team_to_target(target, team_number)
                jobs.append((sender, ip, command))

    queue_jobs(linux_command, linux_targets, break_manager.manager.send_linux_command)
    queue_jobs(windows_command, windows_targets, break_manager.manager.send_windows_command)
    queue_jobs(router_command, router_targets, break_manager.manager.send_linux_command)

    attempted = len(jobs)
    if attempted == 0:
        return 'No redboard commands configured', 400

    succeeded = 0
    max_workers = min(64, attempted)

    # Use native threads so blocking socket operations run in parallel.
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(sender, ip, command) for sender, ip, command in jobs]
        for future in as_completed(futures):
            try:
                if future.result():
                    succeeded += 1
            except Exception as e:
                print(f"Error dispatching redboard command: {e}")

    failed = attempted - succeeded
    if failed:
        return f'Redboard deployed with partial success: {succeeded}/{attempted} commands succeeded'
    return f'Redboard break deployed to all devices: {succeeded}/{attempted} commands succeeded'


if __name__ == '__main__':
    original_stdout = sys.__stdout__
    original_stderr = sys.__stderr__

    sys.stdout = LogEmitter(original_stdout)
    sys.stderr = LogEmitter(original_stderr)

    flaskApp = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), flaskApp, log_output=False)
