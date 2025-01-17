"""Test script for Lua file generation"""
import json
from pathlib import Path

def generate_test_lua(data: dict) -> str:
    """Convert dictionary data to Lua format"""
    # Start with return statement
    lua_content = "return {\n"
    
    # Handle NPCs
    if "npcs" in data:
        lua_content += "    npcs = {\n"
        for npc in data["npcs"]:
            lua_content += f"""        {{
            id = "{npc['id']}",
            displayName = "{npc['displayName']}",
            assetId = "{npc['assetId']}",
            model = "{npc.get('model', '')}",
            systemPrompt = [[{npc.get('systemPrompt', '')}]],
            responseRadius = {npc.get('responseRadius', 20)},
            spawnPosition = {json.dumps(npc.get('spawnPosition', {"x": 0, "y": 5, "z": 0}))},
            abilities = {json.dumps(npc.get('abilities', []))},
            shortTermMemory = {{}}
        }},\n"""
        lua_content += "    },\n"
            
    # Close the table
    lua_content += "}\n"
    return lua_content

def test_npc_export():
    """Test NPC data export to Lua"""
    # Test data
    test_data = {
        "npcs": [
            {
                "id": "npc_1",
                "displayName": "Test NPC",
                "assetId": "12345",
                "model": "test_model",
                "systemPrompt": "I am a test NPC",
                "responseRadius": 30,
                "spawnPosition": {"x": 10, "y": 5, "z": 10},
                "abilities": ["walk", "talk"]
            }
        ]
    }
    
    # Generate Lua
    lua_content = generate_test_lua(test_data)
    print("\nGenerated Lua content:")
    print(lua_content)
    
    # Save to test file
    test_file = Path("test_npc_database.lua")
    test_file.write_text(lua_content)
    print(f"\nSaved to: {test_file.absolute()}")

if __name__ == "__main__":
    test_npc_export() 