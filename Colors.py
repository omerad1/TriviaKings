from enum import Enum


class ANSI(Enum):
    """
    Enum representing ANSI escape codes for text styling and colors.
    """

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    PINK = '\033[95m'
    RESET = '\033[0m'
    SAD_FACE = '\U0001F972'
    THUMBS_UP = '\U0001F44D'
    THUMBS_DOWN = '\U0001F44E'
    CROWN = "👑"
