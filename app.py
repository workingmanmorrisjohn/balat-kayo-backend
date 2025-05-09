from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import asyncio
import json
import uuid
from loguru import logger

from src.room import rooms, GameRoom
from src.broadcast_message import default_messages, DefaultMessage
from src.player import Player
from src.config import DEFAULT_PLAYER_IMAGE
from src.event_handler import event_handlers
from src.joining_room import validate_room, identify

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/create-room")
async def create_room():
    room_id = str(uuid.uuid4())[:8]  # short unique room ID
    if room_id in rooms:
        # Extremely rare chance, but regenerate if conflict
        room_id = str(uuid.uuid4())[:8]

    new_room = GameRoom(room_id)
    rooms[room_id] = new_room
    logger.info(f"Created new room: {room_id}")

    return JSONResponse(content={"room_id": room_id})

@app.websocket("/ws/game/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    
    logger.info("Umabot dito")
    
    room_validated = await validate_room(websocket, room_id)
    if not room_validated:
        return
    
    logger.info("Umabot dito rin")

    room = rooms[room_id]
    player = await identify(websocket)
    if not player:
        return
    
    logger.info("Umabot dito rin 2")

    room.add_player(player)
    logger.info(f"Players in room: {room.players.keys()}")
    await room.send_updated_player_list()
    await room.notify_player_who_joined(player)

    try:
        while True:
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            event = message.get('event')
            data = message.get('data', {})

            if event in event_handlers:
                await event_handlers[event](websocket, data, room, player)
            else:
                logger.info(f"Unknown event: {event}")
                logger.info(message)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {player.player_id}")
        disconnected_player = room.remove_player(websocket)
        
        await room.send_updated_player_list()
        
    except Exception as e:
        logger.exception(f"Unexpected error for player {player.player_id}: {e}")
        disconnected_player = room.remove_player(websocket)
        
        await room.send_updated_player_list()