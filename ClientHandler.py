import threading
import time


class ClientHandler(threading.Thread):
    def __init__(self, player, player_manager, client_answers):
        super().__init__()
        self.player = player
        self.player_manager = player_manager
        self.client_answers = client_answers

    def run(self):
        name = self.player.get_name()
        client_socket = self.player.get_socket()
        try:
            answer = client_socket.recv(1024).decode()
            self.client_answers[name] = answer
        except Exception as e:
            print(f"Error receiving answer from {name}: {e}")
            self.client_answers[name] = None


def get_answers(self):
    client_answers = {}
    end_time = time.time() + 10  # Set the end time for receiving answers (10 seconds from now)

    client_threads = []
    for player in self.player_manager.get_active_players():
        client_socket = player.get_socket()
        client_thread = ClientHandler(client_socket, self.player_manager, client_answers)
        client_thread.start()
        client_threads.append(client_thread)

    for thread in client_threads:
        thread.join(end_time - time.time())

    return client_answers
