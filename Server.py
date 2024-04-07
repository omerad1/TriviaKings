import socket
import threading
import time
import random
import json


def get_available_port():
    """Find an available port for the server."""
    # Create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))  # Bind to any available port on localhost
    address = s.getsockname()  # Get the (host, port) tuple assigned by the OS
    ip, port = address
    s.close()  # Close the socket
    return ip, port


# Read configuration data from JSON file
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

# Accessing configuration values
dest_port = config_data['dest_port']
server_name = config_data['server_name']
questions = config_data['questions']
magic_cookie = config_data['magic_cookie']
message_type = config_data['message_type']

# get available port for the server
ip_address, server_port = get_available_port()

# encode and pad the server name
server_name_encoded = server_name.encode('utf-8').ljust(32)

# todo: do somthing with this
players = []
current_question = None


# Function to broadcast offer messages
# Function to broadcast offer messages
def broadcast_offer():
    print("Server started, listening on IP address", ip_address, "waiting for players to join the game!")
    offer_message = magic_cookie + message_type + server_name_encoded + server_port.to_bytes(2, byteorder='big')
    start_time = time.time()  # Record the start time of the 10-second window
    curr_len = len(players)  # how many players we have
    while curr_len == 0 or time.time() - start_time <= 10:  # checks if we doesn't have players yet or that 10 seconds
        # has passed from last join
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as udp_socket:
                udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                udp_socket.bind((ip_address, dest_port))  # Bind to the IP address
                udp_socket.sendto(offer_message, ('<broadcast>', dest_port))
        except OSError as e:
            print("Error:", e)
            # Continue to the next iteration of the loop if there's an error
            continue
        # Sleep for 1 second between broadcasts
        time.sleep(1)
        # Check if a new player has joined
        if len(players) > curr_len:
            curr_len = len(players)
            print("New player joined.")
            start_time = time.time()  # Reset the start time for the 10-second window
    print("No new players joined within 10 seconds. Stopping broadcast.")



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
