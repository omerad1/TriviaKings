import os
import random
import sys
import threading
from JsonReader import JSONReader
from Client import Client
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class GoodBurgerBot(Client, threading.Thread):
    def __init__(self, player_name):
        super().__init__(player_name)

        # Set the paths to load the model and tokenizer
        model_path = os.path.join("saved_models", "model")
        tokenizer_path = os.path.join("saved_models", "tokenizer")

        # Load pre-trained language model and tokenizer
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    def wait_for_input(self, timeout, msg):
        """
        Overrides the wait_for_input method from the parent class.
        The bot will generate a True/False answer using the pre-trained language model.
        """
        server_rows = msg.split('\n')
        question = server_rows[-1]

        # Encode the question using the tokenizer
        inputs = self.tokenizer(question, return_tensors="pt")

        # Generate the answer using the language model
        outputs = self.model(**inputs)
        logits = outputs.logits
        predicted_class_id = logits.argmax().item()

        # Decode the answer
        answer = "T" if predicted_class_id == 0 else "F"

        self.current_answer = answer
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
            bot_client = GoodBurgerBot(names[i])
            bot_threads.append(bot_client)
            bot_client.start()

        # Wait for all bot threads to finish
        for bot_thread in bot_threads:
            bot_thread.join()
