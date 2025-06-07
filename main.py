import os
import sys
import subprocess
from io import StringIO
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import eventlet

# Apply eventlet monkey patching for async support
eventlet.monkey_patch()

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, async_mode='eventlet')


class LogEmitter(StringIO):
    """
    Custom StringIO to emit log data over WebSocket
    """
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def write(self, text):
        if text.strip():  # Ignore empty lines
            self.socketio.emit('log_output', {'data': text})
        super().write(text)

    def flush(self):
        pass  # Overridden for compatibility


def is_running_under_systemd():
    """
    Check if the current process is running under systemd
    """
    return os.getenv('INVOCATION_ID') is not None


def execute_command(action):
    """
    Execute system-level commands like reboot, shutdown, or service restart
    """
    try:
        if action == 'reboot':
            subprocess.run(['sudo', 'shutdown', '-r', 'now'], check=True)

        elif action == 'shutdown':
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)

        elif action == 'restart_service':
            print("Restarting service...")

            if is_running_under_systemd():
                print("Detected systemd — restarting via systemctl")
                subprocess.run(['sudo', 'systemctl', 'restart', 'your-service-name'], check=True)
            else:
                print("Not running under systemd — restarting Python process")
                python = sys.executable
                os.execv(python, [python] + sys.argv)

    except Exception as e:
        print(f"Error executing {action}: {e}")


# WebSocket event handler
@socketio.on('server_action')
def handle_server_action(data):
    action = data.get('action')
    if action:
        print(f"Received {action} request")
        execute_command(action)
    else:
        print("No action specified")


# HTTP route
@app.route('/')
def index():
    return render_template('index.html')


# Entry point
if __name__ == '__main__':
    log_emitter = LogEmitter(socketio)
    sys.stdout = log_emitter
    sys.stderr = log_emitter

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)