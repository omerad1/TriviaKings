import socket
import threading

# Constants
UDP_PORT = 13117


# Function to listen for offer messages
def listen_for_offer():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.bind(('0.0.0.0', UDP_PORT))
        print("Client started, listening for offer requests...")
        while True:
            data, addr = udp_socket.recvfrom(1024)
            magic_cookie = data[:4]
            message_type = data[4]
            if magic_cookie == b'\xab\xcd\xdc\xba' and message_type == 0x2:
                server_name = data[5:37].decode().strip()
                server_port = int.from_bytes(data[37:39], byteorder='big')
                print(f"Received offer from server {server_name} at address {addr[0]}, attempting to connect...")
                connect_to_server(server_name, addr[0], server_port)


# Function to connect to the server over TCP
def connect_to_server(server_name, server_ip, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        try:
            tcp_socket.connect((server_ip, server_port))
            player_name = "Alice"  # Change player name as needed
            tcp_socket.sendall(player_name.encode() + b'\n')
            print("Connected to server. Waiting for game to start...")
            receive_messages_from_server(tcp_socket)
        except Exception as e:
            print(f"Error connecting to server: {e}")


# Function to receive and display messages from the server
def receive_messages_from_server(tcp_socket):
    while True:
        try:
            data = tcp_socket.recv(1024)
            if not data:
                break
            print(data.decode())
        except Exception as e:
            print(f"Error receiving data from server: {e}")
            break


# Main function
def main():
    listen_thread = threading.Thread(target=listen_for_offer)
    listen_thread.start()


if __name__ == "__main__":
    main()
