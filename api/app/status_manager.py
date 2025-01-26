import logging
from typing import Dict, Optional
from .models import GameSnapshot, HumanContextData
from .cache import get_npc_id_from_name, get_agent_id, get_player_info
from letta_templates.npc_utils_v2 import update_location_status, update_group_members_v2
from letta_templates.npc_tools import create_letta_client

logger = logging.getLogger(__name__)

direct_client = create_letta_client()

async def update_status_block(entity_id: str, context: Optional[HumanContextData], enriched_snapshot: GameSnapshot):
    """Update NPC status with enriched context and group info"""
    try:
        if not context:
            logger.warning(f"No context data for {entity_id}, skipping status update")
            return

        agent_id = get_agent_id(get_npc_id_from_name(entity_id))
        if not agent_id:
            logger.warning(f"No agent found for NPC {entity_id}")
            return

        updates = []
        
        # Location updates (optional)
        if context.location:
            updates.append(f"Location: {context.location}")
        
        # Health status (optional)
        try:
            if hasattr(context, 'health') and context.health:
                health = context.health
                current = health.get('current', 0)
                max_health = health.get('max', 100)
                state = health.get('state', '')

                if state == 'Dead':
                    updates.append("Status: Dead")
                elif current < max_health * 0.3:
                    updates.append("Status: Severely injured")
                elif current < max_health * 0.7:
                    updates.append("Status: Injured")
        except Exception as e:
            logger.warning(f"Error processing health for {entity_id}: {e}")
        
        # Activity state (optional)
        if hasattr(context, 'currentActivity') and context.currentActivity:
            updates.append(f"Activity: {context.currentActivity}")
        
        # Group status - handle missing or partial data
        try:
            if hasattr(context, 'currentGroups') and context.currentGroups and context.currentGroups.members:
                member_info = []
                for member in context.currentGroups.members:
                    try:
                        player_info = get_player_info(member)
                        member_info.append({
                            "id": member,
                            "name": member,
                            "location": (enriched_snapshot.humanContext.get(member, {})
                                       .get('location', 'Unknown'))
                        })
                    except Exception as e:
                        logger.warning(f"Error processing member {member}: {e}")
                        continue

                if member_info:  # Only update if we have valid members
                    try:
                        await update_group_members_v2(
                            client=direct_client,
                            agent_id=agent_id,
                            nearby_players=member_info
                        )
                        updates.append(f"Group: With {len(member_info)} others")
                    except Exception as e:
                        logger.error(f"Error updating group members: {e}")
                        updates.append("Group: Alone")  # Add on error
                else:
                    updates.append("Group: Alone")  # Add if no valid members
            else:
                updates.append("Group: Alone")  # Add if no group data
        except Exception as e:
            logger.error(f"Error processing group data: {e}")
            updates.append("Group: Alone")  # Add on any error
        
        # Update status if we have any updates
        if updates:
            try:
                status_text = " | ".join(updates)
                logger.info(f"Updating status for {entity_id}: {status_text}")
                
                await update_location_status(
                    client=direct_client,
                    agent_id=agent_id,
                    current_location=context.location or 'Unknown',
                    current_action=status_text
                )
            except Exception as e:
                logger.error(f"Error updating status: {e}")
                
    except Exception as e:
        logger.error(f"Error in status block update for {entity_id}: {e}", exc_info=True) 