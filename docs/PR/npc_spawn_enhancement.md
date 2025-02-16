# NPC Spawning System Enhancement - Dual Loading

## Current Implementation Analysis

1. **Model Loading Flow**
   - Models are loaded via ModelLoader service
   - Looks for models in ServerStorage/Assets/npcs/
   - Uses local .rbxm files with matching assetId names
   - No direct Toolbox loading currently

2. **Key Files**
   ```
   games/sandbox-v2/src/shared/NPCSystem/services/ModelLoader.lua
   games/sandbox-v2/src/data/NPCDatabase.lua
   ```

## Proposed Enhancement

Add dual-loading capability to ModelLoader:

```lua
-- ModelLoader.lua
local InsertService = game:GetService("InsertService")

function ModelLoader:loadModel(assetId)
    -- Try local file first
    local model = self:loadLocalModel(assetId)
    
    -- If local file not found, try Toolbox
    if not model then
        local success, toolboxModel = pcall(function()
            return InsertService:LoadAsset(assetId)
        end)
        
        if success and toolboxModel then
            model = toolboxModel:GetChildren()[1]
            -- Cache the model for future use
            if model then
                self:cacheModel(assetId, model:Clone())
            end
        end
    end
    
    return model
end
```

## Implementation Steps

1. **Update ModelLoader**
   - Add Toolbox loading support
   - Implement model caching
   - Add proper error handling
   - Keep local file fallback

2. **Update NPCManagerV3**
   - Use enhanced ModelLoader
   - Handle both loading methods
   - Add logging for load source

3. **Migration Plan**
   - Test with existing NPCs
   - Upload custom NPCs to Toolbox
   - Update assetIds in database
   - Keep local files as backup

## Benefits
1. Simpler asset management
2. Preserved textures/materials
3. Backward compatibility
4. Reduced repository size
5. Easier NPC creation

## Questions
1. Should we cache Toolbox models after first load?
2. Do we want to prioritize local or Toolbox loading?
3. Should we add asset version tracking?

## Next Steps
1. Locate ModelLoader.lua
2. Implement dual loading
3. Test with existing NPCs
4. Document new system 