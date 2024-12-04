from typing import Dict, Any, Optional
import requests

class LettaRobloxClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def create_agent(self, npc_type: str, initial_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Letta agent"""
        url = f"{self.base_url}/agents"
        data = {
            "type": npc_type,
            "initial_memory": initial_memory
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def send_message(self, agent_id: str, message: str) -> Dict[str, Any]:
        """Send a message to an agent"""
        url = f"{self.base_url}/agents/{agent_id}/messages"
        data = {"message": message}
        print(f"Sending to Letta agent {agent_id}: {data}")
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            print(f"Got response from Letta agent: {response.json()}")
            return response.json()
        except Exception as e:
            print(f"Letta request failed: {str(e)}")
            return {"message": "I'm having trouble processing that right now."}

    def delete_agent(self, agent_id: str) -> None:
        """Delete a Letta agent"""
        url = f"{self.base_url}/agents/{agent_id}"
        response = requests.delete(url)
        response.raise_for_status()

    def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details including memory"""
        url = f"{self.base_url}/agents/{agent_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting agent details: {str(e)}")
            return {}

    def list_agents(self):
        """List all agents"""
        url = f"{self.base_url}/agents"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()