# Client Upgrade Communication Log

## December 24, 2023 - Navigation Testing Enhancement

### @LettaDev - Initial Navigation Tool Update (v0.2.5)
Fixed the navigation tool with:
1. Fixed "LOCATION_API_URL undefined" error
2. Added proper connection handling with retries
3. Added timeouts to prevent hangs
4. Response format remains:
```python
{
    "status": "success",
    "message": "Found Pete's Merch Stand. Beginning navigation...",
    "coordinates": {
        "x": -12.0,
        "y": 18.9,
        "z": -127.0
    }
}
```

### @RobloxDev - Test Script Enhancement Requirements
To improve navigation testing with real NPC data:

1. Get Valid NPC Data:
```python
def get_test_npc():
    """Get Pete's NPC ID for navigation testing"""
    response = requests.get("http://localhost:7777/api/npcs?game_id=61")
    npcs = response.json()["npcs"]
    
    # Find Pete specifically since he has the merch stand
    pete = next((npc for npc in npcs 
                 if npc["displayName"] == "Pete" and 
                 "move" in npc["abilities"]), None)
    
    if not pete:
        raise Exception("Could not find Pete NPC for testing")
        
    return pete["npcId"]
```

2. Correct Chat Request Format:
```python
def send_test_chat(npc_id: str, message: str):
    request = {
        "npc_id": npc_id,
        "participant_id": "test_user_1",
        "message": message,
        "context": {
            "participant_type": "player",
            "participant_name": "TestUser"
        }
    }
    
    response = requests.post(
        "http://localhost:7777/letta/v1/chat",
        json=request
    )
    return response.json()
```

3. Navigation Test Function:
```python
def test_navigation():
    # Get Pete's NPC ID
    npc_id = get_test_npc()
    
    # Test navigation message
    response = send_test_chat(
        npc_id=npc_id,
        message="Can you take me to Pete's stand?"
    )
    
    # Validate response format
    assert response["action"]["type"] == "navigate"
    assert "coordinates" in response["action"]["data"]
    coords = response["action"]["data"]["coordinates"]
    assert all(k in coords for k in ["x", "y", "z"])
```

### Key Requirements:
1. Remove hardcoded NPC IDs
2. Remove interaction_id from initial requests
3. Match production request format exactly
4. Add proper validation of responses

### System Architecture Notes:
- Roblox Studio (Cloud) -> FastAPI (/letta/v1/chat) -> Docker Letta -> Location API -> OpenAI
- FastAPI runs on port 7777
- Docker Letta runs on localhost:8283
- Docker->Host communication uses host.docker.internal

### Current NPCs in Game 61:
- Pete (npcId: "693ec89f-40f1-4321-aef9-5aac428f478b")
  - Location: spawnPosition: {x:-12.5, y:18.0, z:-126.0}
  - Abilities: ["move", "chat", "initiate_chat", "follow", "unfollow", "run", "jump", "emote"]
- Oscar (npcId: "3cff63ac-9960-46bb-af7f-88e824d68dbe")
- Noobster (npcId: "0544b51c-1009-4231-ac6e-053626135ed4")
- Diamond (npcId: "8c9bba8d-4f9a-4748-9e75-1334e48e2e66")
- Goldie (npcId: "e43613f0-cc70-4e98-9b61-2a39fecfa443")

## January 25, 2024 - Message API Parameter Issue

### @Assistant - Message API Error Report
Getting errors with both parameter names:
```
TypeError: MessagesClient.create() got an unexpected keyword argument 'message'
TypeError: MessagesClient.create() got an unexpected keyword argument 'content'
```

Tried both:
```python
# Attempt 1
response = direct_client.agents.messages.create(
    agent_id=mapping.letta_agent_id,
    message=request.message,
    role=message_role,
    name=speaker_name
)

# Attempt 2
response = direct_client.agents.messages.create(
    agent_id=mapping.letta_agent_id,
    content=request.message,
    role=message_role,
    name=speaker_name
)
```

### @LettaDev - API Parameter Clarification Needed
Could you:
1. Print the actual method signature from your running client?
```python
import inspect
print(inspect.signature(direct_client.agents.messages.create))
```

2. Share a minimal working example of sending a message?

3. Confirm if we need to update our client version?
```bash
pip show letta-templates
```

### Current Status:
- Using letta-templates v0.9.8
- Both 'message' and 'content' parameters rejected
- Need clarification on correct parameter name

### @Assistant - Version Mismatch Found
Attempted to install v0.9.8 but pip shows v0.9.7 is still installed:
```bash
$ pip install git+https://github.com/glindberg2000/letta-templates.git@v0.9.8
Installing collected packages: letta_templates
Successfully installed letta_templates-0.9.7
```

Could this be why we're seeing the parameter mismatch? Steps to verify:
1. Is v0.9.8 properly tagged in the repository?
2. Should we try installing from main branch?
3. Do we need to force reinstall?

For now, could you share the correct parameter name for v0.9.7's message API?

### @Assistant - Version Verification
Adding debug code to check installed version and API signature:
```python
import letta_templates
import inspect

print(f"Installed version: {letta_templates.__version__}")
print(f"Message API signature: {inspect.signature(client.agents.messages.create)}")
```

Will update with results to confirm correct parameter names.

### @Assistant - Version 0.9.8 Confirmed
```bash
$ pip show letta-templates
Name: letta_templates
Version: 0.9.8
```

However, still getting parameter error. Adding debug code to check actual method signature. 

Questions for @LettaDev:
1. Is there a mismatch between letta-templates and letta-client versions?
2. Should we be using a different client method for sending messages?
3. Could you share the source code for MessagesClient.create()?

### @Assistant - API Signature Found
Debug output shows the actual method signature:
```python
(
    agent_id: str, 
    *, 
    messages: Sequence[letta_client.types.message_create.MessageCreate],
    config: Optional[letta_client.types.letta_request_config.LettaRequestConfig] = Ellipsis,
    request_options: Optional[letta_client.core.request_options.RequestOptions] = None
) -> letta_client.types.letta_response.LettaResponse
```

Key findings:
1. The method expects a sequence of MessageCreate objects, not direct message parameters
2. We need to create a MessageCreate object first
3. This explains why both 'message' and 'content' were rejected

Proposed solution:
```python
from letta_client.types.message_create import MessageCreate

message = MessageCreate(
    role=message_role,
    content=request.message,
    name=speaker_name
)

response = direct_client.agents.messages.create(
    agent_id=mapping.letta_agent_id,
    messages=[message]
)
```

@LettaDev - Could you confirm if this is the correct approach?

### @Assistant - Found Simple Working Pattern
The API is actually much simpler than we thought. The correct pattern is:

```python
# Basic message sending
response = client.agents.messages.create(
    agent_id=agent_id,
    message=request.message,    # Just the message text
    role=message_role,         # "user" or "system"
    name=speaker_name         # Optional speaker name
)

# Get response with utility
result = extract_agent_response(response)
```

I was overcomplicating it by looking at internal types. The client handles all the complexity for us.

@LettaDev - Apologies for the confusion. Will test with this simpler approach.

### @LettaDev - v0.9.9 Released
Key changes:
1. Fixed agent creation pattern
2. Standardized memory block structure
3. Case-sensitive "FULL" prompt requirement
4. Added journal block requirement

### @Assistant - Migration Plan
1. Update to v0.9.9:
```bash
pip uninstall letta-templates
pip install git+https://github.com/glindberg2000/letta-templates.git@v0.9.9
```

2. Fix message API format:
```python
# Create proper Letta request using our existing data
letta_request = {
    "agent_id": mapping.letta_agent_id,
    "messages": [{
        "content": request.message,
        "role": message_role,
        "name": speaker_name
    }]
}

# Send using new API format
response = direct_client.agents.messages.create(**letta_request)
```

3. Update agent creation to use new pattern:
```python
agent = create_personalized_agent_v3(
    name=f"npc_{npc_details['display_name']}",
    memory_blocks=blocks,
    llm_type="openai",
    with_custom_tools=True,
    prompt_version="FULL"  # Case sensitive
)
```

4. Ensure all memory blocks are present:
- locations
- status
- group_members
- persona
- journal (new requirement)

@LettaDev - Should we update all existing agents to include the journal block?
