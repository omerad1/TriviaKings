import json


class JSONReader:
    """
    Class for reading configuration data from a JSON file.

    Attributes:
        config_file (str): The path to the JSON configuration file.
        config (dict): The loaded configuration data from the JSON file.
    """

    def __init__(self, config_file='config.json'):
        """
        Initializes the JSONReader.

        Args:
            config_file (str): The path to the JSON configuration file.
        """
        self.config_file = config_file
        self.config = self.read_config()

    def read_config(self):
        """
        Reads the configuration data from the JSON file.

        Returns:
            dict: The loaded configuration data.
        """
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
        """
        Gets a value from the configuration data based on the specified key.

        Args:
            key (str): The key to retrieve the value for.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if the key is not found.
        """
        return self.config.get(key, default)
