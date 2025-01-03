# NPC System Development Status (December 2024)

## Current State

### Core Features Implemented
1. **NPC Management**
   - Create/Edit/Delete NPCs via admin dashboard
   - Asset linking system for NPC models
   - Spawn position management
   - Basic abilities system (move, chat, follow, etc.)

2. **Database Integration**
   - SQLite backend with proper migrations
   - Asset-NPC relationship management
   - Automatic Lua database export
   - Backup system in place

3. **Admin Dashboard**
   - Asset management interface
   - NPC creation and editing
   - Real-time validation
   - Error handling and user feedback

4. **Agent System**
   - Letta AI integration for NPC responses
   - Custom memory blocks for:
     * Human context (human)
     * NPC personality (persona)
     * Known locations (custom)
   - Implemented actions:
     * perform_action
     * navigate_to
     * navigate_to_coordinates

## Potential Future Features
1. **Agent Tools & Memory**
   - Location awareness system
   - NPC relationship tracking
   - Location lookup tools
   - Environment interaction tools

2. **Advanced Behaviors**
   - Location-based behaviors
   - Group interaction handling
   - Dynamic response system

### Recent Fixes
1. **Asset Relationship**
   - Fixed orphaned NPCs issue
   - Improved asset ID handling
   - Added validation for asset existence

2. **Data Export**
   - Added Lua export on NPC creation
   - Maintained export on NPC edits
   - Proper game slug handling

3. **Error Handling**
   - Better validation messages
   - Proper error display in UI
   - Database constraint enforcement

## Current Challenges

1. **Asset Management**
   - Need better handling of asset types
   - Asset preview system needs improvement
   - Asset versioning consideration

2. **NPC Behavior**
   - Basic abilities implemented but need expansion
   - Behavior scripting system needed
   - Better interaction handling

3. **Performance**
   - Database optimization needed for scale
   - Lua export performance considerations
   - Client-side caching strategy needed

4. **Agent Behavior**
   - Missing 'stop' actions for emotes
   - Need better group conversation handling
   - Improve context awareness
   - Better memory persistence

## Next Steps Considerations

1. **Technical Improvements**
   - [ ] Implement asset versioning
   - [ ] Add behavior scripting system
   - [ ] Optimize database queries
   - [ ] Improve error handling
   - [ ] Add 'stop emote' functionality
   - [ ] Implement group chat handling
   - [ ] Improve memory system

2. **Feature Additions**
   - [ ] Advanced NPC behaviors
   - [ ] Group management
   - [ ] Environment interaction
   - [ ] Dynamic spawn points
   - [ ] Enhanced emote system with cancellation
   - [ ] Better location memory
   - [ ] Improved tool usage

3. **Infrastructure**
   - [ ] Better backup strategy
   - [ ] Migration rollback testing
   - [ ] Performance monitoring
   - [ ] Load testing

## Questions for Discussion

1. **Architecture**
   - How should we handle complex NPC behaviors?
   - What's the scaling strategy?
   - Should we consider a different database structure?
   - How to improve agent memory system?
   - Better way to handle action cancellation?

2. **Features**
   - Priority of planned features?
   - Additional features needed?
   - Current feature improvements needed?
   - Which agent tools to add next?
   - How to improve conversation quality?

3. **Integration**
   - How to better integrate with game systems?
   - What additional APIs are needed?
   - External system dependencies?

## Notes
- Current system is stable but needs expansion
- Asset relationship fixes working well
- Need to consider scaling requirements
- Documentation needs updating

## Appendix

### Current Database Schema
```sql
-- Key tables structure
CREATE TABLE npcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_id TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    -- ... other fields
);

-- ... other relevant schema
```

### Key API Endpoints
- POST /api/npcs - Create NPC
- PUT /api/npcs/{npc_id} - Update NPC
- GET /api/npcs - List NPCs
- DELETE /api/npcs/{npc_id} - Delete NPC

### Recent Migration History
- 006_add_asset_slug
- 007_add_asset_slug_trigger
- 009_fix_orphaned_npcs 

### Current Actions
```python
# Verified implemented actions from letta_router.py
ACTIONS = {
    'core': ['perform_action', 'navigate_to', 'navigate_to_coordinates'],
    'abilities': ['move', 'follow', 'wave', 'dance', 'initiate_chat']  # Available through perform_action
}
``` 


## Letta Integration (Updated)

### Agent System
1. **Core Integration**
   - Letta 0.6.6 server integration
   - Custom memory blocks:
     * persona (NPC personality)
     * human (interaction context)
     * locations (navigation data)
   - Tool registration system
   - Autonomous behavior support

2. **Memory System**
   ```python
   # Memory block structure
   memory = BasicBlockMemory(
       blocks=[
           client.create_block(
               label="persona",
               value="NPC personality...",
               limit=2000
           ),
           client.create_block(
               label="locations",
               value=json.dumps({
                   "known_locations": [
                       {
                           "name": "Location Name",
                           "slug": "location_slug"
                       }
                   ]
               }),
               limit=5000
           )
       ]
   )
   ```

3. **Tool System**
   - Navigation Tools:
     * navigate_to(slug) - Location-based movement
     * navigate_to_coordinates(x,y,z) - Direct coordinate movement
   - Action Tools:
     * perform_action("follow", target="player")
     * perform_action("emote", type="wave|dance|sit")
     * perform_action("unfollow")
   - Autonomous Behaviors:
     * Self-initiated navigation
     * Natural conversation endings
     * Dynamic emote usage
     * Location-based decisions

4. **Current Capabilities**
   ```python
   # Available tools
   TOOL_REGISTRY = {
       "navigate_to": navigate_to,
       "navigate_to_coordinates": navigate_to_coordinates,
       "perform_action": perform_action,
       "examine_object": examine_object
   }
   ```

### Recent Improvements
1. **Navigation System**
   - Slug-based location system
   - Coordinate support
   - Autonomous movement
   - Natural transitions

2. **Conversation Management**
   - Graceful endings
   - Loop prevention
   - Natural transitions
   - Context awareness

3. **Behavior System**
   - Emote integration
   - Follow/unfollow actions
   - Location awareness
   - Personality expression

### Next Steps
1. **Tool Enhancements**
   - [ ] Add emote cancellation
   - [ ] Improve group chat handling
   - [ ] Add more complex actions
   - [ ] Enhance location awareness

2. **Memory Improvements**
   - [ ] Add relationship tracking
   - [ ] Improve location memory
   - [ ] Add event memory
   - [ ] Better context retention

3. **Behavior Refinements**
   - [ ] More natural transitions
   - [ ] Better group dynamics
   - [ ] Enhanced personality traits
   - [ ] Improved decision making

