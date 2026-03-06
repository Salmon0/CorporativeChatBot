from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class ChatDTO:
    id: int
    title: Optional[str] = None
    type: str = "private"

@dataclass
class UserDTO:
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@dataclass
class ReactionDTO:
    message_id: int
    user_id: int
    reaction: str
    date: Optional[datetime] = None

@dataclass
class MessageDTO:
    id: int
    chat: ChatDTO
    date: datetime
    user: Optional[UserDTO] = None
    text: Optional[str] = None
    edited_date: Optional[datetime] = None
    reply_to_message_id: Optional[int] = None
    forward_from: Optional[Dict[str, Any]] = None
    media: Optional[List[Dict[str, Any]]] = None
    reactions: List[ReactionDTO] = field(default_factory=list)