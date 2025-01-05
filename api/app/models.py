# app/models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

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

class AgentMapping(BaseModel):
    """
    Maps NPCs to their AI agents for persistent conversations.
    
    Attributes:
        id: Internal database ID
        npc_id: References the NPC in our system
        participant_id: Unique identifier for the participant
        letta_agent_id: The AI agent ID (e.g., Letta agent ID)
        agent_type: Type of AI agent (e.g., 'letta')
        created_at: When this mapping was created
    """
    id: Optional[int] = None
    npc_id: str
    participant_id: str
    letta_agent_id: str
    agent_type: str = "letta"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

def create_agent_mapping(
    npc_id: str, 
    participant_id: str, 
    agent_id: str, 
    agent_type: str = "letta"
) -> AgentMapping:
    """Create a new NPC agent mapping"""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO agent_mappings (npc_id, participant_id, agent_id, agent_type)
            VALUES (?, ?, ?, ?)
            RETURNING *
        """, (npc_id, participant_id, agent_id, agent_type))
        result = cursor.fetchone()
        db.commit()
        return AgentMapping(**dict(result))

def get_agent_mapping(
    npc_id: str, 
    participant_id: str, 
    agent_type: str = "letta"
) -> Optional[AgentMapping]:
    """Get existing NPC agent mapping"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM agent_mappings 
            WHERE npc_id = ? AND participant_id = ? AND agent_type = ?
        """, (npc_id, participant_id, agent_type))
        result = cursor.fetchone()
        return AgentMapping(**dict(result)) if result else None

class ClusterData(BaseModel):
    members: List[str]
    npcs: int
    players: int

class GroupData(BaseModel):
    members: List[str]
    npcs: int
    players: int
    formed: int

class HumanContextData(BaseModel):
    relationships: List[Any]
    currentGroups: GroupData
    recentInteractions: List[Any]
    lastSeen: int

class GameSnapshot(BaseModel):
    timestamp: int
    clusters: List[ClusterData]
    events: List[Any]
    humanContext: Dict[str, HumanContextData]