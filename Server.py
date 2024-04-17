import threading
import time

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
        self.server_name_encoded = self.config_reader.get('server_name').encode('utf-8').ljust(32)
        self.dest_port = self.config_reader.get('dest_port')
        self.magic_cookie = self.config_reader.get('magic_cookie')
        self.message_type = self.config_reader.get('message_type')
        questions = self.config_reader.get('questions')
        true_options = self.config_reader.get('true_options')
        false_options = self.config_reader.get('false_options')
        self.game_engine = GameEngine(self.player_manager, questions, true_options, false_options)

    def broadcast_offer(self, udp_socket):
        """
        Broadcast offer messages to clients using the UDP socket.

        This method runs in a separate thread and broadcasts the offer message every second
        until either a new player joins or 10 seconds have passed since the last join.

        Args:
            udp_socket (socket.socket): The UDP socket used for broadcasting.
        """
        print(
            f"{Colors.ANSI.MAGENTA.value}Server started, listening on IP address \n{Colors.ANSI.RESET.value}{self.ip_address} waiting for players to join the game!")
        offer_message = (
                self.magic_cookie.encode('utf-8') + self.message_type.encode('utf-8') + self.server_name_encoded +
                str(self.tcp_port).encode('utf-8'))
        start_time = time.time()
        curr_len = len(self.player_manager.get_players())
        while curr_len == 0 or time.time() - start_time <= 10:
            try:
                udp_socket.sendto(offer_message, (self.ip_address, self.dest_port))
            except OSError as e:
                print("Error:", e)
                continue
            time.sleep(1)
            if len(self.player_manager.get_players()) > curr_len:
                curr_len = len(self.player_manager.get_players())
                print("New player joined.")
                start_time = time.time()
        print("No new players joined within 10 seconds. Stopping broadcast.")
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

    def start_game(self, tcp_socket):
        """
        Start the trivia game.

        This method is called after the broadcast has finished and players have connected.
        It sends the welcome message to all clients and starts the game engine.

        Args:
            tcp_socket (socket.socket): The TCP socket used for the game server.
        """
        self.send_welcome_message()
        self.game_engine.play_game(tcp_socket)

    def send_welcome_message(self):
        """
        Send the welcome message to all connected players.

        This method is called at the start of the game to greet the players and
        provide information about the game.
        """
        welcome_message = f"Welcome to the {self.server_name_encoded.decode().strip()} server, where we are answering trivia questions!\n"
        players = self.player_manager.get_players()
        for i, player in enumerate(players, 1):
            welcome_message += f"Player {i}: {player.get_name()}\n"
        print(welcome_message)
        for player in players:
            client_socket = player.get_socket()
            client_socket.sendall(welcome_message.encode())

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

    def start(self):
        """
        Start the trivia server.

        This method runs the main loop of the server, handling UDP broadcasts and TCP connections.
        It continues to run until the game is over.
        """
        while True:
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

                # Once broadcast is finished, start the game
                self.game_engine.is_game_over.clear()
                self.start_game(tcp_socket)

            self.game_engine.is_game_over.wait()
            print("Game over, sending out offer requests...")


server = Server()
server.start()
