# app/models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal

class NPCAction(BaseModel):
    type: Literal["follow", "unfollow", "stop_talking", "none"]
    data: Optional[Dict[str, Any]] = None

class NPCResponseV3(BaseModel):
    message: str
    action: NPCAction
    internal_state: Optional[Dict[str, Any]] = None

class PerceptionData(BaseModel):
    visible_objects: List[str] = Field(default_factory=list)
    visible_players: List[str] = Field(default_factory=list)
    memory: List[Dict[str, Any]] = Field(default_factory=list)

class EnhancedChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    initiator_id: str
    target_id: str
    conversation_type: Literal["npc_user", "npc_npc", "group"]
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    system_prompt: str

class ConversationResponse(BaseModel):
    conversation_id: str
    message: str
    action: NPCAction
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationMetrics:
    def __init__(self):
        self.total_conversations = 0
        self.active_conversations = 0
        self.completed_conversations = 0
        self.average_response_time = 0.0
        self.total_messages = 0
        
    @property
    def dict(self):
        return self.model_dump()
        
    def model_dump(self):
        return {
            "total_conversations": self.total_conversations,
            "active_conversations": self.active_conversations,
            "completed_conversations": self.completed_conversations,
            "average_response_time": self.average_response_time,
            "total_messages": self.total_messages
        }