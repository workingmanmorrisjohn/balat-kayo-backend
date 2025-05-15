from typing import Dict, List, Union
import json
from loguru import logger
import asyncio
import random
from fastapi import WebSocket

from .player import Player
from .broadcast_message import BroadcastMessage
from .events import Event
from .game_types import GameWord
from .word_generator import generate_random_word

class GameRoom:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players: Dict[str, Player] = {}
        self.connections: Dict[WebSocket, str] = {}
        self.is_started = False
        self.gamer_timer = None
        self.votes: Dict[str, List[str]] = {}
        self.impostor = ""
        self.the_word = ""
        
    def add_player(self, player: Player):
        self.players[player.player_id] = player
        self.connections[player.websocket] = player.player_id
    
    def remove_player(self, websocket: WebSocket):
        player_id = self.connections.pop(websocket, None)
        if player_id:
            player = self.players.pop(player_id, None)
            self.votes.pop(player_id, None)

            logger.info(f"Player {player_id} removed from room {self.room_id}")
            
            return player_id
        else:
            logger.warning("Tried to remove a websocket that wasn't in connections")
            
        return None
        
    def delete_player(self, player_id: str):
        if player_id in self.players:
            del self.players[player_id]
            
    def set_ready(self, player_id: str):
        self.players[player_id].is_ready = True
        
    def set_name(self, player_id: str, new_name):
        self.players[player_id].player_name = new_name
    
    def set_image(self, player_id: str, new_image):
        self.players[player_id].player_image_url = new_image
    
    def unready(self, player_id: str):
        self.players[player_id].is_ready = False
        
    def start_game(self):
        self.is_started = True
        
    def start_turn(self, player_id: str):
        self.players[player_id].currently_discussing = True
    
    def end_turn(self, player_id: str):
        self.players[player_id].currently_discussing = False
        self.players[player_id].turn_ended = True
        
    def whos_next(self) -> Union[Player, None]:
        all_done = all([player.turn_ended for player in self.players.values()])
        
        if all_done:
            return
        
        next_player = random.choice([player for player in self.players.values() if not player.turn_ended])
        
        return next_player
    
    def reset_room(self):
        self.is_started = False
        self.votes = {}
        self.impostor = ""
        self.the_word = ""
        
        for player_id in self.players.keys():
            try:
                self.players[player_id].is_ready = False
                self.players[player_id].turn_ended = False
                self.players[player_id].has_voted = False
                self.players[player_id].currently_discussing = False
            except Exception as e:
                logger.warning(f"Something went wrong when updating player: {e}")
        
    def all_ready(self) -> bool:
        return all([ player.is_ready for player in self.players.values() ])
    
    def all_voted(self) -> bool:
        return all([ player.has_voted for player in self.players.values() ])
    
    def vote(self, voter: str, voted: str):
        logger.info(f"{voter} voted for {voted}")
        
        if self.votes.get(voted):
            self.votes[voted].append(self.players[voter].player_image_url)
        else:
            self.votes[voted] = [self.players[voter].player_image_url]
        
        self.players[voter].has_voted = True
        
    async def generate_impostor(self):
        players = list(self.players.keys())
        self.impostor = random.choice(players)
        
    def winner(self):
        vote_count = 0
        
        for vote in self.votes.items():
            if vote == self.impostor:
                vote_count += 1
        
        if vote_count <= 0:
            return "impostor"
        
        if vote_count > len(self.players) // 2:
            return "players"
        
        return "impostor"
        
    
    async def send_to_player(self, player: Player, broadcast_message: BroadcastMessage):
        try:
            await player.websocket.send_text(json.dumps(broadcast_message.to_dict()))
            logger.info(f"Player list sent to: {player.player_id}")
        except Exception as e:
            logger.exception(f"Something went wrong when sending message to player! {e}")
            
    async def send_to_all_players(self, broadcast_message: BroadcastMessage):
        tasks = [
            (player, self.send_to_player(player, broadcast_message))
            for player in self.players.values()
        ]

        results = await asyncio.gather(
            *(task for _, task in tasks),
            return_exceptions=True
        )

        for (player, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.exception(f"Error sending message to player {player.player_id}: {result}")
                
    async def send_to_all_except_impostor(self, 
                                          broadcast_message_to_all: BroadcastMessage,
                                          broadcast_message_to_impostor: BroadcastMessage):
        tasks = [
            (player, self.send_to_player(player, broadcast_message_to_all))
            for player in self.players.values() if player != self.impostor
        ]

        results = await asyncio.gather(
            *(task for _, task in tasks),
            return_exceptions=True
        )

        for (player, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.exception(f"Error sending message to player {player.player_id}: {result}")
                
        await self.send_to_player(self.players[self.impostor], broadcast_message_to_impostor)
    
    async def send_updated_player_list(self):
        logger.info("sending updated player list")
        player_dicts = [
            player.model_dump(exclude={"websocket"})
            for player in self.players.values()
        ]
        
        message = BroadcastMessage(Event.UPDATED_PLAYERS_LIST, {"players": player_dicts})
        
        await self.send_to_all_players(message)
                
    async def send_countdown_start(self):
        message = BroadcastMessage(Event.COUNTDOWN_START, {})
        
        await self.send_to_all_players(message)
    
    async def send_game_start(self):
        random_word = generate_random_word()
        message = BroadcastMessage(Event.GAME_START, GameWord(is_impostor=False, word=random_word.word).model_dump())
        message_to_impostor = BroadcastMessage(Event.GAME_START, GameWord(is_impostor=True, word=random_word.clue).model_dump())
        self.the_word = random_word.word
        
        await self.send_to_all_except_impostor(message, message_to_impostor)
        
    async def send_voting_start(self):
        message = BroadcastMessage(Event.VOTING_START, {})
        
        await self.send_to_all_players(message)
        
    async def send_updated_vote_dict(self):
        vote_dict = {voter: True for voter in self.votes}
        
        message = BroadcastMessage(Event.VOTING_START, {"votes": vote_dict})
        
        await self.send_to_all_players(message)
        
    async def show_impostor(self):
        votes_list = []
        
        for player, voters in self.votes.items():
            votes_list.append({
                "player_id": player,
                "voted_this_guy": voters
            })
        
        message_dict = {
            "impostor" : self.impostor,
            "winner" : self.winner(),
            "votes" : votes_list,
            "word" : self.the_word
        }
        
        message = BroadcastMessage(Event.SHOW_IMPOSTOR, message_dict)
        
        await self.send_to_all_players(message)
        
    async def notify_disconnect(self, disconnected_user: Union[str, None]):
        if disconnected_user:
            disconnected_dict = {
                "disconnected_user" : disconnected_user
            }
            
            message = BroadcastMessage(Event.PLAYER_DISCONNECT, disconnected_dict)
        
            await self.send_to_all_players(message)
            
    async def notify_player_who_joined(self, player: Player):
        logger.info("notifying player who joined")
        message = BroadcastMessage(Event.PLAYER_JOINED, {"current_player" : player.model_dump(exclude={"websocket"})})
        
        await self.send_to_player(player, message)
        
    async def notify_player_their_turn(self, player: Player):
        message = BroadcastMessage(Event.START_TURN, {})
        
        await self.send_to_player(player, message)
        
    
rooms: Dict[str, GameRoom] = {}