import json

from JsonReader import JSONReader


class Statistics:
    """
        A singleton class to manage and update game statistics.

        Attributes:
            _instance (Statistics): An instance of the Statistics class.
            file_name (str): The name of the JSON file to store data.
            questions_data (dict): A dictionary to store statistics for each question.
            players_data (dict): A dictionary to store statistics for each player.


        """

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
        """
                Loads existing data from the JSON file or creates a new file if not found.
                """
        try:
            file = open('config.json', 'r')
            data = json.load(file)
            file.close()
            self.players_data = data.get('players_data', {})
            self.questions_data = data.get('questions_data', {})
        except FileNotFoundError:
            # File doesn't exist, create a new one
            self.save_data()

    def save_data(self):
        """
                Saves current data to the JSON file.
                """
        data = {
            'players_data': self.players_data,
            'questions_data': self.questions_data
        }
        with open(self.file_name, 'w') as file:
            json.dump(data, file)

    def update_question_ans(self, question, answers):
        """
               Updates question statistics based on player answers.

               Args:
                   question (str): The question being answered.
                   answers (list): A list of player answers.
               """
        for answer in answers:
            if answer in JSONReader('config.json').get('true_options'):
                self.questions_data[question]['true'] += 1
            else:
                self.questions_data[question]['false'] += 1

        self.save_data()


    def update_correct_players(self, correct_players):
        """
               Updates statistics for correct answers by players.

               Args:
                   correct_players (list): A list of players who answered correctly.
               """
        for player in correct_players:
            self.players_data[player]['correct'] += 1

        self.save_data()

    def update_incorrect_players(self, incorrect_players):
        """
                Updates statistics for incorrect answers by players.

                Args:
                    incorrect_players (list): A list of players who answered incorrectly.
                """
        for player in incorrect_players:
            if player not in self.players_data:
                self.players_data[player] = {'correct': 0, 'incorrect': 0, 'win': 0}
            self.players_data[player]['incorrect'] += 1

        self.save_data()


    def update_winner_player(self, player):
        """
                Updates statistics for winning players.

                Args:
                    player (str): The winning player's name.
                """
        if player not in self.players_data:
            self.players_data[player] = {'correct': 0, 'incorrect': 0, 'win': 0}
        self.players_data[player]['win'] += 1

        self.save_data()


    def get_most_winner(self):
        """
                Returns the player with the highest win count.

                Returns:
                    str: The name of the player with the most wins.
                """
        max_winner = None
        for player in self.players_data:
            if self.players_data[player]['win'] > max_winner:
                max_winner = player

        return max_winner

    def get_most_incorrect_quest(self):
        """
                Returns the question with the most incorrect answers.

                Returns:
                    str: The question with the most incorrect answers.
                """
        max_wrong = None
        for quest in self.questions_data:
            if self.questions_data[quest]['incorrect'] > max_wrong:
                max_wrong = quest

        return max_wrong

    def get_most_correct_quest(self):
        """
            Returns the question with the most correct answers.

            Returns:
                str: The question with the most correct answers.
            """
        max_correct = None
        for quest in self.questions_data:
            if self.questions_data[quest]['correct'] > max_correct:
                max_correct = quest

        return max_correct

    def get_for_each_quest_common_ans(self):
        """
            Returns common answers for each question based on correct/incorrect counts.

            Returns:
                list: A list of tuples containing common answers for each question.
                      Each tuple contains the question and the common answer ('true' or 'false').
            """
        common_answers = []
        for quest in self.questions_data:
            if self.questions_data[quest]['correct'] > self.questions_data[quest]['incorrect']:
                common_answers.append((quest, JSONReader('config.json').get('questions').get('is_true')))

            else:
                if JSONReader('config.json').get('questions').get('is_true') == 'true':
                    common_answers.append((quest,"false"))
                else:
                    common_answers.append((quest,"true"))

        return common_answers



