import threading
import time
import json
import netifaces
from Player import Player
from PlayerManager import PlayerManager
from GameEngine import GameEngine
import socket
import ipaddress

# Read configuration data from JSON file
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

# Accessing configuration values
dest_port = config_data['dest_port']
server_name = config_data['server_name']
questions = config_data['questions']
magic_cookie = config_data['magic_cookie']
message_type = config_data['message_type']
true_answers, false_answers = config_data['true_options'], config_data['false_options']
# get available port for the server

# encode and pad the server name
server_name_encoded = server_name.encode('utf-8').ljust(32)

player_manager = PlayerManager()
game_engine = GameEngine(player_manager, questions, true_answers, false_answers)
broadcast_finished_event = threading.Event


def get_ip_address():
    """
    Get the IP address of the current machine.

    Returns:
        str: The IP address of the current machine.
    """
    hostname = socket.gethostname()
    addr = socket.gethostbyname(hostname)
    return addr


def get_subnet_mask(ip_address):
    """
    Get the subnet mask of the network interface associated with the given IP address.

    Args:
        ip_address (str): The IP address to find the subnet mask for.

    Returns:
        str: The subnet mask of the network interface.
    """
    # Get the list of network interfaces
    interfaces = netifaces.interfaces()

    # Iterate over the interfaces
    for interface in interfaces:
        # Get the address information for the interface
        addrs = netifaces.ifaddresses(interface)

        # Check if the interface has an IPv4 address
        if netifaces.AF_INET in addrs:
            # Get the IP address associated with the interface
            interface_ip = addrs[netifaces.AF_INET][0]['addr']

            # Check if the IP address matches the one we're looking for
            if interface_ip == ip_address:
                # Get the subnet mask
                mask = addrs[netifaces.AF_INET][0]['netmask']
                return mask

    # If we couldn't find the subnet mask, return None
    return None


def get_broadcast_ip(ip_address, subnet_mask):
    """
    Get the broadcast IP address of the network interface associated with the given IP address and subnet mask.

    Args:
        ip_address (str): The IP address of the network interface.
        subnet_mask (str): The subnet mask of the network interface.

    Returns:
        str: The broadcast IP address of the network interface.
    """
    # Convert the IP address and subnet mask to IPv4Network objects
    network = ipaddress.ip_network(f"{ip_address}/{subnet_mask}", strict=False)

    # Get the broadcast address
    broadcast_ip = str(network.broadcast_address)

    return broadcast_ip


def find_available_port(ip_address, start_port=1024, end_port=49151):
    """
    Find an available port for an application.

    Args:
        ip_address: (str): the ip address of the computer the server is running on
        start_port (int): The starting port number to check.
        end_port (int): The ending port number to check.

    Returns:
        int: The available port number.
    """
    for port in range(start_port, end_port):
        try:
            # Create a socket and try to bind to the port
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((ip_address, port))
            # If we reach this point, the port is available
            s.close()
            return port
        except OSError:
            # If the port is already in use, move on to the next one
            continue

    # If we've checked all the ports and haven't found one available,
    # raise an exception
    raise Exception("No available port found in the given range.")


def calculate_broadcast_ip(ip_address, subnet_mask):
    # Calculate the broadcast IP address
    try:
        ip_parts = list(map(int, ip_address.split('.')))
        mask_parts = list(map(int, subnet_mask.split('.')))
        broadcast_parts = [(ip_parts[i] | (~mask_parts[i] & 0xff)) for i in range(4)]
        return '.'.join(map(str, broadcast_parts))
    except ValueError:
        return None


# Function to broadcast offer messages
def broadcast_offer(udp_socket):
    ip_address, port = udp_socket.getsockname()
    subnet_mask = get_subnet_mask(ip_address)
    brod_ip = calculate_broadcast_ip(ip_address, subnet_mask)
    print("Server started, listening on IP address", ip_address, "waiting for players to join the game!")
    offer_message = (magic_cookie.encode('utf-8') + message_type.encode('utf-8') + server_name_encoded +
                     str(port).encode('utf-8'))
    start_time = time.time()  # Record the start time of the 10-second window
    curr_len = len(player_manager.get_players())  # how many players we have
    while curr_len == 0 or time.time() - start_time <= 10:  # checks if we don't have players yet or that 10 seconds
        # has passed from last join
        try:
            udp_socket.sendto(offer_message, (brod_ip, dest_port))
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
    broadcast_finished_event.set()


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

def get_udp_socket(ip_address, udp_port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.bind((ip_address, udp_port))  # Bind to the IP address
    return udp_socket


# Main function
def main():
    while True:
        ip_address = get_ip_address()
        udp_port = find_available_port(ip_address)
        udp_sock = get_udp_socket(ip_address, udp_port)

        # Start UDP broadcast thread
        udp_thread = threading.Thread(target=broadcast_offer, args=(udp_sock,))
        udp_thread.start()
        # Start TCP server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_port = find_available_port(ip_address)
            tcp_socket.bind((ip_address, tcp_port))
            tcp_socket.listen()
            print(f"Server listening on IP address {ip_address}, port {tcp_port}")

            # Accept incoming connections and handle clients
            while True:
                client_socket, address = tcp_socket.accept()
                client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
                client_handler.start()
                # Check if the broadcast has finished
                if broadcast_finished_event.is_set():
                    # Call start_game once the broadcast is finished
                    game_engine.is_game_over.clear()
                    start_game(tcp_socket)
                    break  # Exit the loop to stop accepting new connections
        game_engine.is_game_over.wait()
        print("Game over, sending out offer requests...")


if __name__ == "__main__":
    main()
