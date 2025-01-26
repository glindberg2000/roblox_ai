from typing import Dict, Set
import time
import logging
from .models import HumanContextData
from .database import get_player_info  # For avatar descriptions
from .letta_client import direct_client
from .letta_utils import extract_tool_results
from .npc_cache import get_npc_id_from_name, get_agent_id

logger = logging.getLogger(__name__)

class GroupMembershipManager:
    def __init__(self):
        self.pending_removals: Dict[str, float] = {}  # {member_id: timestamp}
        self.removal_timeout = 300  # 5 minutes
    
    def cancel_pending_removal(self, member_id: str):
        """Cancel pending removal if member returns"""
        if member_id in self.pending_removals:
            logger.info(f"Cancelling pending removal for returning member {member_id}")
            del self.pending_removals[member_id]
    
    def queue_removal(self, member_id: str):
        """Queue member for removal"""
        if member_id not in self.pending_removals:
            logger.info(f"Queueing {member_id} for removal")
            self.pending_removals[member_id] = time.time()
    
    def get_expired_removals(self) -> Set[str]:
        """Get members whose removal time has expired"""
        current_time = time.time()
        expired = {
            member for member, timestamp in self.pending_removals.items()
            if current_time - timestamp > self.removal_timeout
        }
        for member in expired:
            del self.pending_removals[member]
        return expired

    async def handle_group_change(self, npc_id: str, context: HumanContextData, prev_state: Dict):
        """Handle group membership changes with delayed removal"""
        if not context.currentGroups:
            return
            
        current_members = set(context.currentGroups.members)
        prev_members = set(prev_state.get('currentGroups', {}).get('members', []))
        
        # Handle new members
        new_members = current_members - prev_members
        if new_members:
            await self._handle_new_members(npc_id, new_members)
        
        # Handle departing members
        departed = prev_members - current_members
        if departed:
            await self._handle_departing_members(npc_id, departed)
        
        # Process any pending removals
        await self._process_pending_removals(npc_id)
    
    async def _handle_new_members(self, npc_id: str, new_members: Set[str]):
        """Process new group members"""
        agent_id = get_agent_id(npc_id)
        if not agent_id:
            logger.warning(f"No agent found for NPC {npc_id}")
            return
            
        # Cancel any pending removals for returning members
        for member in new_members:
            if member in self.pending_removals:
                logger.info(f"Cancelling pending removal for returning member {member}")
                del self.pending_removals[member]
                continue
        
        # Add new members with their avatar descriptions
        try:
            member_profiles = []
            for member_id in new_members:
                # Get stored avatar description
                player_info = get_player_info(member_id)
                if player_info and player_info.get('avatar_description'):
                    member_profiles.append({
                        "id": member_id,
                        "name": member_id,
                        "join_date": time.time(),
                        "appearance": player_info['avatar_description']
                    })
                else:
                    logger.warning(f"No avatar description found for {member_id}")
                    member_profiles.append({
                        "id": member_id,
                        "name": member_id,
                        "join_date": time.time()
                    })
            
            # Send system message to NPC about new members
            system_msg = f"[SYSTEM] New group members have joined: {', '.join(new_members)}. " \
                        f"Their profiles have been added to your group. Consider making note of " \
                        f"any important details about them."
            
            # Let the NPC process the new members through its own tools
            await direct_client.agents.messages.create(
                agent_id=agent_id,
                role="system",
                content=system_msg
            )
            
            logger.info(f"Added new members to {npc_id}'s group and notified NPC: {new_members}")
            
        except Exception as e:
            logger.error(f"Error handling new members: {e}")
    
    async def _handle_departing_members(self, npc_id: str, departed: Set[str]):
        """Queue departing members for potential removal"""
        current_time = time.time()
        for member in departed:
            if member not in self.pending_removals:
                logger.info(f"Queueing {member} for removal from {npc_id}'s group")
                self.pending_removals[member] = current_time
    
    async def _process_pending_removals(self, npc_id: str):
        """Process pending member removals and let NPC archive memories"""
        current_time = time.time()
        agent_id = get_agent_id(npc_id)
        if not agent_id:
            return
            
        for member, timestamp in list(self.pending_removals.items()):
            time_elapsed = current_time - timestamp
            
            # Time to notify NPC to archive memories
            if time_elapsed > self.removal_timeout:
                try:
                    # Final notification about member removal
                    system_msg = f"[SYSTEM] {member} has been removed from your group."
                    await direct_client.agents.messages.create(
                        agent_id=agent_id,
                        role="system",
                        content=system_msg
                    )
                    
                    del self.pending_removals[member]
                    logger.info(f"Processed removal of {member} from {npc_id}'s group")
                    
                except Exception as e:
                    logger.error(f"Error finalizing member removal {member}: {e}") 