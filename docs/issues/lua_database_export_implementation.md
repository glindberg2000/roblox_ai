# Lua Database Export Implementation Plan

## Confirmed Requirements

1. Field Mappings:
   - modelName = displayName (for chat system dual display)
   - model = assetId (for model loading)
   - name = displayName (for consistency)
   - abilities = from abilityConfig.js (admin selectable)
   - shortTermMemory = {} (empty placeholder)

2. Vector3 Format:
   - Input: Can be stored in any efficient format
   - Output: Must be `Vector3.new(x, y, z)`
   - No schema changes needed, just formatting

3. Abilities:
   - Source: abilityConfig.js defines available abilities
   - Selection: Admin UI checkboxes
   - Storage: Array/JSON in database
   - Output: Lua table format

## Implementation Steps

1. Update utils.py with new formatters:

```python:api/app/utils.py
def format_vector3_lua(pos_data):
    """Convert position data to Lua Vector3 string"""
    pos = json.loads(pos_data) if isinstance(pos_data, str) else pos_data
    return f"Vector3.new({pos['x']}, {pos['y']}, {pos['z']})"

def format_npc_as_lua(npc):
    """Format single NPC as Lua table entry"""
    abilities = json.loads(npc['abilities']) if isinstance(npc['abilities'], str) else npc['abilities']
    abilities_lua = "\n                ".join(f'"{ability}",' for ability in abilities)
    
    return f"""        {{
            id = "{npc['npc_id']}",
            displayName = "{npc['display_name']}",
            name = "{npc['display_name']}",  -- Same as displayName
            assetId = "{npc['asset_id']}",
            model = "{npc['asset_id']}",     -- Same as assetId
            modelName = "{npc['display_name']}", -- Same as displayName
            system_prompt = "{npc['system_prompt']}", 
            responseRadius = {npc['response_radius']},
            spawnPosition = {format_vector3_lua(npc['spawn_position'])},
            abilities = {{
                {abilities_lua}
            }},
            shortTermMemory = {{}}
        }},"""
```

2. Update database.py to use new formatter:

```python:api/app/database.py
def generate_lua_from_db(game_slug: str, db_type: str) -> None:
    """Generate Lua file from database for specific game"""
    with get_db() as db:
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
        
        game_id = game['id']
        db_paths = get_database_paths(game_slug)
        
        if db_type == 'npc':
            # Get NPCs with all required fields
            cursor = db.execute("""
                SELECT npc_id, display_name, asset_id, system_prompt,
                       response_radius, spawn_position, abilities
                FROM npcs 
                WHERE game_id = ?
                ORDER BY display_name
            """, (game_id,))
            npcs = cursor.fetchall()
            
            # Generate Lua content
            lua_content = "return {\n    npcs = {\n"
            for npc in npcs:
                lua_content += format_npc_as_lua(dict(npc))
            lua_content += "\n    }\n}"
            
            # Save to file
            with open(db_paths['npc']['lua'], 'w') as f:
                f.write(lua_content)
```

3. Clean up redundant code:
- Remove save_json_database() from utils.py
- Remove load_json_database() from utils.py
- Consolidate Lua generation in utils.py

## Frontend Updates Needed

1. Update ability selection in dashboard:
```javascript:api/static/js/dashboard/npc.js
function setupAbilitySelectors() {
    const abilityContainer = document.getElementById('abilitySelectors');
    ABILITY_CONFIG.forEach(ability => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = ability.id;
        checkbox.name = 'abilities';
        checkbox.value = ability.id;
        
        const label = document.createElement('label');
        label.htmlFor = ability.id;
        label.innerHTML = `<i class="${ability.icon}"></i> ${ability.name}`;
        
        abilityContainer.appendChild(checkbox);
        abilityContainer.appendChild(label);
    });
}
```

## Testing Plan

1. Verify Lua Output:
   - Check Vector3 formatting
   - Verify all required fields present
   - Validate abilities format
   - Test with various input data

2. Test Cases:
   - NPCs with no abilities
   - Special characters in names/prompts
   - Different position formats
   - Missing optional fields

## Migration Notes

1. No database schema changes required
2. Existing data remains unchanged
3. Only export format is modified
4. No migration scripts needed

## Questions Resolved
- ✓ modelName mapping
- ✓ abilities source
- ✓ Vector3 storage
- ✓ shortTermMemory handling
- ✓ existing data compatibility

## Next Steps
1. Implement new formatters in utils.py
2. Update database.py export function
3. Remove redundant code
4. Add frontend ability selection
5. Test with sample data
6. Document new format 