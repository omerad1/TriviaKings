import json
from JsonReader import JSONReader


class GameStatistics:
    """
    This class will store the game statistics as follows:
    players_data = [games_played, games_won , questions answered correctly, questions answered incorrectly]
    games_data = [games_played]
    questions_data = for each trivia questions, how many players answered correctly and how many players answered incorrectly
    and how many times the question has been appeared in the game
    trivia_king = (player name , how many games he won)
    """

    def __init__(self):
        self.players_data = {}
        self.games_data = 0
        self.question_data = {}
        self.trivia_king = [None, 0]
        self.load_statistics()

    def load_statistics(self):
        reader = JSONReader("statistics.json")
        self.players_data = reader.get("players_data", {})
        self.games_data = reader.get("games_data", 0)
        self.question_data = reader.get("question_data", None)
        self.trivia_king = reader.get("trivia_king", [None, 0])
        if self.question_data is None:
            q_reader = JSONReader("config.json")
            questions = q_reader.get("questions")
            self.question_data = {}
            for question in questions:
                self.question_data[question["question"]] = {"correct_answers": 0, "incorrect_answers": 0,
                                                            "times_appeared": 0}
            self.save_statistics()

    def add_player(self, player):
        name = player.get_name()
        if name not in self.players_data.keys():
            print(name, "is not a player")
            self.players_data[name] = {"games_played": 1, "games_won": 0, "correct_answers": 0, "incorrect_answers": 0}
        else:
            self.players_data[name]["games_played"] += 1
        self.save_statistics()

    def update_player(self, player, key):
        name = player.get_name()
        if name in self.players_data.keys():
            self.players_data[name][key] += 1
        if key == "games_won" and self.trivia_king[1] <= self.players_data[name][key]:
            self.trivia_king = (name, self.players_data[name][key])
        self.save_statistics()

    def update_game(self):
        self.games_data += 1
        self.save_statistics()

    def reload_statistics(self):
        reader = JSONReader("statistics.json")
        self.players_data = reader.get("players_data")
        self.games_data = reader.get("games_data")
        self.question_data = reader.get("question_data")
        self.trivia_king = reader.get("trivia_king")

    def update_question(self, question, correct, incorrect):
        if question in self.question_data:
            self.question_data[question]["correct_answers"] += correct
            self.question_data[question]["incorrect_answers"] += incorrect
            self.question_data[question]["times_appeared"] += 1
        self.save_statistics()

    def save_statistics(self):
        statistics = {
            "players_data": self.players_data,
            "games_data": self.games_data,
            "question_data": self.question_data,
            "trivia_king": self.trivia_king
        }
        with open("statistics.json", "w") as file:
            json.dump(statistics, file)

    def get_trivia_king(self):
        return self.trivia_king[0]

    def get_max(self, key):
        max_val = [None, 0]
        for quest, stats in self.question_data.items():
            val = stats[key]
            if val > max_val[1]:
                max_val[0] = quest
                max_val[1] = val
        return max_val

    def get_most_incorrect_question(self):
        """
                Returns the question with the most incorrect answers.

                Returns:
                    str: The question with the most incorrect answers.
                """
        return self.get_max("incorrect_answers")

    def get_most_correct_question(self):
        """
                Returns the question with the most incorrect answers.

                Returns:
                    str: The question with the most incorrect answers.
                """
        return self.get_max("correct_answers")

    def get_players_data(self):
        return self.players_data

    def get_games_data(self):
        return self.games_data

    def get_question_data(self):
        return self.question_data
