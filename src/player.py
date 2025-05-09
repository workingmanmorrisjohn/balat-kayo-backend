from pydantic import BaseModel, ConfigDict
from fastapi import WebSocket

class Player(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    player_id : str
    websocket : WebSocket
    player_name : str
    player_image_url : str
    is_ready: bool
    turn_ended: bool
    has_voted: bool
    currently_discussing: bool