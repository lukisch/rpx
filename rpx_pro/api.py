"""RPXProAPI: Programmatische Python-API fuer RPX Pro."""

import random
import time
from typing import Dict, List, Optional, Any

from rpx_pro.constants import generate_short_id
from rpx_pro.models.enums import MessageRole, MissionStatus
from rpx_pro.models.entities import Character
from rpx_pro.models.world import World, WorldSettings
from rpx_pro.models.session import ChatMessage, Mission, Session
from rpx_pro.managers.data_manager import DataManager
from rpx_pro.managers.prompt_generator import PromptGenerator


class RPXProAPI:
    """Programmatische API fuer RPX Pro - gibt JSON-serialisierbare Dicts zurueck."""

    def __init__(self, data_manager: DataManager):
        self.dm = data_manager

    # --- Welt ---

    def create_world(self, name: str, genre: str = "Fantasy") -> dict:
        world = self.dm.create_world(name, genre)
        return {"id": world.id, "name": world.settings.name, "genre": world.settings.genre}

    def list_worlds(self) -> list:
        return [
            {"id": w.id, "name": w.settings.name, "genre": w.settings.genre}
            for w in self.dm.worlds.values()
        ]

    def load_world(self, world_id: str) -> dict:
        if world_id not in self.dm.worlds:
            return {"error": f"Welt {world_id} nicht gefunden"}
        world = self.dm.worlds[world_id]
        self.dm.current_world = world
        return {"id": world.id, "name": world.settings.name, "genre": world.settings.genre}

    # --- Session ---

    def create_session(self, world_id: str, name: str) -> dict:
        session = self.dm.create_session(world_id, name)
        if not session:
            return {"error": "Welt nicht gefunden"}
        return {"id": session.id, "world_id": session.world_id, "name": session.name}

    def list_sessions(self) -> list:
        return [
            {"id": s.id, "world_id": s.world_id, "name": s.name}
            for s in self.dm.sessions.values()
        ]

    def load_session(self, session_id: str) -> dict:
        if session_id not in self.dm.sessions:
            return {"error": f"Session {session_id} nicht gefunden"}
        session = self.dm.sessions[session_id]
        self.dm.current_session = session
        return {"id": session.id, "name": session.name, "characters": len(session.characters)}

    # --- Charaktere ---

    def create_character(self, name: str, **kwargs) -> dict:
        session = self.dm.current_session
        if not session:
            return {"error": "Keine aktive Session"}
        char_id = generate_short_id()
        char = Character(id=char_id, name=name, **kwargs)
        session.characters[char_id] = char
        self.dm.save_session(session)
        return {"id": char_id, "name": name}

    def get_character(self, char_id: str) -> dict:
        session = self.dm.current_session
        if not session or char_id not in session.characters:
            return {"error": "Charakter nicht gefunden"}
        return session.characters[char_id].to_dict()

    def heal_character(self, char_id: str, amount: int) -> dict:
        session = self.dm.current_session
        if not session or char_id not in session.characters:
            return {"error": "Charakter nicht gefunden"}
        char = session.characters[char_id]
        old_hp = char.health
        char.health = min(char.max_health, char.health + amount)
        self.dm.save_session(session)
        return {"name": char.name, "old_hp": old_hp, "new_hp": char.health, "healed": char.health - old_hp}

    def damage_character(self, char_id: str, amount: int) -> dict:
        session = self.dm.current_session
        if not session or char_id not in session.characters:
            return {"error": "Charakter nicht gefunden"}
        char = session.characters[char_id]
        old_hp = char.health
        char.health = max(0, char.health - amount)
        self.dm.save_session(session)
        return {"name": char.name, "old_hp": old_hp, "new_hp": char.health, "damage": old_hp - char.health}

    def get_inventory(self, char_id: str) -> dict:
        session = self.dm.current_session
        if not session or char_id not in session.characters:
            return {"error": "Charakter nicht gefunden"}
        char = session.characters[char_id]
        items = []
        world = self.dm.current_world
        for item_id, count in char.inventory.items():
            name = item_id
            if world and item_id in world.typical_items:
                name = world.typical_items[item_id].name
            items.append({"item_id": item_id, "name": name, "count": count})
        return {"character": char.name, "gold": char.gold, "items": items}

    def give_item(self, char_id: str, item_id: str, count: int = 1) -> dict:
        session = self.dm.current_session
        if not session or char_id not in session.characters:
            return {"error": "Charakter nicht gefunden"}
        char = session.characters[char_id]
        char.inventory[item_id] = char.inventory.get(item_id, 0) + count
        self.dm.save_session(session)
        return {"character": char.name, "item_id": item_id, "count": char.inventory[item_id]}

    # --- Chat ---

    def send_chat_message(self, role: str, author: str, content: str) -> dict:
        session = self.dm.current_session
        if not session:
            return {"error": "Keine aktive Session"}
        try:
            msg_role = MessageRole(role)
        except ValueError:
            msg_role = MessageRole.SYSTEM
        message = ChatMessage(role=msg_role, author=author, content=content)
        session.chat_history.append(message)
        self.dm.save_session(session)
        return {"role": role, "author": author, "content": content, "timestamp": message.timestamp}

    def get_chat_history(self, limit: int = 50) -> list:
        session = self.dm.current_session
        if not session:
            return []
        messages = session.chat_history[-limit:]
        return [m.to_dict() for m in messages]

    # --- Wuerfel ---

    def roll_dice(self, count: int = 1, sides: int = 20) -> dict:
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        return {"dice": f"{count}W{sides}", "rolls": rolls, "total": total}

    # --- Missionen ---

    def create_mission(self, name: str, objective: str, description: str = "") -> dict:
        session = self.dm.current_session
        if not session:
            return {"error": "Keine aktive Session"}
        mission_id = generate_short_id()
        mission = Mission(id=mission_id, name=name, description=description, objective=objective)
        session.active_missions[mission_id] = mission
        self.dm.save_session(session)
        return {"id": mission_id, "name": name, "objective": objective}

    def complete_mission(self, mission_id: str) -> dict:
        session = self.dm.current_session
        if not session or mission_id not in session.active_missions:
            return {"error": "Mission nicht gefunden"}
        mission = session.active_missions[mission_id]
        mission.status = MissionStatus.COMPLETED
        session.completed_missions.append(mission_id)
        del session.active_missions[mission_id]
        self.dm.save_session(session)
        return {"id": mission_id, "name": mission.name, "status": "completed"}

    # --- Prompts ---

    def generate_start_prompt(self) -> str:
        session = self.dm.current_session
        world = self.dm.current_world
        if not session or not world:
            return ""
        return PromptGenerator.generate_game_start_prompt(session, world)

    def generate_context_update(self) -> str:
        session = self.dm.current_session
        if not session:
            return ""
        return PromptGenerator.generate_context_update_prompt(session)
