import random
import threading

from Client import Client


# Bot implementation
class Bot(Client):
    def __init__(self, player_name):
        super().__init__(f"BOT:{player_name}")
        true_answers = self.json_reader.get('true_options')
        false_answers = self.json_reader.get('false_options')
        self.answer_choices = true_answers + false_answers

    def receive_question(self):
        while self.running:
            data = self.server_socket.recv(4096)
            if not data:
                print("Server disconnected, listening for offer requests...")
                self.running = False
                break
            print(data.decode().strip())

            # Wait for user input, if received before the timer expires, cancel the timer
            user_input = random.choice(self.answer_choices)
            self.server_socket.sendall(user_input.encode() + b"\n")

