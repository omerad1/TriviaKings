import json


class JSONReader:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.read_config()

    def read_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.config_file} not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {self.config_file}.")
            return {}

    def get(self, key, default=None):
        return self.config.get(key, default)
