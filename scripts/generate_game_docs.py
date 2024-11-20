import os
import json
from datetime import datetime

def create_game_docs(game_path):
    print(f'\nStarting documentation generation for: {os.path.abspath(game_path)}')
    
    docs = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'gameDirectory': game_path,
        'fileStructure': {},
        'luaFiles': {},
        'projectConfig': None
    }

    def read_file(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                print(f'Reading file: {file_path}')
                return file.read()
        except Exception as e:
            print(f'Error reading file {file_path}: {e}')
            return None

    def process_directory(dir_path, structure):
        try:
            print(f'\nProcessing directory: {dir_path}')
            items = os.listdir(dir_path)
            for item in items:
                full_path = os.path.join(dir_path, item)
                if os.path.isdir(full_path):
                    print(f'Found directory: {item}')
                    structure[item] = {}
                    process_directory(full_path, structure[item])
                else:
                    print(f'Found file: {item}')
                    structure[item] = 'file'
                    if item.endswith('.lua'):
                        print(f'Found Lua file: {item}')
                        content = read_file(full_path)
                        if content:
                            relative_path = os.path.relpath(full_path, game_path)
                            docs['luaFiles'][relative_path] = content
                    elif item == 'default.project.json':
                        print('Found project configuration file')
                        content = read_file(full_path)
                        if content:
                            docs['projectConfig'] = content
        except Exception as e:
            print(f'Error processing directory {dir_path}: {e}')

    # Process the game directory
    process_directory(game_path, docs['fileStructure'])

    # Generate markdown documentation
    markdown = f'''# Game Documentation
Generated on: {docs['timestamp']}

## Directory Structure

'''
def print_structure(structure, indent=0):
result = ‘’
for name, value in sorted(structure.items()):
result += ’  ’ * indent + name + ‘\n’
if isinstance(value, dict):
result += print_structure(value, indent + 1)
return result


markdown += print_structure(docs['fileStructure'])
markdown += '```\n\n'

# Add Lua files
if docs['luaFiles']:
    markdown += '## Lua Files\n\n'
    for lua_file, content in docs['luaFiles'].items():
        markdown += f'### File: `{lua_file}`\n\n'
        markdown += '```lua\n'
        markdown += content
        markdown += '\n```\n\n'

# Add project configuration
if docs['projectConfig']:
    markdown += '## Project Configuration\n\n'
    try:
        parsed_config = json.loads(docs['projectConfig'])
        markdown += '```json\n'
        markdown += json.dumps(parsed_config, indent=4)
        markdown += '\n```\n\n'
    except json.JSONDecodeError as e:
        print(f'Error parsing project configuration as JSON: {e}')
        markdown += 'Invalid JSON format in project configuration file.\n\n'

return markdown


