import socket
import threading
import time
import random
from Colors import ANSI
from ClientHandler import ClientHandler
from PlayerManager import PlayerManager
from Player import Player


class GameEngine:
    """
    Class representing the game engine for managing the gameplay.

    Attributes:
        round (int): The current round of the game.
        player_manager (PlayerManager): The player manager managing the players.
        questions (list): List of questions for the game.
        socket (socket): The TCP socket used for communication with the clients.
        client_answers_lock (threading.Lock): Lock object for synchronizing access to client answers.
        true_answers (list): List of true answers.
        false_answers (list): List of false answers.
        is_game_over (threading.Event): Event object to signal when the game is over.
    """

    def __init__(self, player_manager, questions, true_answers, false_answers):
        """
        Initializes the GameEngine with the provided parameters.

        Args:
            player_manager (PlayerManager): The player manager managing the players.
            questions (list): List of questions for the game.
            true_answers (list): List of true answers.
            false_answers (list): List of false answers.
        """
        self.round = 0
        self.player_manager = player_manager
        self.questions = questions
        self.socket = None
        self.true_answers = true_answers
        self.false_answers = false_answers
        self.is_game_over = threading.Event()

    def get_answers(self):
        """
        Receives answers from clients.

        Returns:
            dict: Dictionary containing client answers.
        """
        end_time = time.time() + 10  # Set the end time for receiving answers (10 seconds from now)

        client_threads = []
        client_answers = {}
        client_answers_lock = threading.Lock()
        for player in self.player_manager.get_active_players():
            client_thread = ClientHandler(player, self.player_manager, client_answers, client_answers_lock)
            client_thread.start()
            client_threads.append(client_thread)

        for thread in client_threads:
            thread.join(end_time - time.time())

        return client_answers

    def send_message_to_clients(self, msg):
        """
        Sends a message to all active clients.

        Args:
            msg (str): The message to send to clients.
        """
        print(msg)
        for player in self.player_manager.get_active_players():
            client_socket = player.get_socket()
            try:
                client_socket.sendall(msg.encode())

            except socket.error as se:
                print(f"A socket error occurred {se}")
                print(f'player {player.get_name()} has been kicked')
                self.player_manager.update_player_status(player)

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                print(f'player {player.get_name()} has been kicked')
                self.player_manager.update_player_status(player)

    def play_game(self, tcp_socket):
        """
        Plays the game.

        Args:
            tcp_socket (socket.socket): The TCP socket for communication with clients.
        """
        self.socket = tcp_socket
        random.shuffle(self.questions)
        while self.round < len(self.questions) and not self.is_game_over:
            question = self.questions[self.round]
            self.play_round(question)
            self.round += 1

    def game_over(self, winner):
        """
        Handles the end of the game.

        Args:
            winner (Player): The winning player.
        """
        msg = f"Game over! \nCongratulations to the winner : {ANSI.PINK.value}{winner.get_name()} {ANSI.CROWN.value}{ANSI.RESET.value}!"
        self.send_message_to_clients(msg)
        self.is_game_over.set()

    def handle_answers(self, answers, answer):
        """
        Handles client answers.

        Args:
            answers (dict): Dictionary containing client answers.
            answer (str): The correct answer.

        Returns:
            list: List of correct players.
            list: List of incorrect players.
        """
        correct_players = []
        incorrect_players = []
        for player, player_answer in answers.items():
            if (answer and player_answer in self.true_answers) or (not answer and player_answer in self.false_answers):
                correct_players.append(player)
            else:
                incorrect_players.append(player)
        return correct_players, incorrect_players

    def build_round_question_msg(self, question):
        """
        Builds a question message for a round of the game.
        Args:
            question (dict): a dict of the question and its answer.
        Returns:
            (string) the round msg for the players
        """
        player_names = ", ".join([player.get_name() for player in self.player_manager.get_active_players()])
        round_msg = f"{ANSI.CYAN.value}Round {self.round}{ANSI.RESET.value}"
        player_msg = f"{ANSI.BLUE.value}, played by {player_names}{ANSI.RESET.value}"
        question_msg = f"{ANSI.MAGENTA.value}\nThe next question is...{ANSI.RESET.value}"
        question_body = f"\nTrue or False: {question['question']}"
        msg = f"{round_msg}{player_msg}{question_msg}{question_body}"
        return msg

    def play_round(self, question):
        """
        Plays a round of the game.
        Args:
            question (dict): a dict of the question and its answer.
        """
        round_msg = self.build_round_question_msg(question)
        self.send_message_to_clients(round_msg)
        answers = self.get_answers()
        correct_players, incorrect_players = self.handle_answers(answers, question['is_true'])
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
                    msg += f"{ANSI.GREEN.value} {player.name} is correct ! {ANSI.THUMBS_UP.value} {ANSI.RESET.value}"
                else:
                    msg += f"{ANSI.RED.value} {player.name} is incorrect ! {ANSI.THUMBS_UP.value} {ANSI.RESET.value}"

            self.player_manager.set_active_players(correct_players)
            self.send_message_to_clients(msg)
