from typing import Dict, Optional
import logging
from .cache import (
    get_npc_description,
    get_player_info,
    get_player_description
)
from .models import GroupUpdate
from datetime import datetime
from letta_templates.npc_utils_v2 import (
    add_group_member,
    remove_group_member,
    update_group_members_v2
)
import json

logger = logging.getLogger(__name__)

class GroupProcessor:
    def __init__(self, letta_client):
        self.client = letta_client
        
    async def process_group_update(
        self,
        npc_id: str,
        player_id: str,
        is_joining: bool,
        player_name: Optional[str] = None,
        purge: bool = False
    ) -> Dict:
        """
        Process a single NPC's group update when a player joins/leaves
        """
        try:
            logger.info(f"\nProcessing group update:")
            logger.info(f"  Agent ID: {npc_id}")
            logger.info(f"  Player: {player_id} ({player_name})")
            logger.info(f"  Action: {'purge' if purge else 'joining' if is_joining else 'leaving'}")

            # Get player description
            player_appearance = get_player_description(player_name)
            logger.info(f"\nPlayer data:")
            logger.info(f"  Description: {player_appearance}")

            if purge:
                group_state = update_group_members_v2(
                    self.client,
                    agent_id=npc_id,
                    players=[],  # Empty list to clear group
                    update_message="Group purged",
                    send_notification=False
                )
                return {
                    "success": True,
                    "action": "purged",
                    "group_size": 0
                }

            if is_joining:
                # Add single member with details
                group_state = add_group_member(
                    self.client,
                    agent_id=npc_id,
                    player_id=player_id,
                    player_name=player_name,
                    appearance=player_appearance,
                    notes="Joined group",
                    update_message=f"{player_name} joined the group",
                    send_notification=False
                )
                action = "joined"
            else:
                # Remove single member
                group_state = remove_group_member(
                    self.client,
                    agent_id=npc_id,
                    player_id=player_id,
                    update_message=f"{player_name} left the group",
                    send_notification=False
                )
                action = "left"

            logger.info("\nUpdated group state:")
            logger.info(json.dumps(group_state, indent=2))

            return {
                "success": True,
                "action": action,
                "group_size": len(group_state.get("members", {}))
            }

        except Exception as e:
            logger.error(f"Failed to update group: {e}")
            return {"success": False, "error": str(e)} 