from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import eventlet

# Create the Flask app and initialize SocketIO with eventlet
app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')  # Use eventlet for async_mode

@app.route('/')
def main():
    return render_template('index.html')

@socketio.on('update_status')
def handle_update_status(data):
    print(data)

    # Emit a success message back to the client
    socketio.emit('update_status_all', data)

if __name__ == '__main__':
    # Use eventlet's WSGI server to run the app
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
