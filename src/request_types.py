from pydantic import BaseModel

class CreateRoomRequest(BaseModel):
    numberOfRounds: int