from nltk.corpus import words
import string
import re

HARD_IGNORE = set(["the", "a", "an", "that", "this", "these", "those", "some", "any", "each", "every", "either", "neither", "of", "in"]) 

def remove_non_lowercase_letters(input_string):
    return re.sub(r'[^a-z]', '', input_string)


def get_movie_neighbors(word):
    """
    Given a word, find all valid English words that result from swapping one letter at a time.
    
    :param word: str - The input word.
    :return: list - A list of valid English words after one letter swap.
    """
    english_words = set(words.words())

    word = word.lower()
    word = remove_non_lowercase_letters(word)
    if word in HARD_IGNORE:
        return []
    result = []
    for i in range(len(word)):
        for char in string.ascii_lowercase:  # Iterate through all lowercase letters
            if char != word[i]:  # Avoid swapping with the same letter
                new_word = word[:i] + char + word[i + 1:]  # Replace the character at index i
                if new_word in english_words and new_word not in HARD_IGNORE:  # Check if it's a valid English word
                    result.append(new_word)
            
    return list(set(result))  # Remove duplicates

    
