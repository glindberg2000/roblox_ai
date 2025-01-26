import json
import pytest
from pathlib import Path
from app.snapshot_processor import (
    enrich_snapshot_with_context, 
    generate_health_context,
    generate_activity_context
)
from app.models import (
    GameSnapshot,
    HumanContextData,
    ClusterData
)
from unittest.mock import AsyncMock, patch
from app.cache import NPC_CACHE, AGENT_ID_CACHE
from app.status_manager import update_status_block
import time

def load_sample_snapshot():
    """Load sample snapshot from JSON file"""
    data_path = Path(__file__).parent / "data" / "sample_snapshot.json"
    with open(data_path) as f:
        return GameSnapshot(**json.load(f))

@pytest.fixture(autouse=True)
def setup_location_cache():
    """Initialize location cache for testing"""
    from app.cache import LOCATION_CACHE
    
    # Add multiple test locations
    LOCATION_CACHE.clear()
    LOCATION_CACHE.update({
        'chipotle': {
            'name': 'Chipotle',
            'coordinates': [8.0, 3.0, -12.0]  # Close to test position
        },
        'petes_stand': {
            'name': "Pete's Merch Stand",
            'coordinates': [-6.8, 3.0, -115.0]  # Where Pete usually is
        },
        'town_square': {
            'name': 'Town Square',
            'coordinates': [0.0, 3.0, 0.0]  # Center point
        }
    })
    yield
    LOCATION_CACHE.clear()

@pytest.fixture(autouse=True)
def cleanup_caches():
    """Clean up test entries from caches"""
    yield
    NPC_CACHE.clear()
    AGENT_ID_CACHE.clear()

def test_snapshot_enrichment():
    """Test snapshot enrichment with real data"""
    snapshot = load_sample_snapshot()
    enriched = enrich_snapshot_with_context(snapshot)
    
    # Test Diamond's enrichment specifically
    diamond = enriched.humanContext['Diamond']
    
    # 1. Test location enrichment
    assert diamond.location == 'Chipotle'  # Use dot notation
    
    # 2. Test narrative generation
    latest = diamond.recentInteractions[-1]  # Access model attributes
    assert 'at the entrance to Chipotle' in latest.narrative
    
    # 3. Test group data preservation
    group = diamond.currentGroups
    assert len(group.members) == 5
    assert all(m in group.members for m in ['Kaiden', 'Goldie', 'Oscar', 'Noobster', 'Diamond'])
    
    # 4. Test position data preservation
    assert abs(diamond.position.x - 7.87) < 0.01
    assert diamond.position.y == 3.0
    assert abs(diamond.position.z - (-12.006)) < 0.01

def calculate_distance(pos1, pos2):
    """Calculate 3D distance between two positions"""
    return ((pos1['x'] - pos2['x'])**2 + 
            (pos1['y'] - pos2['y'])**2 + 
            (pos1['z'] - pos2['z'])**2)**0.5

def test_location_narratives():
    """Test different location narrative cases based on distance thresholds"""
    chipotle_pos = {'x': 8.0, 'y': 3.0, 'z': -12.0}
    
    test_cases = [
        # Basic distance thresholds
        {
            'pos': {'x': 8.0, 'y': 3.0, 'z': -12.0},  # Distance = 0
            'expected': 'at the entrance to',
            'threshold': '<5'
        },
        {
            'pos': {'x': 18.0, 'y': 3.0, 'z': -12.0},  # Distance = 10
            'expected': 'right outside',
            'threshold': '<15'
        },
        {
            'pos': {'x': 28.0, 'y': 3.0, 'z': -12.0},  # Distance = 20
            'expected': 'near',
            'threshold': '<30'
        },
        {
            'pos': {'x': 48.0, 'y': 3.0, 'z': -12.0},  # Distance = 40
            'expected': 'in the vicinity of',
            'threshold': '<50'
        },
        # Edge cases
        {
            'pos': {'x': 13.0, 'y': 3.0, 'z': -12.0},  # Just inside 'right outside'
            'expected': 'right outside',
            'threshold': 'edge <15'
        },
        {
            'pos': {'x': 58.0, 'y': 3.0, 'z': -12.0},  # Beyond all thresholds
            'expected': 'at (',  # Should show coordinates
            'threshold': '≥50'
        },
        # Different Y levels
        {
            'pos': {'x': 8.0, 'y': 10.0, 'z': -12.0},  # Above but same x,z
            'expected': 'right outside',  # Y difference affects distance
            'threshold': 'vertical'
        },
        # Multiple locations nearby
        {
            'pos': {'x': 0.0, 'y': 3.0, 'z': 0.0},  # At Town Square
            'expected': 'at the entrance to Town Square',
            'threshold': 'multiple'
        }
    ]
    
    for case in test_cases:
        distance = calculate_distance(case['pos'], chipotle_pos)
        print(f"\nTesting position {case['pos']}")
        print(f"Distance to Chipotle: {distance:.1f}")
        print(f"Expected ({case['threshold']}): {case['expected']}")
        
        snapshot = GameSnapshot(
            timestamp=1234567890,
            events=[],
            clusters=[],
            humanContext={
                'TestNPC': {
                    'position': case['pos'],
                    'recentInteractions': [{'timestamp': 1234567890, 'narrative': ''}],
                    'currentGroups': {'members': [], 'npcs': 0, 'players': 0, 'formed': 1234567890},
                    'lastSeen': 1234567890,
                    'relationships': []
                }
            }
        )
        
        enriched = enrich_snapshot_with_context(snapshot)
        narrative = enriched.humanContext['TestNPC'].recentInteractions[-1].narrative  # Use dot notation
        print(f"Got: {narrative}")
        
        assert case['expected'] in narrative

def test_group_updates():
    """Test group membership changes and updates"""
    chipotle_pos = {'x': 8.0, 'y': 3.0, 'z': -12.0}
    
    test_cases = [
        {
            'name': 'single_join',
            'old_members': ['Diamond'],
            'new_members': ['Diamond', 'Pete'],
            'expected_update': 'Pete joined the group'
        },
        {
            'name': 'multiple_join',
            'old_members': ['Diamond'],
            'new_members': ['Diamond', 'Pete', 'Oscar'],
            'expected_update': 'Pete, Oscar joined the group'
        },
        {
            'name': 'single_leave',
            'old_members': ['Diamond', 'Pete'],
            'new_members': ['Diamond'],
            'expected_update': 'Pete left the group'
        },
        {
            'name': 'multiple_leave',
            'old_members': ['Diamond', 'Pete', 'Oscar'],
            'new_members': ['Diamond'],
            'expected_update': 'Pete, Oscar left the group'
        },
        {
            'name': 'simultaneous_join_leave',
            'old_members': ['Diamond', 'Pete'],
            'new_members': ['Diamond', 'Oscar'],
            'expected_updates': ['Pete left the group', 'Oscar joined the group']
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting {case['name']}")
        
        # Create snapshot with old group
        old_snapshot = GameSnapshot(
            timestamp=1234567890,
            events=[],
            clusters=[{
                'members': case['old_members'],
                'npcs': len(case['old_members']),
                'players': 0
            }],
            humanContext={
                'Diamond': {
                    'position': chipotle_pos,
                    'recentInteractions': [],
                    'currentGroups': {
                        'members': case['old_members'],
                        'npcs': len(case['old_members']),
                        'players': 0,
                        'formed': 1234567890
                    },
                    'lastSeen': 1234567890,
                    'relationships': []
                }
            }
        )
        
        # Create snapshot with new group
        new_snapshot = GameSnapshot(
            timestamp=1234567891,
            events=[],
            clusters=[{
                'members': case['new_members'],
                'npcs': len(case['new_members']),
                'players': 0
            }],
            humanContext={
                'Diamond': {
                    'position': chipotle_pos,
                    'recentInteractions': [],
                    'currentGroups': {
                        'members': case['new_members'],
                        'npcs': len(case['new_members']),
                        'players': 0,
                        'formed': 1234567890
                    },
                    'lastSeen': 1234567891,
                    'relationships': []
                }
            }
        )
        
        # Process both snapshots
        enriched_old = enrich_snapshot_with_context(old_snapshot)
        enriched_new = enrich_snapshot_with_context(new_snapshot)
        
        # Check group updates
        diamond_context = enriched_new.humanContext['Diamond']
        group = diamond_context.currentGroups
        
        print(f"Old members: {case['old_members']}")
        print(f"New members: {case['new_members']}")
        print(f"Updates: {group.updates}")
        
        # Verify group state
        assert set(group.members) == set(case['new_members'])
        
        # Verify updates
        if 'expected_update' in case:
            assert case['expected_update'] in group.updates[0]
        else:
            for expected in case['expected_updates']:
                assert any(expected in update for update in group.updates)

def test_health_updates():
    """Test health status changes and narratives"""
    test_cases = [
        # Basic damage cases
        {
            'name': 'severe_damage',
            'old_health': {'current': 100, 'max': 100, 'state': 'Running'},
            'new_health': {'current': 70, 'max': 100, 'state': 'Running'},
            'expected': 'Took severe damage (-30)'
        },
        {
            'name': 'minor_damage',
            'old_health': {'current': 100, 'max': 100, 'state': 'Running'},
            'new_health': {'current': 90, 'max': 100, 'state': 'Running'},
            'expected': 'Took minor damage'
        },
        # Death states
        {
            'name': 'death_from_damage',
            'old_health': {'current': 30, 'max': 100, 'state': 'Running'},
            'new_health': {'current': 0, 'max': 100, 'state': 'Dead'},
            'expected': ['Took fatal damage', 'Died']
        },
        {
            'name': 'unusual_death',
            'old_health': {'current': 100, 'max': 100, 'state': 'Running'},
            'new_health': {'current': 0, 'max': 0, 'state': 'Dead'},
            'expected': ['In an unusual health state', 'Died']
        },
        # Recovery cases
        {
            'name': 'significant_healing',
            'old_health': {'current': 50, 'max': 100, 'state': 'Running'},
            'new_health': {'current': 80, 'max': 100, 'state': 'Running'},
            'expected': 'Recovered significantly (+30)'
        },
        {
            'name': 'resurrection',
            'old_health': {'current': 0, 'max': 100, 'state': 'Dead'},
            'new_health': {'current': 100, 'max': 100, 'state': 'Running'},
            'expected': ['Resurrected', 'Recovered significantly (+100)']
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting {case['name']}")
        narrative = generate_health_context(case['old_health'], case['new_health'])
        print(f"Got: {narrative}")
        
        if isinstance(case['expected'], list):
            for expected in case['expected']:
                assert expected in narrative
        else:
            assert case['expected'] in narrative

def test_activity_updates():
    """Test activity state changes and narratives"""
    test_cases = [
        # Movement states
        {
            'name': 'start_running',
            'old_state': {'health': {'state': 'Idle', 'isMoving': False}},
            'new_state': {'health': {'state': 'Running', 'isMoving': True}},
            'velocity': [1.0, 0.0, 1.0],
            'expected': 'Running'
        },
        {
            'name': 'fake_running',
            'old_state': {'health': {'state': 'Running', 'isMoving': True}},
            'new_state': {'health': {'state': 'Running', 'isMoving': False}},
            'velocity': [0.0, 0.0, 0.0],
            'expected': 'Standing'
        },
        # Emote states
        {
            'name': 'start_emoting',
            'old_state': {'health': {'state': 'Running', 'isMoving': True}},
            'new_state': {'health': {'state': 'Emoting', 'isMoving': False}},
            'velocity': [0.0, 0.0, 0.0],
            'expected': 'Performing emote'
        },
        {
            'name': 'wave_emote',
            'old_state': {'health': {'state': 'Idle', 'isMoving': False}},
            'new_state': {
                'health': {'state': 'Emoting', 'isMoving': False},
                'emote': {'name': 'Wave', 'target': 'Pete'}
            },
            'velocity': [0.0, 0.0, 0.0],
            'expected': 'Waving at Pete'
        },
        # Special states
        {
            'name': 'jumping',
            'old_state': {'health': {'state': 'Running', 'isMoving': True}},
            'new_state': {'health': {'state': 'Jumping', 'isMoving': True}},
            'velocity': [1.0, 2.0, 1.0],
            'expected': 'Just jumped'
        },
        {
            'name': 'dancing',
            'old_state': {'health': {'state': 'Idle', 'isMoving': False}},
            'new_state': {
                'health': {'state': 'Emoting', 'isMoving': False},
                'emote': {'name': 'Dance', 'style': 'Hip Hop'}
            },
            'velocity': [0.0, 0.0, 0.0],
            'expected': 'Dancing Hip Hop style'
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting {case['name']}")
        narrative = generate_activity_context(case['old_state'], case['new_state'])
        print(f"Got: {narrative}")
        assert case['expected'] in narrative

def test_group_member_states():
    """Test state tracking for group members"""
    chipotle_pos = {'x': 8.0, 'y': 3.0, 'z': -12.0}
    
    test_cases = [
        {
            'name': 'member_takes_damage',
            'members': ['Diamond', 'Pete'],
            'updates': {
                'Pete': {
                    'old_health': {'current': 100, 'max': 100, 'state': 'Running'},
                    'new_health': {'current': 70, 'max': 100, 'state': 'Running'}
                }
            },
            'expected': 'Pete took severe damage'
        },
        {
            'name': 'member_emotes',
            'members': ['Diamond', 'Pete', 'Oscar'],
            'updates': {
                'Oscar': {
                    'old_state': {'health': {'state': 'Idle'}},
                    'new_state': {
                        'health': {'state': 'Emoting'},
                        'emote': {'name': 'Wave', 'target': 'Pete'}
                    }
                }
            },
            'expected': 'Oscar is waving at Pete'
        },
        {
            'name': 'multiple_member_updates',
            'members': ['Diamond', 'Pete', 'Oscar'],
            'updates': {
                'Pete': {
                    'old_health': {'current': 100, 'max': 100},
                    'new_health': {'current': 80, 'max': 100}
                },
                'Oscar': {
                    'old_state': {'health': {'state': 'Idle'}},
                    'new_state': {'health': {'state': 'Dancing'}}
                }
            },
            'expected': ['Pete took damage', 'Oscar started dancing']
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting {case['name']}")
        # Create and process snapshots...

@pytest.mark.asyncio
async def test_status_and_group_updates():
    """Test status block updates and group member handling"""
    npc_id = "test_npc"
    agent_id = "test_agent"
    current_time = int(time.time())  # Integer timestamp
    
    # Mock cache entries
    NPC_CACHE[npc_id] = {"id": npc_id}
    AGENT_ID_CACHE[npc_id] = agent_id
    
    # Create test snapshot with health, location, group
    snapshot = GameSnapshot(
        timestamp=current_time,  # Required field
        events=[],              # Required field
        clusters=[],            # Required field
        humanContext={
            npc_id: HumanContextData(
                health={"current": 50, "max": 100},
                location="Town Square",
                currentGroups={
                    "members": ["player1", "player2"],
                    "npcs": 0,
                    "players": 2,
                    "formed": current_time  # Use integer timestamp
                },
                currentActivity="Standing",
                lastSeen=current_time,  # Use integer timestamp
                recentInteractions=[],
                relationships=[]
            )
        }
    )
    
    # Mock the client calls - update patch paths
    with patch('app.status_manager.update_location_status', new_callable=AsyncMock) as mock_status_update, \
         patch('app.status_manager.update_group_members_v2', new_callable=AsyncMock) as mock_group_update:
        
        # Process snapshot
        enriched = enrich_snapshot_with_context(snapshot)
        await update_status_block(npc_id, enriched.humanContext[npc_id], enriched)
        
        # Verify status update was called with correct data
        mock_status_update.assert_called_once()
        status_call = mock_status_update.call_args[1]
        assert status_call['current_location'] == "Town Square"
        assert "Status: Injured" in status_call['current_action']
        assert "Group: With 2 others" in status_call['current_action']
        
        # Verify group update was called with correct members
        mock_group_update.assert_called_once()
        group_call = mock_group_update.call_args[1]
        assert len(group_call['nearby_players']) == 2
        assert all(p['id'] in ['player1', 'player2'] for p in group_call['nearby_players'])

@pytest.mark.asyncio
async def test_status_updates_with_missing_data():
    """Test status updates with partial or missing data"""
    npc_id = "test_npc"
    agent_id = "test_agent"
    
    # Mock cache entries
    NPC_CACHE[npc_id] = {"id": npc_id}
    AGENT_ID_CACHE[npc_id] = agent_id
    
    test_cases = [
        {
            'name': 'missing_health',
            'context': HumanContextData(
                location="Town Square",
                currentGroups={"members": [], "npcs": 0, "players": 0, "formed": int(time.time())},
                lastSeen=int(time.time()),
                recentInteractions=[],
                relationships=[]
            ),
            'expected_updates': ["Location: Town Square", "Group: Alone"]
        },
        {
            'name': 'partial_group_data',
            'context': HumanContextData(
                location="Town Square",
                health={"current": 50, "max": 100},
                currentGroups={"members": ["invalid_player"], "npcs": 0, "players": 1, "formed": int(time.time())},
                lastSeen=int(time.time()),
                recentInteractions=[],
                relationships=[]
            ),
            'expected_updates': ["Location: Town Square", "Status: Injured", "Group: Alone"]
        },
        {
            'name': 'minimal_data',
            'context': HumanContextData(
                location="Unknown",
                currentGroups={"members": [], "npcs": 0, "players": 0, "formed": int(time.time())},
                lastSeen=int(time.time()),
                recentInteractions=[],
                relationships=[]
            ),
            'expected_updates': ["Location: Unknown", "Group: Alone"]
        }
    ]
    
    current_time = int(time.time())
    
    for case in test_cases:
        print(f"\nTesting {case['name']}")
        
        snapshot = GameSnapshot(
            timestamp=current_time,
            events=[],
            clusters=[],
            humanContext={npc_id: case['context']}
        )
        
        with patch('app.status_manager.update_location_status', new_callable=AsyncMock) as mock_status_update:
            await update_status_block(npc_id, case['context'], snapshot)
            
            # Verify status update was called with expected data
            mock_status_update.assert_called_once()
            status_call = mock_status_update.call_args[1]
            
            # Check that all expected updates are in the status text
            status_text = status_call['current_action']
            for expected in case['expected_updates']:
                assert expected in status_text, f"Missing {expected} in status: {status_text}"

if __name__ == "__main__":
    # Run test directly
    test_snapshot_enrichment() 