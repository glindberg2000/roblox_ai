Updated Design for Programmatically Applying Animations and Scripts to NPCs

Here’s a logical plan to enhance your system to programmatically add animations and scripts to NPCs, based on the requirements you’ve outlined:

1. Where to Store the Animation Scripts

	•	Folder Location: Add a new folder in ServerStorage to store reusable scripts and animation data. For example:

/src/assets/scripts
├── AnimateScript.server.lua
├── WalkScript.server.lua
└── EmoteScript.server.lua

This folder will store Lua scripts for animations and behaviors, ensuring you can dynamically apply them to NPCs when they’re loaded.
Update the project configuration to include this folder:

"ServerStorage": {
  "Assets": {
    "scripts": {
      "$path": "src/assets/scripts"
    }
  }
}

2. Creating Sample Scripts

Here are sample scripts for common NPC behaviors:

Animate Script

This script will handle animations like walking, running, and jumping. Save it as AnimateScript.server.lua:

-- AnimateScript.server.lua
local AnimateScript = {}

function AnimateScript.applyTo(npcModel)
    local humanoid = npcModel:FindFirstChildOfClass("Humanoid")
    if not humanoid then
        warn("No Humanoid found in model:", npcModel.Name)
        return
    end

    -- Attach an Animator if not present
    local animator = humanoid:FindFirstChildOfClass("Animator") or Instance.new("Animator", humanoid)

    -- Add animations (these IDs must be your actual animation assets)
    local animations = {
        walk = "rbxassetid://12345678",  -- Replace with your walk animation asset ID
        run = "rbxassetid://87654321",  -- Replace with your run animation asset ID
    }

    -- Create Animation objects for each animation
    for animName, assetId in pairs(animations) do
        local anim = Instance.new("Animation")
        anim.Name = animName
        anim.AnimationId = assetId
        anim.Parent = npcModel

        local track = animator:LoadAnimation(anim)
        npcModel:SetAttribute(animName .. "Track", track)
    end

    print("Animations applied to:", npcModel.Name)
end

return AnimateScript

Walk Script

A simple script to make NPCs walk to random points. Save it as WalkScript.server.lua:

-- WalkScript.server.lua
local WalkScript = {}

function WalkScript.walkToRandomPoint(npc)
    local humanoid = npc:FindFirstChildOfClass("Humanoid")
    if not humanoid then return end

    local currentPosition = npc.PrimaryPart.Position
    local randomOffset = Vector3.new(math.random(-20, 20), 0, math.random(-20, 20))
    local targetPosition = currentPosition + randomOffset

    humanoid:MoveTo(targetPosition)
    print(npc.Name .. " is walking to:", targetPosition)
end

return WalkScript

3. Programmatically Apply Scripts to NPCs

In your NPC creation logic, dynamically attach these scripts when an NPC is spawned.

Update NPCManagerV3.lua:

local ServerStorage = game:GetService("ServerStorage")
local AnimateScript = require(ServerStorage.Assets.scripts.AnimateScript)
local WalkScript = require(ServerStorage.Assets.scripts.WalkScript)

function NPCManagerV3:createNPC(npcData)
    print("Creating NPC:", npcData.displayName)
    if not workspace:FindFirstChild("NPCs") then
        Instance.new("Folder", workspace).Name = "NPCs"
    end

    local model = ServerStorage.Assets.npcs:FindFirstChild(npcData.model)
    if not model then
        warn("Model not found for NPC:", npcData.displayName)
        return
    end

    local npcModel = model:Clone()
    npcModel.Name = npcData.displayName
    npcModel.Parent = workspace.NPCs

    -- Ensure the model has a PrimaryPart
    npcModel.PrimaryPart = npcModel:FindFirstChild("HumanoidRootPart")

    -- Apply animations and behaviors
    AnimateScript.applyTo(npcModel)

    local npc = {
        model = npcModel,
        id = npcData.id,
        displayName = npcData.displayName,
        responseRadius = npcData.responseRadius,
        shortTermMemory = {},
    }

    -- Schedule random walking behavior
    task.spawn(function()
        while true do
            WalkScript.walkToRandomPoint(npcModel)
            task.wait(math.random(5, 10))  -- Random delay between walks
        end
    end)

    self.npcs[npc.id] = npc
    print("NPC added:", npc.displayName, "Total NPCs:", self:getNPCCount())
end

4. Testing Scripts

To confirm the scripts are working as intended, add a debug function to NPCManagerV3.lua:

function NPCManagerV3:testNPCBehaviors()
    for _, npc in pairs(self.npcs) do
        print("Testing behaviors for:", npc.displayName)
        WalkScript.walkToRandomPoint(npc.model)
    end
end

Call this function manually in MainNPCScript.server.lua after NPCs are initialized:

npcManagerV3:testNPCBehaviors()

5. Enhancing NPC Capabilities

Store the abilities of each NPC (e.g., move, chat, emote) in their database entry. Update NPCDatabase.lua with abilities:

{
    id = "diamond",
    displayName = "Diamond",
    model = "4446576906",
    abilities = { "move", "chat", "emote" },
    ...
}

During NPC creation, check their abilities and dynamically load appropriate scripts:

if table.find(npcData.abilities, "move") then
    WalkScript.walkToRandomPoint(npcModel)
end
if table.find(npcData.abilities, "emote") then
    -- Load emote behaviors here
end

6. Update Storage and Configuration

	1.	Scripts Folder: Store reusable scripts in /src/assets/scripts.
	2.	Animations Folder: Store reusable animations (if needed) in /src/assets/animations.

Example configuration update for default.project.json:

"ServerStorage": {
  "Assets": {
    "scripts": {
      "$path": "src/assets/scripts"
    },
    "animations": {
      "$path": "src/assets/animations"
    }
  }
}

Next Steps:

	1.	Implement these scripts and validate behavior in your game.
	2.	Add test cases for more complex interactions (e.g., group actions, emotes).
	3.	Let me know if you need additional features or optimizations!