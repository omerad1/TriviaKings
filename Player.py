class Player:
    """
    Class representing a player in the game.

    Attributes:
        name (str): The name of the player.
        socket (socket): The socket associated with the player.
        active (bool): Flag indicating whether the player is active in the game.
    """

    def __init__(self, name, socket, active):
        """
        Initializes the Player.

        Args:
            name (str): The name of the player.
            socket (socket.socket): The socket associated with the player.
            active (bool): Flag indicating whether the player is active in the game.
        """
        self.name = name
        self.socket = socket
        self.active = active

    def get_name(self):
        """
        Gets the name of the player.

        Returns:
            str: The name of the player.
        """
        return self.name

    def get_socket(self):
        """
        Gets the socket associated with the player.

        Returns:
            socket.socket: The socket associated with the player.
        """
        return self.socket

    def is_active(self):
        """
        Checks if the player is active in the game.

        Returns:
            bool: True if the player is active, False otherwise.
        """
        return self.active

    def set_active(self, act):
        """
        Sets the active status of the player.

        Args:
            act (bool): The active status to set.
        """
        self.active = act

    def set_name(self, new_name):
        """
        Sets the name of the player.

        Args:
            new_name (str): The new name to set for the player.
        """
        self.name = new_name

    def __eq__(self, other):
        """
        Checks if two players are equal based on their names.

        Args:
            other (Player): The other player to compare.

        Returns:
            bool: True if the players have the same name, False otherwise.
        """
        return self.name == other.name

    def __hash__(self):
        """
        Computes the hash value of the player based on their name.

        Returns:
            int: The hash value of the player's name.
        """
        return hash(self.name)
