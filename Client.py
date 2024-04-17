import socket
import threading
import time
import Colors
from JsonReader import JSONReader

SERVER_NAME_LENGTH = 32
SERVER_PORT_LENGTH = 4


class Client:
    def __init__(self, player_name):
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
        self.current_answer = "-1"

    def start(self):
        self.running = True
        print(f"Starting client for {Colors.ANSI.BLUE.value} {self.player_name} {Colors.ANSI.RESET.value} listening "
              f"for offers...")
        self.listen_for_offers()
        self.connect_to_server()
        self.get_welcome_message()
        self.play_game()

    def listen_for_offers(self):
        udp_port = self.json_reader.get('dest_port')
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
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
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((self.server_address, self.server_port))
        self.server_socket.sendall(f"{self.player_name}\n".encode())
        print(f"Connected to server at address: {self.server_address}, port: {self.server_port}\n"
              f"waiting for game to start... ")

    def play_game(self):
        # Create an event object to signal when the game should stop
        stop_event = threading.Event()

        # Define the game loop function
        def game_loop():
            while not stop_event.is_set():
                data = self.server_socket.recv(4096)
                if not data:
                    print("Server disconnected, listening for offer requests...")
                    stop_event.set()  # Set the event to stop the game loop
                    break
                msg = data.decode()
                print(msg)
                if self.game_over_message in msg:
                    print(f"{Colors.ANSI.RED.value} Senior {self.player_name} the game is over, it was a lovely game "
                          f"{Colors.ANSI.RESET.value}")
                    stop_event.set()  # Set the event to stop the game loop
                    break

                # Wait for user input with a 10-second timeout
                self.current_answer = None
                self.wait_for_input(10)

                # If user input is not None, send it to the server
                if self.current_answer is not None:
                    self.server_socket.sendall(self.current_answer.encode('utf-8'))
                else:
                    # Send a default answer if the user hasn't provided one after 10 seconds
                    self.send_auto_answer()

        # Create a thread for the game loop
        game_thread = threading.Thread(target=game_loop)
        game_thread.start()

        # Wait for the game loop to finish
        game_thread.join()

        # Close the server socket when the game ends
        self.server_socket.close()

    def get_welcome_message(self):
        data = self.server_socket.recv(4096)
        print(data.decode()) if data else None

    def send_auto_answer(self):
        # Send a default answer if the user hasn't provided one after 10 seconds
        default_answer = "Auto answer after 10 seconds"
        self.server_socket.sendall(default_answer.encode())

    def parse_offer_message(self, message):
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

    def wait_for_input(self, timeout):
        """
        Wait for user input with a timeout.

        Args:
            timeout (int): The timeout period in seconds.

        Returns:
            str or None: The user input if received within the timeout, else None.
        """
        print("Waiting for input...")
        start_time = time.time()

        # Function to read input asynchronously
        def input_thread_func():
            try:
                ans = input("Enter your answer (you have 10 seconds !): ")
                print(ans)
                self.current_answer = ans
            except Exception as e:
                print(f"Error in input_thread_func: {e}")
                return None

        input_thread = threading.Thread(target=input_thread_func)
        input_thread.start()
        input_thread.join(timeout - (time.time() - start_time))  # Wait for the remaining time

        if input_thread.is_alive():
            print("No input received, continuing ...")
            self.current_answer = "-1"
        else:
            print("Answer received: " + self.current_answer)


# Example usage
client = Client("Crime Adam")
client.start()
