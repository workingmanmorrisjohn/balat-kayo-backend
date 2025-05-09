from .events import Event
from enum import StrEnum

class BroadcastMessage:
    def __init__(self, event: str, data: dict):
        self.event = event
        self.data = data

    def to_dict(self):
        return {"event": self.event, "data": self.data}
    
class DefaultMessage(StrEnum):
    INVALID_ROOM_ID = "invalid_room_id"
   
default_messages = {
    DefaultMessage.INVALID_ROOM_ID : BroadcastMessage(Event.INVALID_ROOM_ID, {"message": "Invalid room id!"})
}