import socket
import threading
import time
import random

# Constants
UDP_PORT = 13117
TCP_PORT = 12345
SERVER_NAME = "Mystic"  # Adjust server name as needed
MAX_PLAYERS = 3

# Global variables
players = []
questions = [
    {
        "question": "Aston Villa's current manager is Pep Guardiola",
        "answer": False
    },
    {
        "question": "Aston Villa's mascot is a lion named Hercules",
        "answer": True
    }
]
current_question = None

# Function to broadcast offer messages
def broadcast_offer():
    offer_message = b'\xab\xcd\xdc\xba\x02' + SERVER_NAME.encode().ljust(32) + \
                    (TCP_PORT).to_bytes(2, byteorder='big')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.bind(('0.0.0.0', UDP_PORT))
        while True:
            udp_socket.sendto(offer_message, ('<broadcast>', UDP_PORT))
            time.sleep(1)

# Function to handle TCP connections with clients
def handle_client(client_socket, address):
    global players
    try:
        # Receive player name from client
        player_name = client_socket.recv(1024).decode().strip()
        players.append((player_name, client_socket))
        print(f"Player {player_name} connected from {address}")

        # Start the game if all players have joined
        if len(players) == MAX_PLAYERS:
            start_game()
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

# Function to start the game
def start_game():
    global current_question
    send_welcome_message()
    while True:
        current_question = random.choice(questions)
        send_question_to_clients(current_question)
        time.sleep(10)

# Function to send welcome message to all clients
def send_welcome_message():
    welcome_message = f"Welcome to the {SERVER_NAME} server, where we are answering trivia questions about Aston Villa FC.\n"
    for i, (player_name, client_socket) in enumerate(players, 1):
        welcome_message += f"Player {i}: {player_name}\n"
    for _, client_socket in players:
        client_socket.sendall(welcome_message.encode())

# Function to send question to all clients
def send_question_to_clients(question_data):
    for _, client_socket in players:
        client_socket.sendall(question_data["question"].encode())

# Main function
def main():
    # Start UDP broadcast thread
    udp_thread = threading.Thread(target=broadcast_offer)
    udp_thread.start()

    # Start TCP server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind(('0.0.0.0', TCP_PORT))
        tcp_socket.listen()
        print(f"Server started, listening on IP address 0.0.0.0, port {TCP_PORT}")

        # Accept incoming connections
        while True:
            client_socket, address = tcp_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
            client_handler.start()

if __name__ == "__main__":
    main()
