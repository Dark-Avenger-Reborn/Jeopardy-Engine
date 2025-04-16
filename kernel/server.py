import socket

def start_server(host='127.0.0.1', port=4444):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print(f"[*] Listening on {host}:{port}")

    client_socket, client_address = server.accept()
    print(f"[*] Connection from {client_address}")

    while True:
        command = input("Shell> ")
        if command.lower() == "exit":
            break
        client_socket.send(command.encode())

    client_socket.close()
    server.close()

if __name__ == "__main__":
    start_server()
