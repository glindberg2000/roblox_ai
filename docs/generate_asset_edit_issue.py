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
    # First read the base problem description
    base_doc = read_file('docs/asset_edit_form_issue.md')
    
    # Define the files we want to include
    files_to_include = [
        'api/static/js/dashboard_new/assets.js',
        'api/static/js/dashboard_new/state.js',
        'api/static/js/dashboard_new/ui.js',
        'api/app/dashboard_router.py',
        'api/templates/dashboard_new.html'
    ]

    # Create the complete problem description
    complete_doc = base_doc + "\n\n## Relevant Code Files\n"

    # Add each file's content
    for filepath in files_to_include:
        complete_doc += f"\n### {filepath}\n"
        ext = Path(filepath).suffix
        if ext == '.py':
            complete_doc += "```python\n"
        elif ext == '.js':
            complete_doc += "```javascript\n"
        elif ext == '.html':
            complete_doc += "```html\n"
        else:
            complete_doc += "```\n"
        complete_doc += read_file(filepath)
        complete_doc += "\n```\n"

    # Write to file
    with open('docs/asset_edit_form_issue_complete.md', 'w', encoding='utf-8') as f:
        f.write(complete_doc)

if __name__ == "__main__":
    create_problem_doc()
    print("Generated asset_edit_form_issue_complete.md") 