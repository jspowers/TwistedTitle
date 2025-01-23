from nltk.corpus import words
import string
import re
from .hard_ignore_words import HARD_IGNORE

def remove_non_alpha_letters(input_string):
    return re.sub(r'[^A-Z]', '', input_string)

def get_movie_neighbors(word):
    """
    Given a word, find all valid English words that result from swapping one letter at a time.
    
    :param word: str - The input word.
    :return: list - A list of valid English words after one letter swap.
    """
    english_words = set(words.words())

    # convert word to uppercase and remove non-alphabetic characters
    word = word.upper()
    word = remove_non_alpha_letters(word)

    # skip if the word is in hard ignore list 
    if word in HARD_IGNORE:
        return []
    
    # Find all valid English words that result from swapping one letter at a time
    result = []
    for i in range(len(word)):
        for char in string.ascii_uppercase:  # Iterate through all uppercase letters
            if char != word[i]:  # Avoid swapping with the same letter
                new_word = word[:i] + char + word[i + 1:]  # Replace the character at index i
                if new_word.lower() in english_words and new_word not in HARD_IGNORE:  # Check if it's a valid English word
                    result.append(new_word)
            
    return list(set(result))  # Remove duplicates

    
