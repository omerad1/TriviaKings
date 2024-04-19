import random
import sys
import threading
from JsonReader import JSONReader
from Client import Client


class Bot(Client, threading.Thread):
    def __init__(self, player_name):
        super().__init__(f'BOT:{player_name}')
        true_answers = self.config_reader.get('true_options')
        false_answers = self.config_reader.get('false_options')
        self.answer_choices = true_answers + false_answers

    def wait_for_input(self, timeout, msg):
        """
        Overrides the wait_for_input method from the parent class.
        The bot will randomly answer with "True" or "False".
        """
        self.current_answer = random.choice(self.answer_choices)
        print(f"Bot {self.player_name} answered: {self.current_answer}")


if __name__ == '__main__':
    number_of_bots = int(sys.argv[1])
    json_reader = JSONReader()
    names = json_reader.get('names')
    cap = len(names)
    if number_of_bots > cap:
        print(f'Number of bots entered is bigger than capacity: {cap}')
    else:
        random.shuffle(names)
        bot_threads = []
        for i in range(number_of_bots):
            bot_client = Bot(names[i])
            bot_threads.append(bot_client)
            bot_client.start()

        # Wait for all bot threads to finish
        for bot_thread in bot_threads:
            bot_thread.join()
