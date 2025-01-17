# app/conversation_managerV2.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, ConfigDict
from .models import ConversationMetrics
import uuid
import logging

logger = logging.getLogger("roblox_app")

class Participant(BaseModel):
    id: str
    type: Literal["npc", "player"]
    name: str

class Message(BaseModel):
    sender_id: str
    content: str
    timestamp: datetime

class Conversation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    type: Literal["npc_user", "npc_npc", "group"]
    participants: Dict[str, Participant]
    messages: List[Message]
    created_at: datetime
    last_update: datetime
    metadata: Dict[str, Any] = {}

class ConversationMetrics:
    def __init__(self):
        self.total_conversations = 0
        self.successful_conversations = 0
        self.failed_conversations = 0
        self.average_duration = 0.0
        self.active_conversations = 0
        self.completed_conversations = 0
        self.average_response_time = 0.0
        self.total_messages = 0

    def dict(self):
        return {
            "total_conversations": self.total_conversations,
            "successful_conversations": self.successful_conversations,
            "failed_conversations": self.failed_conversations,
            "average_duration": self.average_duration,
            "active_conversations": self.active_conversations,
            "completed_conversations": self.completed_conversations,
            "average_response_time": self.average_response_time,
            "total_messages": self.total_messages
        }

class ConversationManagerV2:
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.participant_conversations: Dict[str, List[str]] = {}
        self.expiry_time = timedelta(minutes=30)
        self.metrics = ConversationMetrics()

    def create_conversation(
        self,
        type: Literal["npc_user", "npc_npc", "group"],
        participant1_data: Dict[str, Any],
        participant2_data: Dict[str, Any]
    ) -> str:
        """Create a new conversation between participants"""
        try:
            # Create Participant objects from dictionaries
            participant1 = Participant(
                id=participant1_data["id"],
                type=participant1_data.get("type", "npc"),
                name=participant1_data.get("name", f"Entity_{participant1_data['id']}")
            )
            
            participant2 = Participant(
                id=participant2_data["id"],
                type=participant2_data.get("type", "player"),
                name=participant2_data.get("name", f"Entity_{participant2_data['id']}")
            )

            conversation_id = str(uuid.uuid4())
            now = datetime.now()
            
            conversation = Conversation(
                id=conversation_id,
                type=type,
                participants={
                    participant1.id: participant1,
                    participant2.id: participant2
                },
                messages=[],
                created_at=now,
                last_update=now,
                metadata={}
            )
            
            # Store conversation
            self.conversations[conversation_id] = conversation
            
            # Update participant indexes
            for p_id in [participant1.id, participant2.id]:
                if p_id not in self.participant_conversations:
                    self.participant_conversations[p_id] = []
                self.participant_conversations[p_id].append(conversation_id)
            
            # Update metrics
            self.metrics.total_conversations += 1
            self.metrics.active_conversations += 1
                
            logger.info(f"Created conversation {conversation_id} between {participant1.name} and {participant2.name}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None

    def add_message(self, conversation_id: str, sender_id: str, content: str) -> bool:
        """Add a message to a conversation"""
        try:
            conversation = self.conversations.get(conversation_id)
            if not conversation:
                return False
                
            message = Message(
                sender_id=sender_id,
                content=content,
                timestamp=datetime.now()
            )
            
            conversation.messages.append(message)
            conversation.last_update = datetime.now()
            
            # Update metrics
            self.metrics.total_messages += 1
            
            return True
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False

    def end_conversation(self, conversation_id: str) -> bool:
        """End and clean up a conversation"""
        try:
            conversation = self.conversations.get(conversation_id)
            if not conversation:
                return False
                
            # Update metrics
            self.metrics.active_conversations -= 1
            self.metrics.completed_conversations += 1
            
            # Calculate response time metrics
            if len(conversation.messages) > 1:
                total_time = (conversation.last_update - conversation.created_at).total_seconds()
                avg_time = total_time / len(conversation.messages)
                self._update_average_response_time(avg_time)
            
            # Remove from participant tracking
            for participant_id in conversation.participants:
                if participant_id in self.participant_conversations:
                    self.participant_conversations[participant_id].remove(conversation_id)
                    
            # Remove conversation
            del self.conversations[conversation_id]
            return True
            
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            return False

    def _update_average_response_time(self, response_time: float):
        """Update average response time metric"""
        current = self.metrics.average_response_time
        total = self.metrics.total_messages
        if total > 0:
            self.metrics.average_response_time = (current * (total - 1) + response_time) / total
        else:
            self.metrics.average_response_time = response_time

    def get_history(self, conversation_id: str, limit: Optional[int] = None) -> List[str]:
        """Get conversation history as a list of messages"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return []
            
        messages = [msg.content for msg in conversation.messages]
        if limit:
            messages = messages[-limit:]
            
        return messages

    def get_conversation_context(self, conversation_id: str) -> Dict:
        """Get full conversation context"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {}
            
        return {
            "type": conversation.type,
            "participants": {
                pid: participant.model_dump() 
                for pid, participant in conversation.participants.items()
            },
            "created_at": conversation.created_at.isoformat(),
            "last_update": conversation.last_update.isoformat(),
            "message_count": len(conversation.messages),
            "metadata": conversation.metadata
        }

    def get_active_conversations(self, participant_id: str) -> List[str]:
        """Get all active conversations for a participant"""
        return self.participant_conversations.get(participant_id, [])

    def cleanup_expired(self) -> int:
        """Remove expired conversations"""
        now = datetime.now()
        expired = []
        
        for conv_id, conv in self.conversations.items():
            if now - conv.last_update > self.expiry_time:
                expired.append(conv_id)
                
        for conv_id in expired:
            self.end_conversation(conv_id)
            
        return len(expired)