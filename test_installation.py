from letta_templates.npc_tools import (
    TOOL_REGISTRY,
    MINIMUM_PROMPT,
    SOCIAL_AWARENESS_PROMPT,
    GROUP_AWARENESS_PROMPT,
    LOCATION_AWARENESS_PROMPT,
    TOOL_INSTRUCTIONS
)
import letta_templates

print(f"Version: {letta_templates.__version__}")
print("\nAvailable tools:")
for tool in TOOL_REGISTRY:
    print(f"- {tool}")


# Add to test_installation.py
print("\nVerifying prompts:")
print(f"MINIMUM_PROMPT length: {len(MINIMUM_PROMPT)} chars")
print(f"SOCIAL_AWARENESS_PROMPT length: {len(SOCIAL_AWARENESS_PROMPT)} chars")
print(f"GROUP_AWARENESS_PROMPT length: {len(GROUP_AWARENESS_PROMPT)} chars")
print(f"LOCATION_AWARENESS_PROMPT length: {len(LOCATION_AWARENESS_PROMPT)} chars")
print(f"TOOL_INSTRUCTIONS length: {len(TOOL_INSTRUCTIONS)} chars")