from .config import STATIC_DIR
import random

with open(STATIC_DIR / 'adjectives.txt', 'r') as file:
    adjectives = [word.strip() for word in file.readlines()]

with open(STATIC_DIR / 'nouns.txt', 'r') as file:
    nouns = [word.strip() for word in file.readlines()]
    
def generate_random_name() -> str:
    return f"{random.choice(adjectives)} {random.choice(nouns)}"