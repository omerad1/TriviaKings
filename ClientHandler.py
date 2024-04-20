import threading
from Player import Player
from Colors import ANSI


class ClientHandler(threading.Thread):
    """
    Class representing a thread for handling client interactions.

    Attributes:
        player (Player): The player associated with the client.
        player_manager (PlayerManager): The player manager managing the players.
        client_answers (dict): Dictionary to store client answers.
        client_answers_lock (threading.Lock): Lock object for synchronizing access to client answers.
    """

    def __init__(self, player, player_manager, client_answers, client_answers_lock):
        """
        Initializes the ClientHandler.

        Args:
            player (Player): The player associated with the client.
            player_manager (PlayerManager.PlayerManager): The player manager managing the players.
            client_answers (dict): Dictionary to store client answers.
            client_answers_lock (threading.Lock): Lock object for synchronizing access to client answers.
        """
        super().__init__()
        self.player = player
        self.player_manager = player_manager
        self.client_answers = client_answers
        self.client_answers_lock = client_answers_lock

    def run(self):
        """
        Runs the thread to handle client interactions.
        """
        name = self.player.get_name()
        client_socket = self.player.get_socket()
        try:
            answer = client_socket.recv(1024).decode()
            # Use thread-safe access to the shared dictionary
            with self.client_answers_lock:
                self.client_answers[self.player] = answer
        except Exception as e:
            print(f"{ANSI.RED.value}Socket error when receiving receiving answer from {name}: {e}{ANSI.RESET.value}")
            # Use thread-safe access to the shared dictionary
            with self.client_answers_lock:
                self.client_answers[self.player] = None
