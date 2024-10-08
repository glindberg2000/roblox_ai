-- NPCDatabase.lua

return {
	npcs = {
		{
			id = "eldrin",
			displayName = "Eldrin the Wise",
			model = "Eldrin",
			responseRadius = 20,
			sightRange = 50,
			hearingRange = 30,
			spawnPosition = { 0, 5, 0 },
			backstory = "Eldrin is an ancient wizard with vast knowledge of the arcane arts.",
			traits = { "wise", "patient", "magical" },
			system_prompt = "You are Eldrin the Wise, a centuries-old wizard who resides in the enchanted forest of Eldoria.",
			routines = {
				{ type = "wander", area = { -10, 10, -10, 10, 0, 0 }, duration = 300 },
				{ type = "idle", duration = 60 },
			},
		},
		{
			id = "luna",
			displayName = "Luna the Stargazer",
			model = "Luna",
			responseRadius = 15,
			sightRange = 40,
			hearingRange = 25,
			spawnPosition = { 10, 5, 10 },
			backstory = "Luna is a young astronomer fascinated by the celestial bodies.",
			traits = { "curious", "intelligent", "dreamy" },
			system_prompt = "You are Luna the Stargazer, a mystical astronomer who lives in the Celestial Tower.",
			routines = {
				{ type = "observe", target = "sky", duration = 180 },
				{ type = "wander", area = { 5, 15, 5, 15, 5, 5 }, duration = 120 },
			},
		},
	},
}
