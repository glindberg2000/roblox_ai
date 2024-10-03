import os
import shutil

def create_directory(path):
    os.makedirs(path, exist_ok=True)

def create_file(path, content=""):
    with open(path, 'w') as f:
        f.write(content)

def setup_roblox_project():
    # Project root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(root_dir, "src")

    # Remove existing src directory
    if os.path.exists(src_dir):
        shutil.rmtree(src_dir)

    # Create new directory structure
    create_directory(os.path.join(src_dir, "shared"))
    create_directory(os.path.join(src_dir, "server"))
    create_directory(os.path.join(src_dir, "client"))
    create_directory(os.path.join(src_dir, "assets"))

    # Create file stubs
    create_file(os.path.join(src_dir, "shared", "NPCManager.lua"), "-- NPCManager code goes here\n")
    create_file(os.path.join(src_dir, "server", "MainNPCScript.server.lua"), "-- MainNPCScript code goes here\n")
    create_file(os.path.join(src_dir, "server", "NPCConfigurations.lua"), "-- NPCConfigurations code goes here\n")
    create_file(os.path.join(src_dir, "client", "NPCClientHandler.client.lua"), "-- NPCClientHandler code goes here\n")

    # Create placeholder files for NPC models
    create_file(os.path.join(src_dir, "assets", "Eldrin.rbxm"), "-- Placeholder for Eldrin model\n")
    create_file(os.path.join(src_dir, "assets", "Luna.rbxm"), "-- Placeholder for Luna model\n")

    # Create default.project.json
    default_project_json = '''{
  "name": "EllaAIRobloxGame",
  "tree": {
    "$className": "DataModel",

    "ReplicatedStorage": {
      "$className": "ReplicatedStorage",
      "$path": "src/shared",
      "NPCManager": {
        "$path": "src/shared/NPCManager.lua"
      }
    },

    "ServerScriptService": {
      "$className": "ServerScriptService",
      "$path": "src/server",
      "MainNPCScript": {
        "$path": "src/server/MainNPCScript.server.lua"
      },
      "NPCConfigurations": {
        "$path": "src/server/NPCConfigurations.lua"
      }
    },

    "StarterPlayer": {
      "$className": "StarterPlayer",
      "StarterPlayerScripts": {
        "$className": "StarterPlayerScripts",
        "$path": "src/client",
        "NPCClientHandler": {
          "$path": "src/client/NPCClientHandler.client.lua"
        }
      }
    },

    "ServerStorage": {
      "$className": "ServerStorage",
      "$path": "src/assets",
      "Eldrin": {
        "$path": "src/assets/Eldrin.rbxm"
      },
      "Luna": {
        "$path": "src/assets/Luna.rbxm"
      }
    },

    "Workspace": {
      "$className": "Workspace",
      "$properties": {
        "FilteringEnabled": true
      },
      "NPCs": {
        "$className": "Folder"
      }
    }
  }
}'''
    create_file(os.path.join(root_dir, "default.project.json"), default_project_json)

    print("Roblox project structure created successfully!")

if __name__ == "__main__":
    setup_roblox_project()