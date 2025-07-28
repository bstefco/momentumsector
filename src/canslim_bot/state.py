import json
import os
from typing import Any, Dict

def load_state(path: str = "positions.json") -> Dict[str, Any]:
    """
    Load state from a JSON file. If the file does not exist, create it and return an empty dict.

    Args:
        path (str): Path to the JSON file.

    Returns:
        dict: Loaded state dictionary.
    """
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump({}, f)
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_state(state: Dict[str, Any], path: str = "positions.json") -> None:
    """
    Save state to a JSON file.

    Args:
        state (dict): State dictionary to save.
        path (str): Path to the JSON file.
    """
    with open(path, 'w') as f:
        json.dump(state, f, indent=2) 