# test_install.py
from letta_templates import __version__
from letta_templates.npc_tools import perform_action

print(f"letta-templates version: {__version__}")
print("\nTesting tool access:")
print(perform_action("emote", "wave", "Alice"))