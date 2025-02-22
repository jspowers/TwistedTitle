import re
from .hard_ignore_words import HARD_IGNORE
from .global_utils import remove_non_alpha_letters
from dataclasses import dataclass

@dataclass(frozen=True)
class ClueValidation:
    """
    A class to represent a Clue Validation.
    Scope is reference to the button that fires the validation.
    """
    code: str
    scope: set[str]
    message: str
    action: str

class ClueValidations:
    TWISTED_TITLE_EMPTY = ClueValidation(
        code="TWISTED_TITLE_EMPTY",
        scope={'propose_clue', 'generate_gpt_response'},
        message="Twisted title was not provided",
        action="BLOCK",
    )
    TWISTED_TITLE_LENGTH = ClueValidation(
        code="TWISTED_TITLE_LENGTH",
        scope={'propose_clue', 'generate_gpt_response'},
        message="Twisted title length is different from original title",
        action="BLOCK",
    )
    TWISTED_TITLE_CHANGE_COUNT = ClueValidation(
        code="TWISTED_TITLE_CHANGE_COUNT",
        scope={'propose_clue', 'generate_gpt_response'},
        message="Twisted title has too many changes from original title",
        action="BLOCK",
    )
    CLUE_HAS_TITLE = ClueValidation(
        code="CLUE_HAS_TITLE",
        scope={'propose_clue'},
        message="Clue has word from original titles or twisted title",
        action="PASS",
    )
    DESCRIPTION_IS_EMPTY = ClueValidation(
        code="DESCRIPTION_IS_EMPTY",
        scope={'propose_clue'},
        message="Clue has word from original titles or twisted title",
        action="BLOCK",
    )

def validate_clue(original_movie: str, modified_movie: str, clue: str = None) -> list[ClueValidations]:
    """
    Validates a clue based on the original movie and modified movie titles.

    Args:
    clue (str): The clue to validate.
    original_movie (str): The original movie title.
    modified_movie (str): The modified movie title.

    Returns:
    DICT: {twisted title too different, Clue has title}
    """

    # Initialize the list of errors
    errs = []

    # TWISTED_TITLE_EMPTY - Check if twisted title is empty
    if not modified_movie or modified_movie.strip() == '':
        errs.append(ClueValidations.TWISTED_TITLE_EMPTY)
        return errs
    
    stripped_og = remove_non_alpha_letters(original_movie)
    stripped_mod = remove_non_alpha_letters(modified_movie) or ''

    # TWISTED_TITLE_LENGTH - Check that twisted title is valid
    if len(stripped_og) != len(stripped_mod):
        errs.append(ClueValidations.TWISTED_TITLE_LENGTH)
    
    # TWISTED_TITLE_CHANGE_COUNT - Check the change count 
    change_count = 0

    for i in range(len(stripped_og if len(stripped_og) <= len(stripped_mod) else stripped_mod)):
        if stripped_og[i] != stripped_mod[i]:
            change_count += 1
        if change_count > 1:
            errs.append(ClueValidations.TWISTED_TITLE_CHANGE_COUNT)
            break


    # SOFT VALIDATION - RESULT WOULD ONLY BE STORED IN MONGODB FOR CLUE MANAGEMENT
    # CLUE_HAS_TITLE - Check if the clue contains any of the banned words
    if clue: 
        clue_words = set(
            [word.upper() for word in clue.split() if word.upper() not in HARD_IGNORE]
        )

        # Get the banned the words
        original_split = set(
            [
                word.upper()
                for word in original_movie.split()
                if word.upper() not in HARD_IGNORE
            ]
        )
        modified_split = set(
            [
                word.upper()
                for word in modified_movie.split()
                if word.upper() not in HARD_IGNORE
            ]
        )
        banned_words = original_split.union(modified_split)

        for word in clue_words:
            if word in banned_words:
                errs.append(ClueValidations.CLUE_HAS_TITLE)
                break

    return errs
