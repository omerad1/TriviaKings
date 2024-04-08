import threading
import time


class ClientHandler(threading.Thread):
    def __init__(self, player, player_manager, client_answers,client_answers_lock):
        super().__init__()
        self.player = player
        self.player_manager = player_manager
        self.client_answers = client_answers
        self.client_answers_lock = client_answers_lock

    def run(self):
        name = self.player.get_name()
        client_socket = self.player.get_socket()
        try:
            answer = client_socket.recv(1024).decode()
            # Use thread-safe access to the shared dictionary
            with self.client_answers_lock:
                self.client_answers[self.player] = answer
        except Exception as e:
            print(f"Error receiving answer from {name}: {e}")
            # Use thread-safe access to the shared dictionary
            with self.client_answers_lock:
                self.client_answers[self.player] = None



