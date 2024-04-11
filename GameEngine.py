import threading
import time

import Colors
from Colors import ANSI
import random
from ClientHandler import ClientHandler


class GameEngine:
    def __init__(self, player_manager, questions, true_answers, false_answers):
        self.round = 0
        self.player_manager = player_manager
        self.questions = questions
        self.socket = None
        self.client_answers = {}
        self.client_answers_lock = threading.Lock()  # Define the lock object
        self.true_answers = true_answers
        self.false_answers = false_answers
        self.is_game_over = threading.Event()

    def get_answers(self):
        end_time = time.time() + 10  # Set the end time for receiving answers (10 seconds from now)

        client_threads = []
        for player in self.player_manager.get_active_players():
            client_thread = ClientHandler(player, self.player_manager, self.client_answers,
                                          self.client_answers_lock)  # Pass the lock object to the client handler
            client_thread.start()
            client_threads.append(client_thread)

        for thread in client_threads:
            thread.join(end_time - time.time())

        return self.client_answers

    def send_message_to_clients(self, msg):
        print(msg)
        for player in self.player_manager.get_active_players():
            client_socket = player.get_socket()
            client_socket.sendall(msg.encode())

    def play_game(self, tcp_socket):
        self.socket = tcp_socket
        random.shuffle(self.questions)
        while self.round < len(self.questions):
            question = self.questions[self.round]
            self.play_round(question)
            self.round += 1

    def game_over(self, winner):
        msg = f"Game over! \nCongratulations to the winner : {ANSI.PINK}{winner.get_name()} {ANSI.CROWN}{ANSI.RESET}!"
        self.send_message_to_clients(msg)
        self.is_game_over.set()

    def handle_answers(self, answers, answer):
        correct_players = []
        incorrect_players = []
        for player, player_answer in answers.items():
            if (answer and player_answer in self.true_answers) or (not answer and player_answer in self.false_answers):
                correct_players.append(player)
            else:
                incorrect_players.append(player)
        return correct_players, incorrect_players

    def play_round(self, question_answer):
        player_names = ", ".join([player.get_name() for player in self.player_manager.get_active_players()])
        round_msg = f"{ANSI.CYAN.value}Round {self.round}{ANSI.RESET.value}"
        player_msg = f"{ANSI.BLUE.value}, played by {player_names}{ANSI.RESET.value}"
        question_msg = f"{ANSI.MAGENTA.value}\nThe next question is...{ANSI.RESET.value}"
        question_body = f"\nTrue or False: {question_answer["question"]}"
        msg = f"{round_msg}{player_msg}{question_msg}{question_body}"
        self.send_message_to_clients(msg)
        answers = self.get_answers()
        correct_players, incorrect_players = self.handle_answers(answers, question_answer)
        # no one answered / no one answered correct
        if len(correct_players) == 0:
            self.send_message_to_clients(f"{ANSI.RED.value} No one answered correctly {ANSI.SAD_FACE.value} "
                                         f"playing another round {ANSI.RESET.value}")
        elif len(correct_players) == 1:
            self.game_over(correct_players[0])
            # finish game , correct player is the winner
        # multiple correct answers
        else:
            msg = ""
            for player in self.player_manager.get_active_players():
                if player in correct_players:
                    msg += f"{ANSI.GREEN.value} {player.name} is correct ! {ANSI.THUMBS_UP} {ANSI.RESET.value}"
                else:
                    msg += f"{ANSI.RED.value} {player.name} is incorrect ! {ANSI.THUMBS_UP} {ANSI.RESET.value}"

            self.player_manager.set_active_players(correct_players)

            self.send_message_to_clients(msg)
