import re

def remove_non_alpha_letters(input_string):
    return re.sub(r"[^A-Z]", "", input_string.upper())