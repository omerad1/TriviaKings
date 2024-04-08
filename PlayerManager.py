import random
import threading


class PlayerManager:
    def __init__(self):
        self.players = []
        self.active_players = []
        self.lock = threading.Lock()

    def add_player(self, player):
        with self.lock:
            name = player.get_name()
            if name in self.players:
                for i in range(len(self.players)):
                    if not name + "_" + str(i) in self.players:
                        player.set_name(name + "_" + str(i))
            self.players.append(player)
            self.active_players.append(player)

    def get_players(self):
        return self.players

    def update_player_status(self, player):
        with self.lock:
            if player in self.players:
                player.set_acitve(False)
                self.active_players.remove(player)

    def get_active_players(self):
        return self.active_players
