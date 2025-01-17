import os
import re
from pathlib import Path
import argparse

def scan_and_replace_files(directory, dry_run=True, verbose=True):
    # Define pattern-to-replacement mapping
    replacements = [
        # Original patterns
        (r'require\s*\(\s*ReplicatedStorage\.NPCSystem\.ChatUtils\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.chat.ChatUtils)'),
        (r'require\s*\(\s*ReplicatedStorage\.NPCSystem\.LettaConfig\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.config.LettaConfig)'),
        (r'require\s*\(\s*ReplicatedStorage\.NPCSystem\.NPCChatHandler\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.chat.NPCChatHandler)'),
        (r'require\s*\(\s*ReplicatedStorage\.NPCSystem\.NPCConfig\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.config.NPCConfig)'),
        
        # Service patterns
        (r'require\s*\(\s*ReplicatedStorage\.Shared\.services\.MovementService\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.services.MovementService)'),
        (r'require\s*\(\s*ReplicatedStorage\.Shared\.services\.VisionService\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.services.VisionService)'),
        (r'require\s*\(\s*ReplicatedStorage\.Shared\.services\.InteractionService\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.services.InteractionService)'),
        (r'require\s*\(\s*ReplicatedStorage\.Shared\.services\.LoggerService\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)'),
        
        # Logger patterns
        (r'require\s*\(\s*ServerScriptService:WaitForChild\("Logger"\)\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)'),
        (r'require\s*\(\s*ReplicatedStorage:WaitForChild\("Logger"\)\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)'),
        
        # Additional variations with game:GetService
        (r'require\s*\(\s*game:GetService\("ReplicatedStorage"\)\.NPCSystem\.ChatUtils\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.chat.ChatUtils)'),
        (r'require\s*\(\s*game:GetService\("ReplicatedStorage"\)\.Shared\.services\.LoggerService\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)'),
        
        # V4ChatClient patterns
        (r'require\s*\(\s*ReplicatedStorage\.NPCSystem\.NPCConfig\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.config.NPCConfig)'),
        (r'require\s*\(\s*ReplicatedStorage\.NPCSystem\.ChatUtils\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.chat.ChatUtils)'),
        (r'require\s*\(\s*ReplicatedStorage\.NPCSystem\.LettaConfig\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.config.LettaConfig)'),
        
        # Additional WaitForChild variations
        (r'require\s*\(\s*ReplicatedStorage:WaitForChild\("NPCSystem"\)\.ChatUtils\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.chat.ChatUtils)'),
        (r'require\s*\(\s*ReplicatedStorage:WaitForChild\("NPCSystem"\)\.LettaConfig\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.config.LettaConfig)'),
        (r'require\s*\(\s*ReplicatedStorage:WaitForChild\("NPCSystem"\)\.NPCConfig\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.config.NPCConfig)'),
        
        # game:GetService variations
        (r'require\s*\(\s*game:GetService\("ReplicatedStorage"\)\.NPCSystem\.NPCConfig\s*\)',
         'require(ReplicatedStorage.Shared.NPCSystem.config.NPCConfig)'),
        
        # V4ChatClient specific patterns
        (r'local NPCConfig = require\(ReplicatedStorage\.NPCSystem\.NPCConfig\)',
         'local NPCConfig = require(ReplicatedStorage.Shared.NPCSystem.config.NPCConfig)'),
        (r'local ChatUtils = require\(ReplicatedStorage\.NPCSystem\.ChatUtils\)',
         'local ChatUtils = require(ReplicatedStorage.Shared.NPCSystem.chat.ChatUtils)'),
        (r'local LettaConfig = require\(ReplicatedStorage\.NPCSystem\.LettaConfig\)',
         'local LettaConfig = require(ReplicatedStorage.Shared.NPCSystem.config.LettaConfig)'),
        
        # With variable assignment
        (r'local \w+ = require\(ReplicatedStorage\.NPCSystem\.ChatUtils\)',
         'local ChatUtils = require(ReplicatedStorage.Shared.NPCSystem.chat.ChatUtils)'),
        (r'local \w+ = require\(ReplicatedStorage\.NPCSystem\.LettaConfig\)',
         'local LettaConfig = require(ReplicatedStorage.Shared.NPCSystem.config.LettaConfig)'),
        (r'local \w+ = require\(ReplicatedStorage\.NPCSystem\.NPCConfig\)',
         'local NPCConfig = require(ReplicatedStorage.Shared.NPCSystem.config.NPCConfig)'),
    ]

    findings = []

    if verbose:
        print(f"Scanning directory: {directory}")

    # Walk through all .lua files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.lua'):
                filepath = os.path.join(root, file)
                if verbose:
                    print(f"Checking file: {filepath}")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if verbose:
                            print(f"File size: {len(content)} bytes")
                    
                    new_content = content
                    for pattern, replacement in replacements:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            if verbose:
                                print(f"Found match in {filepath}: {match.group()}")
                                print(f"Will replace with: {replacement}")
                            findings.append({
                                'file': filepath,
                                'old_require': match.group(),
                                'new_require': replacement,
                                'line_number': len(content[:match.start()].splitlines()) + 1
                            })
                            new_content = new_content.replace(match.group(), replacement)
                    
                    if new_content != content and not dry_run:
                        print(f"Updating {filepath}")
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                            
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    if verbose:
        print("\nChecking V4ChatClient.lua requires:")
        v4_path = os.path.join(directory, "shared/NPCSystem/chat/V4ChatClient.lua")
        try:
            with open(v4_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\nFirst 500 chars of V4ChatClient.lua:")
                print(content[:500])
                # Print all require statements
                requires = re.findall(r'local \w+ = require[^)]+\)', content)
                print("\nRequire statements found:")
                for req in requires:
                    print(req)
        except Exception as e:
            print(f"Error reading V4ChatClient.lua: {e}")

    return findings

def main():
    parser = argparse.ArgumentParser(description='Update require paths in Lua files')
    parser.add_argument('--apply', action='store_true', help='Apply the changes (default is dry-run)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')
    args = parser.parse_args()

    src_dir = 'src'
    findings = scan_and_replace_files(src_dir, dry_run=not args.apply, verbose=args.verbose)
    
    print("\nFiles needing updates:")
    for finding in findings:
        print(f"\nFile: {finding['file']}")
        print(f"Line {finding['line_number']}: {finding['old_require']}")
        print(f"Should be: {finding['new_require']}")

    print(f"\nTotal files to update: {len(set(f['file'] for f in findings))}")
    print(f"Total replacements needed: {len(findings)}")
    
    if not args.apply:
        print("\nThis was a dry run. Use --apply to make the changes.")
    else:
        print("\nChanges have been applied.")

if __name__ == "__main__":
    main() 