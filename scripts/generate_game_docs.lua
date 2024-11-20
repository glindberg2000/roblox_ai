local fs = require("fs")
local json = require("json")
local path = require("path")

local function createGameDocs(gamePath)
    local docs = {
        timestamp = os.date(),
        gameDirectory = gamePath,
        fileStructure = {},
        luaFiles = {},
        projectConfig = nil
    }

    -- Function to read file contents
    local function readFile(filePath)
        local file = io.open(filePath, "r")
        if file then
            local content = file:read("*all")
            file:close()
            return content
        end
        return nil
    end

    -- Function to process directory recursively
    local function processDirectory(dir, structure)
        local items = fs.readdirSync(dir)
        
        for _, item in ipairs(items) do
            local fullPath = path.join(dir, item)
            local stats = fs.statSync(fullPath)
            
            if stats.type == "directory" then
                structure[item] = {}
                processDirectory(fullPath, structure[item])
            else
                structure[item] = "file"
                
                -- Store Lua file contents
                if item:match("%.lua$") then
                    local content = readFile(fullPath)
                    if content then
                        docs.luaFiles[fullPath] = content
                    end
                end
                
                -- Store project config
                if item == "default.project.json" then
                    local content = readFile(fullPath)
                    if content then
                        docs.projectConfig = content
                    end
                end
            end
        end
    end

    -- Process the game directory
    processDirectory(gamePath, docs.fileStructure)

    -- Generate markdown documentation
    local markdown = [[
# Game Documentation
Generated on: ]] .. docs.timestamp .. [[

## Directory Structure
]]

    -- Function to print directory structure
    local function printStructure(structure, indent)
        local result = ""
        for name, value in pairs(structure) do
            result = result .. string.rep("  ", indent) .. name .. "\
    end

    -- Print directory structure
    printStructure(docs.fileStructure, 0)

    -- Add Lua files section
    markdown = markdown .. "\n\n## Lua Files\n"
    for filePath, content in pairs(docs.luaFiles) do
        markdown = markdown .. "### " .. filePath .. "\n\n"
        markdown = markdown .. content .. "\n\n"
    end

    -- Add project config section
    if docs.projectConfig then
        markdown = markdown .. "\n\n## Project Config\n"
        markdown = markdown .. docs.projectConfig .. "\n\n"
    end

    -- Save markdown documentation to a file
    local outputFilePath = path.join(gamePath, "game_docs.md")
    local outputFile = io.open(outputFilePath, "w")
    if outputFile then
        outputFile:write(markdown)
        outputFile:close()
    end
end

-- Example usage
createGameDocs("/path/to/your/game") 