from pydantic import BaseModel

class GameWord(BaseModel):
    is_impostor: bool
    word: str

class WordClue(BaseModel):
    word: str
    clue: str