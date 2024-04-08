import socket
import threading
import time
import random
import json

from Player import Player
from PlayerManager import PlayerManager
from GameEngine import GameEngine


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

player_manager = PlayerManager()
game_engine = GameEngine(player_manager, questions)
broadcast_finished_event = threading.Event


# Function to broadcast offer messages
def broadcast_offer():
    print("Server started, listening on IP address", ip_address, "waiting for players to join the game!")
    offer_message = magic_cookie + message_type + server_name_encoded + server_port.to_bytes(2, byteorder='big')
    start_time = time.time()  # Record the start time of the 10-second window
    curr_len = len(player_manager.get_players())  # how many players we have
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
        if len(player_manager.get_players()) > curr_len:
            curr_len = len(player_manager.get_players())
            print("New player joined.")
            start_time = time.time()  # Reset the start time for the 10-second window
    print("No new players joined within 10 seconds. Stopping broadcast.")
    broadcast_finished_event.set()  # Set the event when the broadcast is finished


# Function to handle TCP connections with clients
def handle_client(client_socket, address):
    try:
        # Receive player name from client
        player_name = client_socket.recv(1024).decode().strip()
        player = Player(player_name, client_socket, True)
        player_manager.add_player(player)
        print(f"Player {player_name} connected from {address}")

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()


# Function to start the game
def start_game(tcp_socket):
    send_welcome_message()
    game_engine.play_game(tcp_socket)


# Function to send welcome message to all clients
def send_welcome_message():
    welcome_message = f"Welcome to the {server_name} server, where we are answering trivia questions about Movies !\n"
    players = player_manager.get_players()
    for i, (player) in enumerate(players, 1):
        welcome_message += f"Player {i}: {player.get_name()}\n"
    print(welcome_message)
    for p in players:
        client_socket = p.get_socket()
        client_socket.sendall(welcome_message.encode())


# Function to send question to all clients


# Main function
def main():
    # Start UDP broadcast thread
    udp_thread = threading.Thread(target=broadcast_offer)
    udp_thread.start()

    # Start TCP server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind(('0.0.0.0', server_port))
        tcp_socket.listen()
        print(f"Server listening on IP address 0.0.0.0, port {server_port}")

        # Accept incoming connections and handle clients
        while True:
            client_socket, address = tcp_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
            client_handler.start()

            # Check if the broadcast has finished
            if broadcast_finished_event.is_set():
                # Call start_game once the broadcast is finished
                start_game(tcp_socket)
                break  # Exit the loop to stop accepting new connections


if __name__ == "__main__":
    main()