class Player:
    def __init__(self, name, socket, active):
        self.name = name
        self.socket = socket
        self.active = active

    def get_name(self):
        return self.name

    def get_socket(self):
        return self.socket

    def is_active(self):
        return self.active

    def set_active(self, act):
        self.active = act

    def set_name(self, new_name):
        self.name = new_name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)
