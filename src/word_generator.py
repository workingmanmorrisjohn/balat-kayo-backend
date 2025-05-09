import random
import json

from .config import STATIC_DIR
from .game_types import WordClue

with open('./static/word_list.json', 'r') as file:
    word_list = [ WordClue(word=word_clue["word"], clue=word_clue["clue"]) for word_clue in json.load(file)["words"] ]
    
def generate_random_word() -> WordClue:
    return random.choice(word_list)