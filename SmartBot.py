import os
import random
import sys
import threading
from JsonReader import JSONReader
from Client import Client
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class SmartBot(Client, threading.Thread):
    def __init__(self, player_name, answer_probability):
        super().__init__(player_name)
        self.answer_probability = answer_probability
        true_answers = self.json_reader.get('true_options')
        false_answers = self.json_reader.get('false_options')
        self.answer_choices = true_answers + false_answers
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

        if random.random() < self.answer_probability:
            # Answer based on the model
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
        else:
            # Random answer
            self.current_answer = random.choice(self.answer_choices)
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
