-- NPCDatabaseV2.lua
return {
	npcs = {
		{
			id = "oz",
			displayName = "Oz the Omniscient",
			model = "Oz", -- Make sure this matches exactly with the model name in ServerStorage.NPCModels
			responseRadius = 25,
			sightRange = 60,
			hearingRange = 40,
			spawnPosition = { 20, 5, 20 }, -- Changed position to avoid overlap with v1 NPCs
			system_prompt = "You are Oz the Omniscient, a mysterious and all-knowing entity. You speak in riddles and have knowledge of past, present, and future events.",
		},
		-- Add more v2 NPCs here as needed
	},
}
