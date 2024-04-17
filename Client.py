import socket
import struct
import threading

from JsonReader import JSONReader

SERVER_NAME_LENGTH = 32
SERVER_PORT_LENGTH = 2


class Client:
    def __init__(self, player_name):
        self.player_name = player_name
        self.server_port = None
        self.server_socket = None
        self.udp_socket = None
        self.running = False
        self.json_reader = JSONReader()
        self.server_name = self.json_reader.get('server_name')

    def start(self):
        self.running = True
        self.listen_for_offers()
        self.connect_to_server()
        self.play_game()

    def listen_for_offers(self):
        udp_port = self.json_reader.get('dest_port')
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('', udp_port))
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        while self.running:
            message, address = self.udp_socket.recvfrom(4096)
            if self.parse_offer_message(message):
                print(
                    f"Received offer from server '{self.server_name}' at address {address[0]}, attempting to connect...")
                break

    def connect_to_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((self.server_name, self.server_port))
        self.server_socket.sendall(f"{self.player_name}\n".encode())

    def receive_question(self):
        while self.running:
            data = self.server_socket.recv(4096)
            if not data:
                print("Server disconnected, listening for offer requests...")
                self.running = False
                break
            print(data.decode().strip())

            # Start the timer for 10 seconds
            timer = threading.Timer(10, self.send_auto_answer)
            timer.start()

            # Wait for user input, if received before the timer expires, cancel the timer
            user_input = input("Enter your answer (or wait for auto answer in 10 seconds): ")
            timer.cancel()

            # Send user input to the server
            self.server_socket.sendall(user_input.encode() + b"\n")

    def send_auto_answer(self):
        # Send a default answer if the user hasn't provided one after 10 seconds
        default_answer = "Auto answer after 10 seconds"
        self.server_socket.sendall(default_answer.encode() + b"\n")

    def play_game(self):
        # Start listening for questions in a separate thread
        question_thread = threading.Thread(target=self.receive_question)
        question_thread.start()

    def parse_offer_message(self, message):
        if len(message) < 4 + 1 + SERVER_NAME_LENGTH + SERVER_PORT_LENGTH:
            return False

        real_magic_cookie = self.json_reader.get('magic_cookie')
        magic_cookie = struct.unpack('I', message[:4])[0]
        if magic_cookie != real_magic_cookie:
            return False

        offer_message_type = self.json_reader.get('message_type')
        message_type = struct.unpack('B', message[4:5])[0]
        if message_type != offer_message_type:
            return False

        server_name = message[5:5 + SERVER_NAME_LENGTH].decode().strip()
        if self.server_name != server_name:
            return False

        self.server_port = \
        struct.unpack('H', message[5 + SERVER_NAME_LENGTH:5 + SERVER_NAME_LENGTH + SERVER_PORT_LENGTH])[0]
        return True


# Example usage
client = Client("Alice")
client.start()
