return {
    -- Template NPC structure:
    --[[
    {
        id = "unique_npc_id",
        displayName = "NPC Display Name",
        model = "model_name",  -- Matches the .rbxm file name
        responseRadius = 20,
        assetId = "asset_id_here",
        spawnPosition = Vector3.new(0, 5, 0),
        system_prompt = [[NPC's personality and behavior description]],
        abilities = {
            "ability1",
            "ability2"
        },
        shortTermMemory = {},
    }
    --]]
}