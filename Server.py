import threading
import time
import netifaces
import Colors
from JsonReader import JSONReader
from Player import Player
from PlayerManager import PlayerManager
from GameEngine import GameEngine
import socket
import ipaddress


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
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((ip_address, port))
            s.close()
            return port
        except OSError:
            continue
    raise Exception("No available port found in the given range.")


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
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            interface_ip = addrs[netifaces.AF_INET][0]['addr']
            if interface_ip == ip_address:
                mask = addrs[netifaces.AF_INET][0]['netmask']
                return mask
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
    network = ipaddress.ip_network(f"{ip_address}/{subnet_mask}", strict=False)
    broadcast_ip = str(network.broadcast_address)
    return broadcast_ip


class Server:
    """
    A server implementation for a trivia game.

    The server listens for UDP broadcasts to receive connection requests from clients,
    and then handles TCP connections to manage the trivia game.

    Attributes:
        config_reader (JSONReader): An instance of the JSONReader class used to read the configuration file.
        player_manager (PlayerManager): An instance of the PlayerManager class used to manage the players.
        game_engine (GameEngine): An instance of the GameEngine class used to manage the game logic.
        broadcast_finished_event (threading.Event): An event used to signal that the broadcast has finished.
        ip_address (str): The IP address of the server.
        udp_port (int): The UDP port used for broadcasting offers.
        tcp_port (int): The TCP port used for the game server.
        server_name_encoded (bytes): The encoded and padded server name.
    """

    def __init__(self, config_file='config.json'):
        self.config_reader = JSONReader(config_file)
        self.player_manager = PlayerManager()
        self.broadcast_finished_event = threading.Event()
        self.ip_address = get_ip_address()
        self.udp_port = find_available_port(self.ip_address)
        self.tcp_port = find_available_port(self.ip_address)
        self.server_name = self.config_reader.get('server_name')
        self.dest_port = self.config_reader.get('dest_port')
        self.magic_cookie = self.config_reader.get('magic_cookie')
        self.message_type = self.config_reader.get('message_type')
        self.questions = self.config_reader.get('questions')
        self.true_options = self.config_reader.get('true_options')
        self.false_options = self.config_reader.get('false_options')
        self.game_engine = GameEngine(self.player_manager, self.questions, self.true_options, self.false_options,
                                      self.server_name)

    def broadcast_offer(self, udp_socket):
        """
        Broadcast offer messages to clients using the UDP socket.

        This method runs in a separate thread and broadcasts the offer message every second
        until either a new player joins or 10 seconds have passed since the last join.

        Args:
            udp_socket (socket.socket): The UDP socket used for broadcasting.
        """
        subnet_mask = get_subnet_mask(self.ip_address)
        brod_ip = get_broadcast_ip(self.ip_address, subnet_mask)
        print(f"{Colors.ANSI.MAGENTA.value}Server started, listening on IP address \n"
              f"{Colors.ANSI.RESET.value}{self.ip_address} waiting for players to join the game!")
        offer_message = (
                self.magic_cookie.encode('utf-8') + self.message_type.encode('utf-8') +
                self.server_name.encode('utf-8').ljust(32) + str(self.tcp_port).encode('utf-8'))
        start_time = time.time()
        curr_len = len(self.player_manager.get_players())
        while curr_len == 0 or time.time() - start_time <= 10:
            try:
                udp_socket.sendto(offer_message, (brod_ip, self.dest_port))
            except OSError as e:
                print("Error:", e)
                continue
            time.sleep(1)
            if len(self.player_manager.get_players()) > curr_len:
                curr_len = len(self.player_manager.get_players())
                start_time = time.time()

        print("No new players joined within 10 seconds. Stopping broadcast.")
        udp_socket.close()
        self.broadcast_finished_event.set()

    def handle_client(self, client_socket, address):
        """
        Handle a client connection.

        This method is called when a new client connects to the server over TCP.
        It receives the player name from the client and adds the player to the PlayerManager.

        Args:
            client_socket (socket.socket): The client socket.
            address (tuple): The client address.
        """
        try:
            player_name = client_socket.recv(1024).decode().strip()
            player = Player(player_name, client_socket, True)
            self.player_manager.add_player(player)
            print(f"Player {player_name} connected from {address}")
        except Exception as e:
            print(f"Error handling client: {e}")

    def get_udp_socket(self):
        """
        Create and configure the UDP socket for broadcasting offers.

        Returns:
            socket.socket: The configured UDP socket.
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.bind((self.ip_address, self.udp_port))
        return udp_socket

    def reset_game(self):
        """
        Resets the game.

        This method is called once the game is over, it resets the server data and starts over.
        """
        self.player_manager = PlayerManager()
        self.udp_port = find_available_port(self.ip_address)
        self.tcp_port = find_available_port(self.ip_address)
        self.game_engine = GameEngine(self.player_manager, self.questions, self.true_options,
                                      self.false_options, self.server_name)
        self.broadcast_finished_event.clear()
        self.start()

    def start(self):
        """
        Start the trivia server.

        This method runs the main loop of the server, handling UDP broadcasts and TCP connections.
        It continues to run until the game is over.
        """
        udp_socket = self.get_udp_socket()

        # Start UDP broadcast thread
        udp_thread = threading.Thread(target=self.broadcast_offer, args=(udp_socket,))
        udp_thread.start()

        # Start TCP server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_socket.bind((self.ip_address, self.tcp_port))
            tcp_socket.listen()
            print(f"Server listening on IP address {self.ip_address}, port {self.tcp_port}")

            while not self.broadcast_finished_event.is_set():
                tcp_socket.settimeout(1)  # Set a timeout of 1 second
                try:
                    client_socket, address = tcp_socket.accept()
                except socket.timeout:
                    continue  # Continue waiting if no client connects within 1 second

                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_handler.start()

            self.game_engine.play_game(tcp_socket)

        self.reset_game()


if __name__ == '__main__':
    server = Server()
    server.start()
