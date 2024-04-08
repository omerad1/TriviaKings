import threading
import time
from Colors import ANSIColor
import random
from ClientHandler import ClientHandler

class GameEngine:
    def __init__(self, player_manager, questions):
        self.round = 0
        self.player_manager = player_manager
        self.questions = questions
        self.socket = None

    def send_message_to_clients(self, msg):
        for player in self.player_manager.get_players():
            client_socket = player.get_socket()
            client_socket.sendall(msg.encode())

    def play_game(self, tcp_socket):
        self.socket = tcp_socket
        random.shuffle(self.questions)
        while len(self.player_manager.get_active_players()) > 1 and self.round < len(self.questions):
            question = self.questions[self.round]
            self.play_round(question)

    def get_answers(self):
        client_answers = {}
        end_time = time.time() + 10  # Set the end time for receiving answers (10 seconds from now)

        client_threads = []
        for player in self.player_manager.get_active_players():
            client_thread = ClientHandler(player, self.player_manager, client_answers)
            client_thread.start()
            client_threads.append(client_thread)

        for thread in client_threads:
            thread.join(end_time - time.time())

        return client_answers

    def play_round(self, question):
        player_names = ", ".join([player.get_name() for player in self.player_manager.get_active_players()])
        round_msg = f"{ANSIColor.CYAN.value}Round {self.round}{ANSIColor.RESET.value}"
        player_msg = f"{ANSIColor.BLUE.value}, played by {player_names}{ANSIColor.RESET.value}"
        question_msg = f"{ANSIColor.MAGENTA.value}\nThe next question is...{ANSIColor.RESET.value}"
        question_body = f"\nTrue or False: {question}"
        msg = f"{round_msg}{player_msg}{question_msg}{question_body}"

        print(msg)
        self.send_message_to_clients(msg)
        answers = self.get_answers()
