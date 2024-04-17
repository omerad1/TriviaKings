import threading
from Player import Player


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
            name = player.get_name()
            if name in self.players:
                for i in range(len(self.players)):
                    if not name + "_" + str(i) in self.players:
                        player.set_name(name + "_" + str(i))
            self.players.append(player)
            self.active_players.append(player)

    def get_players(self):
        """
        Gets all players.

        Returns:
            list: List of all players.
        """
        return self.players

    def update_player_status(self, player):
        """
        Updates the status of a player.

        Args:
            player (Player): The player to update.
        """
        with self.lock:
            if player in self.players:
                player.set_active(False)
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
