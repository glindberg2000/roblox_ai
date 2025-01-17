import os
from pathlib import Path

def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {filepath}"
    except Exception as e:
        return f"Error reading file {filepath}: {str(e)}"

def create_problem_doc():
    # Define the files we want to include
    files_to_include = [
        'api/app/dashboard_router.py',
        'api/static/js/dashboard_new/index.js',
        'api/static/js/dashboard_new/state.js',
        'api/static/js/dashboard_new/ui.js',
        'api/static/js/dashboard_new/utils.js',
        'api/static/js/dashboard_new/games.js',
        'api/static/js/dashboard_new/assets.js',
        'api/static/js/dashboard_new/npc.js',
        'api/static/js/abilityConfig.js',
        'api/templates/dashboard_new.html'
    ]

    # Create the problem description
    problem_desc = """
Problem Description: NPC Edit Form Issue in New Dashboard

Current State:
1. NPC edit form is showing empty values for required fields
2. Save operation fails with 500 Internal Server Error
3. Error message: "'NoneType' object is not subscriptable"

Relevant Logs:
"""

    # Add each file's content
    for filepath in files_to_include:
        problem_desc += f"\n### {filepath}\n"
        problem_desc += "```javascript\n"
        problem_desc += read_file(filepath)
        problem_desc += "\n```\n"

    # Write to file
    with open('dashboard_modularization_issue.md', 'w', encoding='utf-8') as f:
        f.write(problem_desc)

if __name__ == "__main__":
    create_problem_doc()
    print("Generated dashboard_modularization_issue.md") 