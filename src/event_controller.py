from loguru import logger
import asyncio

from .room import GameRoom
from .player import Player

async def ready(room: GameRoom, player: Player):
    room.set_ready(player.player_id)
    
    await room.send_updated_player_list()
    
    if room.all_ready():
        asyncio.create_task(start_game_countdown(room))

async def start_game_countdown(room: GameRoom):
    logger.info(f"All players are ready in room {room.room_id}. Starting the game in 3 seconds.")
    
    room.start_game()
    
    await room.send_countdown_start()
    
    await asyncio.sleep(3)
    await start_game(room)
    
async def start_game(room: GameRoom):
    logger.info(f"Game started in {room.room_id}. Discussion ongoing.")
    
    await room.generate_impostor()
    await room.send_game_start()
    
    next_player = room.whos_next()
    
    if next_player:
        room.start_turn(next_player.player_id)
        await room.send_updated_player_list()
        await room.notify_player_their_turn(next_player)