from typing import Dict, Optional, List
import logging
from .cache import (
    get_npc_description,
    get_player_info,
    get_player_description
)
from .models import GroupUpdate
from datetime import datetime
from letta_templates.npc_utils_v2 import upsert_group_member
import json

logger = logging.getLogger(__name__)

class GroupProcessor:
    def __init__(self, letta_client):
        self.client = letta_client
        
    def get_health_status(self, health_data):
        """Convert health numbers to status string"""
        if not health_data:
            return "healthy"  # Default state
            
        current = health_data.get('current', 0)
        max_health = health_data.get('max', 100)
        percentage = (current / max_health) * 100
        
        if current <= 0:
            return "dead"
        elif percentage <= 25:
            return "critical"
        elif percentage <= 75:
            return "injured"
        return "healthy"
        
    async def batch_update_members(
        self,
        npc_id: str,
        updates: List[Dict]
    ) -> Dict:
        """Efficiently update multiple members at once"""
        results = []
        for update in updates:
            try:
                # Prepare update data
                update_data = {
                    "name": update["name"],
                    "is_present": update["is_joining"],
                    "appearance": get_player_description(update["name"]),
                    "health_status": self.get_health_status(update.get("health_data")),
                    "last_location": update.get("location", "Unknown")
                }
                
                if not update["is_joining"]:
                    update_data["last_seen"] = datetime.now().isoformat()

                # Single update call per member
                result = upsert_group_member(
                    self.client,
                    agent_id=npc_id,
                    entity_id=update["entity_id"],
                    update_data=update_data
                )
                
                results.append({
                    "entity_id": update["entity_id"],
                    "success": result["success"],
                    "message": result["message"],
                    "error": result.get("error"),
                    "data": result.get("data")
                })
                
            except Exception as e:
                logger.error(f"Failed to update member {update['entity_id']}: {e}")
                results.append({
                    "entity_id": update["entity_id"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": any(r["success"] for r in results),
            "results": results
        }
        
    async def process_group_update(
        self,
        npc_id: str,
        player_id: str,
        is_joining: bool,
        player_name: Optional[str] = None,
        health_data: Optional[Dict] = None,
        location: Optional[str] = None,
        purge: bool = False
    ) -> Dict:
        """Process group member updates efficiently using single-call pattern"""
        try:
            logger.info(f"\nProcessing group update:")
            logger.info(f"  Agent ID: {npc_id}")
            logger.info(f"  Player: {player_id} ({player_name})")
            logger.info(f"  Action: {'joining' if is_joining else 'leaving'}")

            # Get player description
            player_appearance = get_player_description(player_name)
            
            # Prepare update data with all available fields
            update_data = {
                "name": player_name,
                "is_present": is_joining,
                "appearance": player_appearance,
                "health_status": self.get_health_status(health_data),
                "last_location": location or "Unknown"
            }
            
            # Add last_seen for departing members
            if not is_joining:
                update_data["last_seen"] = datetime.now().isoformat()

            try:
                # Single efficient update call
                result = upsert_group_member(
                    self.client,
                    agent_id=npc_id,
                    entity_id=player_id,
                    update_data=update_data
                )
                
                logger.info("\nUpdated group state:")
                logger.info(json.dumps(result, indent=2))

                if not result["success"]:
                    return {
                        "success": False,
                        "error": result["error"]
                    }

                return {
                    "success": True,
                    "action": "joined" if is_joining else "left",
                    "message": result["message"],
                    "group_size": result["data"]["group_size"],
                    "present_count": result["data"]["present_count"]
                }

            except Exception as e:
                logger.error(f"Exception during group update: {e}")
                return {"success": False, "error": str(e)}

        except Exception as e:
            logger.error(f"Failed to process group update: {e}")
            return {"success": False, "error": str(e)} 