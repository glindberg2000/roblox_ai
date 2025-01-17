import sys
from pathlib import Path

# Add api directory to path
api_dir = Path(__file__).parent.parent
sys.path.append(str(api_dir))

from letta_roblox.client import LettaRobloxClient

def list_agents():
    """List all agents in Letta server and local database"""
    print("Checking Letta server...")
    
    letta_client = LettaRobloxClient("http://localhost:8333")
    try:
        agents = letta_client.list_agents()
        if agents:
            print("\nLetta Agents:")
            print("-" * 40)
            for agent in agents:
                print(f"ID: {agent['id']}")
                print(f"Name: {agent['name']}")
                print(f"Created: {agent['created_at']}")
                if agent.get('memory'):
                    print("\nMemory:")
                    print(f"Persona: {agent['memory'].get('persona', 'Not set')}")
                    print(f"Human: {agent['memory'].get('human', 'Not set')}")
                print("-" * 40)
        else:
            print("No agents found on Letta server")
            
    except Exception as e:
        print(f"! Failed to access Letta server: {e}")

if __name__ == "__main__":
    list_agents() 