import select
import socket
import sys
import threading
import Colors
from JsonReader import JSONReader

SERVER_NAME_LENGTH = 32
SERVER_PORT_LENGTH = 4


class Client(threading.Thread):
    """
    Client class for the game.

    This class represents a client that connects to a server and plays the game.
    It inherits from the `threading.Thread` class to allow for concurrent execution.

    Attributes:
        player_name (str): The name of the player.
        game_over_message (str): The message indicating the end of the game.
        server_port (int): The port number of the server.
        server_socket (socket.socket): The socket used for communication with the server.
        udp_socket (socket.socket): The UDP socket used for receiving offers.
        running (bool): A flag indicating whether the client is running or not.
        json_reader (JsonReader): An instance of the JsonReader class for reading configuration data.
        server_name (str): The name of the server.
        server_address (str): The IP address of the server.
        current_answer (str): The current answer provided by the user or bot.
    """

    def __init__(self, player_name):
        """
        Initialize the Client object.

        Args:
            player_name (str): The name of the player.
        """
        super().__init__()
        config_reader = JSONReader("config.json")
        self.game_over_message = config_reader.get("game_over_message")
        self.player_name = player_name
        self.server_port = None
        self.server_socket = None
        self.udp_socket = None
        self.running = False
        self.json_reader = JSONReader()
        self.server_name = self.json_reader.get('server_name')
        self.server_address = None
        self.current_answer = None

    def run(self):
        """
        Run the client.

        This method is the entry point for the client thread.
        It starts the client, listens for offers, connects to the server, gets the welcome message, and starts the game.
        """
        try:
            self.running = True
            print(
                f"Starting client for {Colors.ANSI.BLUE.value} {self.player_name} {Colors.ANSI.RESET.value} listening for offers...")
            self.listen_for_offers()
            self.connect_to_server()
            self.get_welcome_message()
            self.play_game()
        except socket.error as e:
            print(f"Server connection crushed: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                print("Server socket closed.")
            if self.udp_socket:
                self.udp_socket.close()
                print("UDP socket closed.")

    def listen_for_offers(self):
        """
        Listen for offers from the server using a UDP socket.

        This method creates a UDP socket, binds it to the destination port specified in the configuration,
        and listens for offer messages from the server. Once an offer message is received and parsed successfully,
        it breaks out of the loop and attempts to connect to the server.
        """
        udp_port = self.json_reader.get('dest_port')
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.udp_socket.bind(('', udp_port))
        while self.running:
            message, address = self.udp_socket.recvfrom(4096)
            self.server_address = address[0]
            if self.parse_offer_message(message):
                print(
                    f"Received offer from server '{Colors.ANSI.MAGENTA.value} {self.server_name} {Colors.ANSI.RESET.value}' at address {self.server_address}, "
                    f"attempting to connect...")
                break

    def connect_to_server(self):
        """
        Connect to the server using a TCP socket.

        This method creates a TCP socket, connects to the server address and port obtained from the offer message,
        sends the player's name to the server, and prints a message indicating the successful connection.
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((self.server_address, self.server_port))
        self.server_socket.sendall(f"{self.player_name}\n".encode())
        print(f"Connected to server at address: {self.server_address}, port: {self.server_port}\n"
              f"waiting for game to start... ")

    def play_game(self):
        """
        Play the game by receiving messages from the server, handling user input, and sending responses.

        This method is the main game loop. It receives messages from the server, prints them, checks for the game over
        message, prompts the user for input if a question is asked, and sends the user's answer or a default answer
        to the server. The loop continues until the game is over or the server disconnects.
        """
        stop_event = threading.Event()

        while not stop_event.is_set():
            data = self.server_socket.recv(4096)
            if not data:
                print("Server disconnected, finishing game...")
                stop_event.set()  # Set the event to stop the game loop
                break

            msg = data.decode()
            print(msg)

            if self.game_over_message in msg:
                print(f"{Colors.ANSI.RED.value}Senior {self.player_name} the game is over, it was a lovely game!"
                      f"{Colors.ANSI.RESET.value}")
                stop_event.set()  # Set the event to stop the game loop
                break

            if "True or False" not in msg:
                continue

            self.current_answer = None
            self.wait_for_input(10, msg)

            # If user input is not None, send it to the server
            if self.current_answer is not None:
                print(f"Sending answer: {self.current_answer}")
                self.server_socket.sendall(self.current_answer.encode())
            # Send a default answer if the user hasn't provided one after 10 seconds
            else:
                print("Sending default answer")
                self.server_socket.sendall("".encode())

        # Close the server socket when the game ends
        self.server_socket.close()

    def get_welcome_message(self):
        """
        Receive and print the welcome message from the server.

        This method repeatedly receives data from the server until it receives a message containing the string 'Welcome'.
        It prints any messages received from the server.
        """
        msg = None
        while not msg or 'Welcome' not in msg:
            data = self.server_socket.recv(4096)
            if data:
                msg = data.decode()
                print(msg)

    def wait_for_input(self, timeout, msg):
        """
        Wait for user input with a timeout.

        Args:
            timeout (int): The timeout period in seconds.

        Returns:
            str or None: The user input if received within the timeout, else None.

        This method prompts the user to enter an answer, waits for the specified timeout period for user input,
        and stores the input in the `current_answer` attribute. If no input is received within the timeout,
        it prints a message indicating that no input was received.
        :param timeout: the timeout for waiting to the client input
        :param msg: the question from the server
        """
        self.current_answer = None
        try:
            print(f"{Colors.ANSI.GREEN.value}Enter your answer{Colors.ANSI.RESET.value} (you have 10 seconds !):")
            inputs, _, _ = select.select([sys.stdin], [], [], timeout)
            if inputs:
                ans = sys.stdin.readline().strip()
                self.current_answer = ans
        except TimeoutError:
            print("No input received within 10 seconds.")

    def parse_offer_message(self, message):
        """
        Parse an offer message from the server.

        Args:
            message (bytes): The offer message received from the server.

        Returns:
            bool: True if the offer message is valid and contains the expected data, False otherwise.

        This method parses the offer message received from the server and validates its contents against the expected
        format and configuration data. If the message is valid, it extracts the server port from the message and
        returns True. Otherwise, it returns False.
        """
        if len(message) < 4 + 1 + SERVER_NAME_LENGTH + SERVER_PORT_LENGTH:
            return False

        real_magic_cookie = self.json_reader.get('magic_cookie')
        magic_cookie = message[:10].decode('utf-8')
        if magic_cookie != real_magic_cookie:
            return False

        offer_message_type = self.json_reader.get('message_type')
        message_type = message[10:13].decode('utf-8')
        if message_type != offer_message_type:
            return False

        server_name = message[13:13 + SERVER_NAME_LENGTH].decode().strip()
        if self.server_name != server_name:
            return False

        self.server_port = int(message[13 + SERVER_NAME_LENGTH: 13 + SERVER_NAME_LENGTH + SERVER_PORT_LENGTH].decode())
        return True


if __name__ == '__main__':
    client_name = sys.argv[1]
    client = Client(client_name)
    client.start()
