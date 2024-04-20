import random
import sys
import threading
from JsonReader import JSONReader
from Client import Client


class SmartBot(Client, threading.Thread):
    def __init__(self, player_name, answer_probability):
        super().__init__(f'SMART_BOT:{player_name} 👽')
        self.answer_probability = answer_probability

    def wait_for_input(self, timeout, msg):
        """
        Overrides the wait_for_input method from the parent class.
        The bot will generate a True/False answer using the pre-trained language model.
        """
        true_ans = (random.random() < self.answer_probability)
        # Answer based on the model
        server_rows = msg.split('\n')
        question = f'{server_rows[-1]}'
        qus_prefix = f"{self.config_reader.get('question_message_prefix')}:"
        question = question.lstrip(qus_prefix)
        questions = self.config_reader.get('questions')
        for q in questions:
            if question in q['question']:
                if true_ans:
                    self.current_answer = 't' if q['is_true'] else 'f'
                else:
                    self.current_answer = 'f' if q['is_true'] else 't'

        print(f"Bot {self.player_name} answered: {self.current_answer}")


if __name__ == '__main__':
    number_of_bots = int(sys.argv[1])
    prob = float(sys.argv[2])
    if prob < 0 or prob > 1:
        print("Error: Probability must be a number between 0 and 1.")
    else:
        json_reader = JSONReader()
        names = json_reader.get('names')
        cap = len(names)
        if number_of_bots > cap:
            print(f'Number of bots entered is bigger than capacity: {cap}')
        else:
            random.shuffle(names)
            bot_threads = []
            for i in range(number_of_bots):
                bot_client = SmartBot(names[i], prob)
                bot_threads.append(bot_client)
                bot_client.start()

            # Wait for all bot threads to finish
            for bot_thread in bot_threads:
                bot_thread.join()
