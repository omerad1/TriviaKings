import socket
import threading
import time
import random
from Colors import ANSI
from ClientHandler import ClientHandler
from PlayerManager import PlayerManager
from Player import Player
from GameStatistics import GameStatistics


class GameEngine:
    """
    Class representing the game engine for managing the gameplay.

    Attributes:
        round (int): The current round of the game.
        player_manager (PlayerManager): The player manager managing the players.
        questions (list): List of questions for the game.
        socket (socket): The TCP socket used for communication with the clients.
        true_answers (list): List of true answers.
        false_answers (list): List of false answers.
    """

    def __init__(self, player_manager, questions, true_answers, false_answers, server_name,
                 question_prefix, client_lose_msg):
        """
        Initializes the GameEngine with the provided parameters.

        Args:
            player_manager (PlayerManager): The player manager managing the players.
            questions (list): List of questions for the game.
            true_answers (list): List of true answers.
            false_answers (list): List of false answers.
            server_name (string): the server name.
        """
        self.round = 0
        self.server_name = server_name
        self.player_manager = player_manager
        self.questions = questions
        self.socket = None
        self.true_answers = true_answers
        self.false_answers = false_answers
        self.game_statistics = GameStatistics()

        self.question_prefix = question_prefix
        self.client_lose_message = client_lose_msg

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

    def kick_player(self, player):
        print(f'player {player.get_name()} has been kicked')
        self.player_manager.kick_player(player)

    def handle_client_send(self, player, msg):
        client_socket = player.get_socket()
        try:
            client_socket.sendall(msg.encode())
        except socket.error as se:
            print(f'Socket error happened when sending player {player.get_name()} a message, error: {se}')
            self.player_manager.kick_player(player)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.kick_player(player)

    def send_message_to_clients(self, msg):
        """
        Sends a message to all active clients.

        Args:
            msg (str): The message to send to clients.
        """
        print(msg)
        for player in self.player_manager.get_players():
            self.handle_client_send(player, msg)

    def send_welcome_message(self):
        """
        Send the welcome message to all connected players.

        This method is called at the start of the game to greet the players and
        provide information about the game.
        """
        welcome_message = f"Welcome to the {self.server_name} server, where we are answering trivia questions!\n"
        players = self.player_manager.get_active_players()
        for i, player in enumerate(players, 1):
            welcome_message += f"Player {i}: {player.get_name()}\n"
        print(welcome_message)
        for player in players:
            self.handle_client_send(player, welcome_message)

    def play_game(self, tcp_socket):
        """
        Plays the game.

        Args:
            tcp_socket (socket.socket): The TCP socket for communication with clients.
        """
        for player in self.player_manager.get_active_players():
            print(f"player {player}")
            self.game_statistics.add_player(player)
        self.send_welcome_message()
        time.sleep(1)
        self.socket = tcp_socket
        random.shuffle(self.questions)
        winner = None
        while self.round < len(self.questions) and len(self.player_manager.get_active_players()) > 0:
            question = self.questions[self.round]
            winner = self.play_round(question)
            if winner is not None:
                break
            self.round += 1

        if self.round == len(self.questions):
            msg = f"Were out of questions, the game is over {ANSI.SAD_FACE.value}"
            print(msg)
            self.send_message_to_clients(msg)
        elif len(self.player_manager.get_active_players()) == 0:
            print(f"Were out of players, game is over {ANSI.SAD_FACE.value}")
        elif winner is not None:
            self.game_over(winner)

    def game_over(self, winner):
        """
        Handles the end of the game.

        Args:
            winner (Player): The winning player.
        """
        self.game_statistics.update_player(winner,"games_won")
        msg = (f"Game over! \nCongratulations to the winner : {ANSI.PINK.value}{winner.get_name()}"
               f" {ANSI.CROWN.value}{ANSI.RESET.value}!")
        self.send_message_to_clients(msg)

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
        print(f'The correct answer was {answer}')
        for player, player_answer in answers.items():
            print(f'Player: {player.get_name()} answered: {player_answer}')
            if player_answer is None:
                self.kick_player(player)
            elif (answer and player_answer in self.true_answers) or (
                    not answer and player_answer in self.false_answers):
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
        round_msg = f"{ANSI.CYAN.value}Round {(self.round + 1)}{ANSI.RESET.value}"
        player_msg = f"{ANSI.BLUE.value}, played by {player_names}{ANSI.RESET.value}"
        question_msg = f"{ANSI.MAGENTA.value}\nThe next question is...{ANSI.RESET.value}"
        question_body = f"\n{self.question_prefix}: {question['question']}"
        msg = f"{round_msg}{player_msg}{question_msg}{question_body}"
        return msg

    def update_players_statistics(self, correct, incorrect, question):
        for player in correct:
            self.game_statistics.update_player(player, "correct_answers")
        for player in incorrect: self.game_statistics.update_player(player, "incorrect_answers")
        self.game_statistics.update_question(question["question"], len(correct), len(incorrect))

    def send_message_to_losers(self, losers):
        msg = f'{ANSI.RED.value}{self.client_lose_message}{ANSI.SAD_FACE.value}{ANSI.RESET.value}'
        for player in losers:
            self.handle_client_send(player, msg)

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

        self.update_players_statistics(correct_players, incorrect_players, question)  # update the game statistics

        # no one answered / no one answered correct
        if len(correct_players) == 0:
            self.send_message_to_clients(f"{ANSI.RED.value}No one answered correctly {ANSI.SAD_FACE.value} "
                                         f"playing another round {ANSI.RESET.value}")
        # There is a winner
        elif len(correct_players) == 1:
            return correct_players[0]

        # multiple correct answers
        else:
            msg = ""
            for player in self.player_manager.get_active_players():
                if player in correct_players:
                    msg += f"{ANSI.GREEN.value}{player.name} is correct ! {ANSI.THUMBS_UP.value} {ANSI.RESET.value}\n"
                else:
                    msg += f"{ANSI.RED.value}{player.name} is incorrect ! {ANSI.THUMBS_DOWN.value} {ANSI.RESET.value}\n"

            self.player_manager.set_active_players(correct_players)
            self.send_message_to_clients(msg)
            self.send_message_to_losers(incorrect_players)

        return None
