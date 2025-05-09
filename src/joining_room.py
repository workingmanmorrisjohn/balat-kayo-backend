from fastapi import WebSocket
import json
from typing import Dict
import uuid
from loguru import logger

from .player import Player
from .config import DEFAULT_PLAYER_IMAGE
from .room import rooms
from .broadcast_message import default_messages, DefaultMessage
from .events import Event

async def identify(websocket: WebSocket) -> bool:
    message_json = await websocket.receive_text()
    message = json.loads(message_json)
    
    logger.info(f"Identifying: {message}")
    
    if message.get('event') == Event.IDENTIFY:
        player = await handle_identify(websocket, message['data'])
        
        return player
    else:
        await websocket.close()
        return

async def handle_identify(websocket: WebSocket, message_data: Dict) -> Player:
    player_id = str(uuid.uuid4())
    player_name = message_data.get("player_name", "")
    player_image_url = message_data.get("player_image_url", DEFAULT_PLAYER_IMAGE)
    
    player = Player(player_id=player_id,
                    websocket=websocket, 
                    player_name=player_name, 
                    player_image_url=player_image_url,
                    is_ready=False,
                    turn_ended=False,
                    has_voted=False,
                    currently_discussing=False
                    )
    
    return player
    
async def validate_room(websocket: WebSocket, room_id: str) -> bool:
    if room_id not in rooms:
        websocket.send(json.dumps(default_messages[DefaultMessage.INVALID_ROOM_ID]))
        
        await websocket.close()
        return False
    
    return True