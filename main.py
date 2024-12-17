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
    """
    This function is triggered when the 'update_status' event is emitted from the client.
    It processes the received data and returns a response over the WebSocket.
    """
    string_of_ips = ""
    ip_list = []

    # Log or process the received data
    print("Received Data:")
    for team in data:
        for ip_state in team['ipStates']:
            if ip_state['isChecked']:
                if (":" in ip_state['ip']):
                    finalIP = ip_state['ip'].split(":")[0]
                else:
                    finalIP = ip_state['ip']
                ip_list.append(ip_state['ip'])
                string_of_ips += finalIP + ","

    string_of_ips = string_of_ips[:-1]
    print(string_of_ips)
    print(ip_list)

    # Emit a success message back to the client
    socketio.emit('status_update_all', ip_list)

if __name__ == '__main__':
    # Use eventlet's WSGI server to run the app
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
