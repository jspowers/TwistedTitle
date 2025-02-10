import re
from typing import Any
import logging

def remove_non_alpha_letters(input_string):
    return re.sub(r"[^A-Z]", "", input_string.upper())

def get_max_string_key_value(dictionary: dict) -> Any: 
    if not dictionary:
        logging.error("Dictionary is empty or None")
        return None  # Return None if the dictionary is empty
    # Convert keys to integers, get the max key, and retrieve its value
    max_key = str(max(map(int, dictionary.keys())))
    
    return dictionary[max_key]