from pydantic import BaseModel

class GameWord(BaseModel):
    is_impostor: bool
    word: str