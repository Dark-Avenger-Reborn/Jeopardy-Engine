import eventlet
eventlet.monkey_patch()

import sys
import subprocess
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
from io import StringIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, async_mode='eventlet')

# Custom stdout handler for real-time logging
class LogStream(StringIO):
    def write(self, msg):
        super().write(msg)
        self.flush()
        socketio.emit('log_output', {'data': msg}, namespace='/logs')

sys.stdout = LogStream()

# Server management functions
def execute_command(action):
    try:
        if action == 'reboot':
            subprocess.run(['sudo', 'shutdown', '-r', 'now'], check=True)
        elif action == 'shutdown':
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
        elif action == 'restart_service':
            # Graceful server restart
            socketio.stop()
    except Exception as e:
        print(f"Error executing {action}: {str(e)}")

# WebSocket handlers
@socketio.on('server_action', namespace='/control')
def handle_server_action(data):
    action = data['action']
    print(f"Received {action} request")
    execute_command(action)

@socketio.on('connect', namespace='/control')
def control_connect():
    emit('log', {'data': 'Connected to control channel'})

# Main route
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print("Server starting...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
