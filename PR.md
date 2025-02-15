# Fix NPC Hunting System

## Current Issue
When an NPC tries to hunt another NPC (e.g. "hunt for Kaiden"), we get an error:
```
attempt to index nil with 'getAllNPCs'
```

This occurs in ActionService.hunt() when trying to look up the target NPC.

## Investigation
- Looking at the logs, NPCs are being created and initialized correctly
- The error happens when ActionService tries to use NPCService:getAllNPCs()
- NPCService appears to be nil when called from ActionService

## Attempted Fix
Tried to:
1. Add NPCManager reference to ActionService
2. Initialize ActionService with NPCManager reference
3. Use NPCManager to look up target NPCs

This didn't work because:
- ActionService is a module that uses static methods
- Can't easily add state to the module without bigger refactoring

## Next Steps
Need to:
1. Investigate how NPCService is supposed to be initialized
2. Look at how other services access the NPC list
3. Consider refactoring ActionService to be instance-based if needed 