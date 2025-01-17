# Group Memory System Design

## Overview
Design document for implementing long-term group memory and individual interaction tracking for NPCs.

## Current Implementation
NPCs currently have status blocks showing immediate state:
```json
{
    "status": {
        "region": "Town Square",
        "location": "Main Plaza",
        "current_action": "chatting",
        "nearby_people": ["Kaiden", "greggytheegg", "Goldie"]
    }
}
```

## Design Options

### Option 1: Individual Memory Blocks
Memory is managed as separate blocks per participant:
```json
{
    "human_blocks": {
        "Kaiden": {
            "first_met": 1736040980,
            "interactions": [],
            "notes": "Likes to hang out at shooting range"
        },
        "greggytheegg": {
            "first_met": 1736040985,
            "interactions": [],
            "notes": "New player, seems friendly"
        }
    }
}
```

### Option 2: Master Group Memory (Recommended)
Single coherent memory structure:
```json
{
    "group_memory": {
        "current_participants": ["Kaiden", "greggytheegg", "Goldie"],
        "journal": [
            {
                "timestamp": 1736040980,
                "type": "group_formed",
                "participants": ["Kaiden", "Goldie"]
            },
            {
                "timestamp": 1736040985,
                "type": "member_joined",
                "participant": "greggytheegg",
                "context": "Approached the group at Main Plaza"
            }
        ],
        "participant_notes": {
            "active": {
                "Kaiden": { "notes": "..." },
                "greggytheegg": { "notes": "..." }
            },
            "archived": {}
        }
    }
}
```

## Technical Considerations

### Database Options
Current: SQLite
- Simple, file-based
- Good for development
- Limited concurrent access

Proposed: PostgreSQL
- Better concurrent access
- Native JSON support
- Better scaling for archived data
- More complex setup/maintenance

### Memory Management Strategies
1. Active Memory:
   - Keep current group state in memory
   - Maintain fixed-size recent history
   - Track active participant notes

2. Archived Memory:
   - Store in database
   - Compress older interactions
   - Index by participant and timestamp

### Update Mechanics
1. Hot-swapping participants:
```python
async def swap_participants(group_id, joining, leaving):
    async with db.transaction():
        # Archive leaving participants
        await archive_participants(group_id, leaving)
        # Load joining participants
        await load_participants(group_id, joining)
        # Update active memory
        await update_group_memory(group_id)
```

2. Memory Compression:
   - Archive entries older than X days
   - Summarize repeated interactions
   - Maintain important markers/milestones

## Open Questions
1. Memory Limits
   - How much history to keep in active memory?
   - When to compress/archive?
   - How to handle memory pressure?

2. Update Frequency
   - How often to sync with database?
   - When to trigger hot-swaps?
   - How to handle rapid group changes?

3. Data Structure
   - Fixed vs dynamic memory blocks?
   - How to structure archived data?
   - What indexes needed for efficient retrieval?

## Next Steps
1. Prototype basic memory structure
2. Test with current SQLite
3. Evaluate PostgreSQL migration need
4. Implement basic hot-swapping
5. Add compression/archival system

## Notes
- Keep memory structure simple initially
- Focus on efficient hot-swapping
- Consider read vs write optimization
- Plan for future scaling

## Performance Considerations
1. Memory Size:
   - Each NPC needs their own group memory
   - Active participants' notes stay in memory
   - Estimate ~10KB per participant
   - 100 NPCs × 10 participants = ~1MB active memory

2. Database Load:
   - Hot-swaps trigger DB reads/writes
   - Peak times: player join/leave events
   - Batch updates when possible

## Integration Points
1. Letta API:
   - Group memory included in context
   - NPCs can reference past interactions
   - Memory updates via system messages

2. Roblox Client:
   - Proximity triggers group changes
   - Movement system affects group formation
   - Chat system references group context

## Risks
1. Memory Growth:
   - Large player counts could bloat memory
   - Need clear archival criteria
   - Monitor memory usage patterns

2. Performance:
   - DB bottlenecks during peak times
   - Memory fragmentation over time
   - Complex query patterns