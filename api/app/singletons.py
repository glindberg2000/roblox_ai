from .conversation_managerV2 import EnhancedConversationManager

# Create singleton instances
conversation_manager = EnhancedConversationManager()

# Export for use throughout the application
__all__ = ['conversation_manager']