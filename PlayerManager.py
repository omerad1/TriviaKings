import threading
from Player import Player
import Statistics


class PlayerManager:
    """
    Class for managing players in the game.

    Attributes:
        players (list): List of all players.
        active_players (list): List of active players.
        lock (threading.Lock): Lock object for synchronizing access to player lists.
    """

    def __init__(self):
        """
        Initializes the PlayerManager.
        """
        self.players = []
        self.active_players = []
        self.lock = threading.Lock()

    def add_player(self, player):
        """
        Adds a player to the manager.

        Args:
            player (Player): The player to add.
        """
        with self.lock:
            name_changed = False
            player_name = player.get_name()
            players_names = self.get_players_names()
            i = 1
            while player_name in players_names:
                new_player_name = f'{player_name}({i})'
                if new_player_name not in players_names:
                    player.set_name(new_player_name)
                    name_changed = True
                    break
                i += 1
            self.players.append(player)
            self.active_players.append(player)
            return name_changed

    def get_players_names(self):
        return [player.get_name() for player in self.players]

    def get_players(self):
        """
        Gets all players.

        Returns:
            list: List of all players.
        """
        return self.players

    def kick_player(self, player):
        """
        Kick inactive player.

        Args:
            player (Player): The player to kick.
        """
        with self.lock:
            if player in self.players:
                self.players.remove(player)
            if player in self.active_players:
                self.active_players.remove(player)

    def get_active_players(self):
        """
        Gets active players.

        Returns:
            list: List of active players.
        """
        return self.active_players

    def set_active_players(self, active_players):
        """
        Sets the list of active players.

        Args:
            active_players (list): List of active players.
        """
        with self.lock:
            self.active_players = active_players

