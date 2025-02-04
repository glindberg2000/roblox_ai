# app/models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal, Set
from datetime import datetime, timedelta
import logging
from .location_utils import find_nearest_location

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

class InteractionData(BaseModel):
    timestamp: int
    narrative: str

class PositionData(BaseModel):
    x: float
    y: float
    z: float

    def __init__(self, **data):
        # Round coordinates to 3 decimal places for cleaner output
        for coord in ['x', 'y', 'z']:
            if coord in data:
                data[coord] = round(float(data[coord]), 3)
        super().__init__(**data)

    def get_nearest_location(self) -> str:
        """Calculate nearest known location"""
        from .cache import LOCATION_CACHE  # Import here to avoid circular import
        return find_nearest_location(self.x, self.y, self.z, LOCATION_CACHE)

    def get_location_narrative(self) -> str:
        """Generate narrative description of position relative to known locations"""
        try:
            from .cache import LOCATION_CACHE
            
            logger.debug(f"Generating location narrative for position ({self.x}, {self.y}, {self.z})")
            
            if not LOCATION_CACHE:
                logger.warning("Location cache is empty")
                return f"at coordinates ({self.x}, {self.y}, {self.z})"

            min_distance = float('inf')
            nearest = None

            for slug, loc_data in LOCATION_CACHE.items():
                loc_x, loc_y, loc_z = loc_data["coordinates"]
                # Calculate distance the same way as test
                distance = ((self.x - loc_x)**2 + 
                           (self.y - loc_y)**2 + 
                           (self.z - loc_z)**2)**0.5
                
                logger.debug(f"Distance to {loc_data['name']}: {distance:.1f}")

                if distance < min_distance:
                    min_distance = distance
                    nearest = loc_data

            if nearest:
                narrative = self._get_distance_description(min_distance, nearest['name'])
                logger.debug(f"Generated narrative: {narrative}")
                return narrative

            return f"at coordinates ({self.x}, {self.y}, {self.z})"

        except Exception as e:
            logger.error(f"Error generating location narrative: {str(e)}")
            return f"at coordinates ({self.x}, {self.y}, {self.z})"

    def _get_distance_description(self, distance: float, location_name: str) -> str:
        """Helper to generate distance-based description"""
        logger.debug(f"Calculating description for distance {distance:.1f} to {location_name}")
        
        if distance < 5:
            desc = f"at the entrance to {location_name}"
        elif distance < 15:
            desc = f"right outside {location_name}"
        elif distance < 30:
            desc = f"near {location_name}"
        elif distance < 50:
            desc = f"in the vicinity of {location_name}"
        else:
            desc = f"at ({self.x}, {self.y}, {self.z})"
        
        logger.debug(f"Generated description: {desc} (distance: {distance:.1f})")
        return desc

class GroupData(BaseModel):
    members: List[str]
    npcs: int
    players: int
    formed: int
    updates: List[str] = []

class HumanContextData(BaseModel):
    health: Optional[Dict[str, Any]] = None
    position: Optional[PositionData] = None
    currentGroups: Optional[GroupData] = None
    recentInteractions: Optional[List[InteractionData]] = None
    stateTimestamp: Optional[int] = None
    lastSeen: Optional[int] = None
    positionTimestamp: Optional[int] = None
    location: Optional[str] = None
    needs_status_update: bool = False

class GameSnapshot(BaseModel):
    timestamp: int  # Required
    events: List[Dict[str, Any]]  # Required
    clusters: List[Dict[str, Any]]
    humanContext: Dict[str, Any]

class ChatRequest(BaseModel):
    npc_id: str
    participant_id: str
    messages: List[Dict[str, str]]  # Array of {content, role, name}
    context: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None

class GroupUpdate(BaseModel):
    npc_id: str
    player_id: str
    is_joining: bool
    player_name: Optional[str] = None
    purge: Optional[bool] = False