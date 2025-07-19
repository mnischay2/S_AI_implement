import socket

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"🔌 Server listening on port {PORT}...")
try:
    while True:
        client_conn, client_addr = server_socket.accept()
        print(f"\n📥 Connection from {client_addr}")
        data = client_conn.recv(1024).decode().strip()
        if data:
            print(f"📡 Received data: {data}")
        client_conn.close()
except KeyboardInterrupt:
    print("\n🛑 Server stopped.")
finally:
    server_socket.close()