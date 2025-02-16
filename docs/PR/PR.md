# Fix NPC Hunting System

## Current Issue
When an NPC tries to hunt another NPC (e.g. "hunt for Kaiden"), we get an error:
```
attempt to index nil with 'getAllNPCs'
```

This occurs in ActionService.hunt() when trying to look up target NPCs.

## Investigation
From the logs we can see:
1. The hunt command is being processed correctly:
   - Chat system receives "hunt for Kaiden"
   - Action data includes correct target and type
   - ActionService.hunt() is called with proper NPC and data
2. The error occurs specifically when trying to call getAllNPCs()
3. The error happens in TextChannel.ShouldDeliverCallback context

## Working Action Flows
1. Movement Actions:
   - patrol: Uses PatrolService for waypoint navigation
   - follow: Direct target following via MovementService
   - navigate: Point-to-point movement via NavigationService

2. Behavior System:
   - set_behavior appears unused (old system?)
   - Behaviors now handled through BehaviorService directly
   - patrol uses behavior system for state management

3. Potential Duplicates:
   - Both patrol() and set_patrol() exist
   - navigate() vs NavigationService.Navigate()
   - Multiple ways to handle following behavior

## Key Findings
1. The hunt action flow works up until NPC lookup:
   - Correct action data: `{"target":"Kaiden","type":"destroy"}`
   - NPC reference valid: `Oscar (type: table)`
2. The error suggests we're trying to call getAllNPCs() on something that's nil
3. The error occurs in a chat callback context, which might be relevant
4. We have working debug logs showing the action flow up to the error
5. Working actions use service instances passed in rather than global lookups

## Action Flow Analysis

### Confirmed Active (from logs)
1. Movement:
   ```
   [DEBUG] [MOVEMENT] Moving NPC Pete from (-37.6, 3.0, -118.5) to (-34.8, 3.0, -96.0)
   ```
   - MovementService.MoveTo() is definitely being called
   - NavigationService.CombatNavigate() exists in error logs

2. Chat/Interaction:
   ```
   [INFO] [CHAT] Chat request from Oscar to greggytheegg
   ```
   - Chat system is actively processing commands
   - Interaction detection working

### Needs Investigation
1. Patrol System:
   - Two implementations found:
     ```lua
     ActionService.patrol()
     ActionService.set_patrol()
     ```
   - Need to add distinct logging:
     ```lua
     LoggerService:debug("ACTION", "Legacy patrol() called")
     LoggerService:debug("ACTION", "New set_patrol() called")
     ```

2. Navigation:
   - Multiple entry points:
     ```lua
     ActionService.navigate()
     NavigationService.Navigate()
     ```
   - Add tracking:
     ```lua
     LoggerService:debug("ACTION", "ActionService.navigate called")
     LoggerService:debug("ACTION", "NavigationService.Navigate called")
     ```

3. Following Behavior:
   - Potential paths:
     - Through BehaviorService
     - Direct MovementService calls
     - Legacy follow action
   - Need to log each path uniquely

## Next Steps
1. Check why getAllNPCs() is being called in a TextChannel callback
2. Verify the service reference before calling getAllNPCs()
3. Add better error handling around NPC lookup
4. Add more debug logging for the hunt action flow
5. Clean up duplicate action flows
6. Standardize service access pattern based on working actions

## Next Steps for Flow Analysis
1. Add unique debug logging to each potential action path
2. Test each action type in-game:
   - patrol
   - follow
   - navigate
   - set_behavior
3. Review logs to identify:
   - Which paths are actually used
   - Which are legacy/deprecated
   - Where duplicates exist

## Questions to Answer
1. Why is NPC lookup happening in a TextChannel callback?
2. What should have the getAllNPCs() method?
3. Is the service reference being lost in the chat callback context?
4. Do we need to handle the chat callback differently?
5. Which of the duplicate flows are actually being used?
6. Should we deprecate set_behavior in favor of BehaviorService?
7. Are both patrol implementations needed or is one legacy?
8. Why do we have navigation in both services?
9. Is BehaviorService the new standard for state management?
10. Should we consolidate duplicate flows?

## Files Needed for Analysis

### Core Services
1. `games/sandbox-v2/src/shared/NPCSystem/services/ActionService.lua`
   - Contains action implementations
   - Source of current error
   - Seen in error logs: `ReplicatedStorage.Shared.NPCSystem.services.ActionService:532`

2. `games/sandbox-v2/src/shared/NPCSystem/services/NavigationService.lua`
   - Handles NPC movement
   - Contains CombatNavigate()
   - Seen in recent debug logs

3. `games/sandbox-v2/src/shared/NPCSystem/services/MovementService.lua`
   - Basic movement implementation
   - Actively logging movement: `[DEBUG] [MOVEMENT] Moving NPC Pete...`
   - Created per instance (seen in logs)

### Supporting Systems
4. `games/sandbox-v2/src/shared/NPCSystem/NPCManagerV3.lua`
   - Main NPC management
   - Seen in initialization logs
   - Version identified: "v3.1.0-clusters"

5. `games/sandbox-v2/src/shared/NPCSystem/chat/V4ChatClient.lua`
   - Processes chat commands
   - Seen in git status
   - Recently modified

Would you like me to verify any other files before we proceed with the analysis?

## Analysis Approach
1. Map all action flows across files
2. Add unique logging to each path
3. Test in-game to identify active flows
4. Review test files for intended usage
5. Document findings for each duplicate

## Expected Outcomes
1. Complete map of action flows
2. Identification of active vs legacy paths
3. Understanding of service relationships
4. Clear upgrade path for deprecated flows 