# Group Status Caching System

## Overview
This document outlines the caching and update strategy for NPC group status management, optimizing performance while maintaining data consistency.

## Architecture

### Cache Structures

1. Boot-time Static Cache
```python
STATIC_CACHE = {
    'npc_descriptions': {
        'npc_id': {
            'name': str,
            'description': str,
            'display_name': str
        }
    },
    'locations': {
        'slug': {
            'coordinates': [x, y, z],
            'name': str,
            'description': str
        }
    }
}
```

2. Runtime Player Cache
```python
PLAYER_CACHE = {
    'player_id': {
        'description': str,
        'last_seen': timestamp,
        'name': str
    }
}
```

3. NPC Group State Cache
```python
NPC_GROUPS = {
    'npc_id': {
        'current_cluster': list[str],  # Member names
        'last_updated': timestamp,
        'last_force_refresh': timestamp,
        'current_location': str,
        'current_action': str
    }
}
```

## Update Logic

### Constants
```python
FORCE_REFRESH_INTERVAL = 300  # 5 minutes
STALE_DATA_THRESHOLD = 30     # 30 seconds
PLAYER_CACHE_TTL = 3600      # 1 hour
```

### Update Decision Flow
```python
def should_update_group(npc_id: str, new_cluster: list, new_location: str) -> bool:
    group_state = NPC_GROUPS.get(npc_id)
    now = time.time()
    
    # Force refresh cases
    if (
        not group_state or  # No cached state
        now - group_state['last_force_refresh'] > FORCE_REFRESH_INTERVAL or
        now - group_state['last_updated'] > STALE_DATA_THRESHOLD
    ):
        return True
        
    # State change cases
    return (
        set(group_state['current_cluster']) != set(new_cluster) or
        group_state['current_location'] != new_location
    )
```

## Integration with Letta Templates

### Group Status Updates
```python
def process_group_update(npc_id: str, snapshot_data: dict):
    if not should_update_group(npc_id, snapshot_data['cluster'], snapshot_data['location']):
        return
        
    nearby_players = [
        {
            'id': player_id,
            'name': PLAYER_CACHE[player_id]['name'],
            'appearance': PLAYER_CACHE[player_id]['description'],
            'notes': ''  # Optional: Could track interaction history
        }
        for player_id in snapshot_data['nearby_players']
    ]
    
    update_group_status(
        client=direct_client,
        agent_id=get_agent_id(npc_id),
        nearby_players=nearby_players,
        current_location=snapshot_data['location'],
        current_action=snapshot_data['action']
    )
    
    # Update cache
    NPC_GROUPS[npc_id] = {
        'current_cluster': snapshot_data['cluster'],
        'last_updated': time.time(),
        'last_force_refresh': time.time(),
        'current_location': snapshot_data['location'],
        'current_action': snapshot_data['action']
    }
```

## Cache Management

### Initialization
```python
def initialize_caches():
    """Load static data on server boot"""
    # Load NPC data
    npcs = get_all_npcs()
    STATIC_CACHE['npc_descriptions'] = {
        npc.id: {
            'name': npc.name,
            'description': npc.description,
            'display_name': npc.display_name
        }
        for npc in npcs
    }
    
    # Load location data
    locations = get_all_locations()
    STATIC_CACHE['locations'] = {
        loc.slug: {
            'coordinates': loc.coordinates,
            'name': loc.name,
            'description': loc.description
        }
        for loc in locations
    }
```

### Player Cache Management
```python
def update_player_cache(player_id: str, player_data: dict):
    """Update player cache when new player data received"""
    PLAYER_CACHE[player_id] = {
        'description': player_data['description'],
        'last_seen': time.time(),
        'name': player_data['name']
    }

def cleanup_player_cache():
    """Remove stale player data"""
    now = time.time()
    stale_players = [
        pid for pid, data in PLAYER_CACHE.items()
        if now - data['last_seen'] > PLAYER_CACHE_TTL
    ]
    for pid in stale_players:
        del PLAYER_CACHE[pid]
```

## Error Handling

### Recovery Procedures
1. Cache corruption detection
2. Force refresh triggers
3. Inconsistency resolution

```python
def verify_cache_consistency():
    """Periodic cache verification"""
    for npc_id, state in NPC_GROUPS.items():
        if cache_needs_refresh(npc_id):
            force_refresh_npc_state(npc_id)

def force_refresh_npc_state(npc_id: str):
    """Force refresh NPC state from current game state"""
    current_state = get_current_game_state(npc_id)
    process_group_update(npc_id, current_state, force=True)
```

## Performance Considerations

### Resource Usage
- Memory: ~100KB per NPC for state tracking
- CPU: Minimal comparison operations per update
- Network: Letta API calls only on actual state changes

### Expected Load
- Snapshot frequency: Every 3 seconds
- Average update rate: ~20% of snapshots requiring updates
- Force refresh: Every 5 minutes per NPC

## Monitoring

### Key Metrics
1. Cache hit rate
2. Update frequency
3. Force refresh rate
4. Error rates

## Future Improvements

### Potential Enhancements
1. Distributed cache support
2. More sophisticated staleness detection
3. Predictive updates
4. Enhanced error recovery

## Implementation Phases

### Phase 1: Basic Implementation
- Static cache setup
- Basic group tracking
- Simple refresh logic

### Phase 2: Enhanced Features
- Advanced staleness detection
- Monitoring implementation
- Error recovery procedures

### Phase 3: Optimizations
- Performance tuning
- Advanced caching strategies
- Distributed support 

## Memory Block Synchronization

### Challenges
1. NPCs can update their own memory blocks via tools
2. Direct memory updates during gameplay need to be preserved
3. Risk of overwriting NPC-initiated changes during group updates

### Proposed Solutions

1. Pre-Update Check
```python
def process_group_update(npc_id: str, snapshot_data: dict):
    # Check for pending NPC-initiated updates
    current_memory = get_agent_memory(npc_id)
    if has_pending_changes(current_memory):
        # Option 1: Merge changes
        merged_state = merge_memory_states(current_memory, snapshot_data)
        # Option 2: Write back changes before update
        write_back_changes(current_memory)
        
    # Proceed with group update...
```

2. Hybrid Approach Options:
- Keep NPC tools writing directly to memory during gameplay
- Use DB only for persistence/recovery
- Implement memory diffing to detect conflicts
- Consider versioning or timestamps for change tracking

### Considerations
- Performance impact of pre-update checks
- Complexity of merge strategies
- Maintaining gameplay responsiveness
- Data consistency vs real-time updates 

## Implementation Roadmap

### Phase 0: Direct Integration (No Caching)
1. Basic Group Updates
```python
# Step 1: Add direct group updates to snapshot processing
def process_snapshot(snapshot_data):
    for npc_id, cluster in snapshot_data['clusters'].items():
        nearby_players = [
            {
                'id': p_id,
                'name': p_name,
                'appearance': get_player_description(p_id),  # Direct DB call
                'notes': ''
            }
            for p_id, p_name in snapshot_data['nearby_players']
        ]
        
        update_group_status(
            client=direct_client,
            agent_id=get_agent_id(npc_id),
            nearby_players=nearby_players,
            current_location=get_npc_location(npc_id),  # Direct location lookup
            current_action="idle"  # Default for testing
        )
```

2. Testing Milestones
- [ ] Verify group updates appear in NPC memory
- [ ] Confirm player descriptions are included
- [ ] Test with multiple NPCs in same area
- [ ] Monitor API call frequency and performance

### Phase 1: Basic Filtering
1. Add Update Filtering
```python
def should_update(npc_id: str, new_cluster: list) -> bool:
    # Simple comparison with last known state
    last_state = get_last_known_state(npc_id)  # In-memory only
    return last_state['cluster'] != new_cluster

def process_snapshot(snapshot_data):
    for npc_id, cluster in snapshot_data['clusters'].items():
        if should_update(npc_id, cluster):
            # Proceed with update...
```

2. Testing Milestones
- [ ] Verify reduced update frequency
- [ ] Confirm no loss of important state changes
- [ ] Test cluster change detection
- [ ] Monitor memory usage

### Phase 2: Cache Implementation
1. Add Static Caches
```python
# Step 1: Initialize boot-time caches
def init_caches():
    load_npc_descriptions()
    load_location_data()

# Step 2: Add player cache
def update_player_cache(player_id: str, description: str):
    PLAYER_CACHE[player_id] = {
        'description': description,
        'last_seen': time.time()
    }
```

2. Testing Milestones
- [ ] Verify cache initialization on boot
- [ ] Test player cache updates
- [ ] Monitor memory usage
- [ ] Verify reduced DB calls

### Phase 3: Memory Block Sync
1. Add Change Detection
```python
# Step 1: Implement change detection
def check_memory_changes(npc_id: str) -> bool:
    current = get_agent_memory(npc_id)
    last_known = get_last_snapshot(npc_id)
    return detect_changes(current, last_known)

# Step 2: Add to update flow
def process_snapshot(snapshot_data):
    for npc_id, cluster in snapshot_data['clusters'].items():
        if check_memory_changes(npc_id):
            # Handle pending changes before update
```

2. Testing Milestones
- [ ] Test NPC tool updates during gameplay
- [ ] Verify no lost updates
- [ ] Monitor performance impact
- [ ] Test conflict resolution

### Phase 4: Monitoring & Optimization
1. Add Metrics
```python
def track_metrics():
    return {
        'updates_processed': METRICS['updates'],
        'cache_hits': METRICS['cache_hits'],
        'api_calls': METRICS['api_calls'],
        'errors': METRICS['errors']
    }
```

2. Testing Milestones
- [ ] Monitor update frequencies
- [ ] Track cache effectiveness
- [ ] Measure API call reduction
- [ ] Identify optimization opportunities 