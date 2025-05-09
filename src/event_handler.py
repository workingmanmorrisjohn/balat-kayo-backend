from typing import Callable, Dict
from fastapi import WebSocket
import asyncio
from loguru import logger

from .room import GameRoom
from .player import Player
from .event_controller import ready
from .events import Event

event_handlers: Dict[str, Callable[[WebSocket, Dict, GameRoom, Player], None]] = {}

def register_event(event_name: str):
    def decorator(func: Callable[[WebSocket, Dict, GameRoom, Player], None]):
        event_handlers[event_name] = func
        return func
    return decorator

@register_event(Event.SET_READY)
async def handle_ready(websocket: WebSocket, data: Dict, room: GameRoom, player: Player):
    await ready(room, player)
    
@register_event(Event.REMOVE_READY)
async def handle_unready(websocket: WebSocket, data: Dict, room: GameRoom, player: Player):
    room.unready(player.player_id)
    
    await room.send_updated_player_list()
    
@register_event(Event.SET_NAME)
async def handle_set_name(websocket: WebSocket, data: Dict, room: GameRoom, player: Player):
    room.set_name(player.player_id, data.get("new_name", player.player_name))
    
    await room.send_updated_player_list()
    
@register_event(Event.END_TURN)
async def handle_end_turn(websocket: WebSocket, data: Dict, room: GameRoom, player: Player):
    logger.info(f"Ending turn of {player.player_name}")
    room.end_turn(player.player_id)
    
    next_player = room.whos_next()
    
    if not next_player:
        await room.send_voting_start()
        return
    
    room.start_turn(next_player.player_id)
    
    await room.send_updated_player_list()
    await room.notify_player_their_turn(next_player)

@register_event(Event.SET_VOTE)
async def handle_vote(websocket: WebSocket, data: Dict, room: GameRoom, player: Player):
    voted = data.get("voted", "")
    
    if voted not in room.players.keys():
        return
    
    room.vote(player.player_id, voted)
    
    await room.send_updated_vote_dict()
    
    if room.all_voted():
        await room.show_impostor()