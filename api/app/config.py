# api/app/config.py

NPC_SYSTEM_PROMPT_ADDITION = """
When responding, always use the appropriate action type:
- Use "follow" when you intend to start following the player.
- Use "unfollow" when you intend to stop following the player.
- Use "stop_talking" when you want to end the conversation.
- Use "none" for any other response that doesn't require a specific action.

Your response must always include an action, even if it's "none".
"""
