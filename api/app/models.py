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

class ClusterCache:
    """
    Manages NPC cluster information with delayed member removal.
    
    Attributes:
        clusters: Dict mapping npc_id to cluster information
        pending_removals: Dict tracking entities pending removal from clusters
        REMOVAL_DELAY: How long to keep entities in context after leaving
    """
    def __init__(self):
        self.clusters: Dict[str, Dict] = {}  # npc_id -> cluster info
        self.pending_removals: Dict[str, Dict] = {}  # npc_id_entity_id -> removal timestamp
        self.REMOVAL_DELAY = timedelta(seconds=30)
    
    def update_from_context(self, npc_id: str, context: dict) -> Dict:
        """Update cluster info from chat context"""
        current_time = datetime.now()
        
        logger.info(f"Updating cluster for NPC {npc_id}")
        
        # Extract nearby entities from context
        current_players = set()
        current_npcs = set()
        
        # Handle nearby players
        nearby_players = context.get("nearby_players", [])
        if nearby_players:
            if isinstance(nearby_players[0], dict):
                current_players = {p["name"] for p in nearby_players}
            else:
                current_players = set(nearby_players)
            
        # Handle nearby NPCs - check if participant is an NPC
        if context.get("participant_type") == "npc":
            current_npcs.add(context["participant_name"])
        
        # Also add any NPCs from nearby_npcs field
        nearby_npcs = context.get("nearby_npcs", [])
        if nearby_npcs:
            current_npcs.update(nearby_npcs)
        
        logger.info(f"Current players in proximity: {current_players}")
        logger.info(f"Current NPCs in proximity: {current_npcs}")
        
        # Get or create cluster info
        cluster_info = self.clusters.get(npc_id, {
            "members": {
                "players": current_players,
                "npcs": current_npcs
            },
            "last_update": current_time,
            "context": {}
        })
        
        # Handle new players
        new_players = current_players - cluster_info["members"]["players"]
        if new_players:
            logger.info(f"New players joined cluster {npc_id}: {new_players}")
            cluster_info["members"]["players"].update(new_players)
        
        # Handle new NPCs
        new_npcs = current_npcs - cluster_info["members"]["npcs"]
        if new_npcs:
            logger.info(f"New NPCs joined cluster {npc_id}: {new_npcs}")
            cluster_info["members"]["npcs"].update(new_npcs)
        
        # Handle members who left
        left_players = cluster_info["members"]["players"] - current_players
        left_npcs = cluster_info["members"]["npcs"] - current_npcs
        
        for member in left_players:
            self._add_to_pending_removals(npc_id, member, "player")
        for member in left_npcs:
            self._add_to_pending_removals(npc_id, member, "npc")
        
        # Process pending removals
        self._process_pending_removals(npc_id)
        
        # Update context
        cluster_info["context"] = context
        cluster_info["last_update"] = current_time
        self.clusters[npc_id] = cluster_info
        
        logger.info(f"Final cluster state for {npc_id}: {cluster_info}")
        
        return cluster_info

    def _process_pending_removals(self, npc_id):
        # Get pending removals for this NPC
        pending = [
            info for key, info in self.pending_removals.items()
            if key.startswith(f"{npc_id}_")
        ]
        if not pending:
            return

        # Get the cluster for this NPC
        cluster = self.clusters.get(npc_id)
        if not cluster:
            return

        # Process each pending removal
        for info in pending:
            try:
                member_type = info["type"]  # "player" or "npc"
                member = info["member"]
                
                # Remove from appropriate set in members dict
                if member in cluster["members"][f"{member_type}s"]:
                    cluster["members"][f"{member_type}s"].discard(member)
                    logger.info(f"Removed {member_type} {member} from cluster {npc_id}")
                    
                # Remove from pending removals
                removal_key = f"{npc_id}_{member}"
                if removal_key in self.pending_removals:
                    del self.pending_removals[removal_key]
                    
            except Exception as e:
                logger.error(f"Error removing member from cluster: {e}")
                logger.error(f"Cluster state: {cluster}")
                logger.error(f"Info: {info}")

    def _add_to_pending_removals(self, npc_id: str, member: str, member_type: str):
        """Add a member to pending removals"""
        removal_key = f"{npc_id}_{member}"
        if removal_key not in self.pending_removals:
            self.pending_removals[removal_key] = {
                "timestamp": datetime.now(),
                "member": member,
                "type": member_type
            }
            logger.info(f"Added {member} to pending removals")

class ClusterData(BaseModel):
    members: List[str]
    npcs: int
    players: int

class GroupData(BaseModel):
    primary: str
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