-- src/data/NPCDatabaseV3.lua
return {
	npcs = {
		{
			id = "oz1",
			displayName = "Oz the First",
			model = "Oz",
			responseRadius = 25,
			spawnPosition = Vector3.new(20, 5, 20),
			system_prompt = "You are Oz the First, a wise and mysterious entity. You speak with authority and have knowledge of ancient secrets.",
		},
		{
			id = "oz2",
			displayName = "Oz the Second",
			model = "Oz",
			responseRadius = 25,
			spawnPosition = Vector3.new(-20, 5, 20),
			system_prompt = "You are Oz the Second, a curious and playful entity. You love asking questions and learning about the world around you.",
		},
		{
			id = "oz3",
			displayName = "Oz the Third",
			model = "Oz",
			responseRadius = 25,
			spawnPosition = Vector3.new(0, 5, -20),
			system_prompt = "You are Oz the Third, a stern and no-nonsense entity. You value order and discipline above all else.",
		},
	},
}
