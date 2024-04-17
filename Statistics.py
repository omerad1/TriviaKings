import json

from JsonReader import JSONReader


class Statistics:
    _instance = None

    def __init__(self):
        self.questions_data = None
        self.players_data = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Statistics, cls).__new__(cls, *args, **kwargs)
            cls._instance.file_name = 'game_data.json'
            cls._instance.players_data = {}
            questions = JSONReader('config.json').get('questions')
            cls._instance.questions_data = {}
            for question in questions:
                questions[question] = {'true': 0, 'false': 0}
            # Load existing data from the file, if it exists
        return cls._instance

    def load_data(self):
        try:
            with open(self.file_name, 'r') as file:
                data = json.load(file)
                self.players_data = data.get('players_data', {})
                self.questions_data = data.get('questions_data', {})
        except FileNotFoundError:
            # File doesn't exist, create a new one
            self.save_data()

    def save_data(self):
        data = {
            'players_data': self.players_data,
            'questions_data': self.questions_data
        }
        with open(self.file_name, 'w') as file:
            json.dump(data, file)

    def update_question_ans(self, question, answers):
        for answer in answers:
            if answer == 't' or answer == 'T' or answer == 'Y' or answer == 'Y' or answer == 1:
                self.questions_data[question]['true'] += 1
            else:
                self.questions_data[question]['false'] += 1

    def update_correct_players(self, correct_players):
        for player in correct_players:
            self.players_data[player]['correct'] += 1

    def update_incorrect_players(self, incorrect_players):
        for player in incorrect_players:
            self.players_data[player]['incorrect'] += 1

    def update_winner_player(self, player):
        self.players_data[player]['win'] += 1
