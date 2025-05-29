import json
from pathlib import Path

BASE_CONFIG_DATA = None

def read_base_config():  
    """
    Loads the config from 'config.json' located in the same directory as this loader,
    only once, and returns it as a dictionary.
    """
    global BASE_CONFIG_DATA

    if BASE_CONFIG_DATA is None:
        # Path is relative to this config_loader.py file
        config_file_path = Path(__file__).parent / "config.json"
        with open(config_file_path, "r") as json_file:
            BASE_CONFIG_DATA = json.load(json_file)
    return BASE_CONFIG_DATA