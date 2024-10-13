from datetime import datetime, timedelta

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.expiry_time = timedelta(minutes=30)

    def get_conversation(self, player_id, npc_id):
        key = (player_id, npc_id)
        if key in self.conversations:
            conversation, last_update = self.conversations[key]
            if datetime.now() - last_update > self.expiry_time:
                del self.conversations[key]
                return []
            return conversation
        return []

    def update_conversation(self, player_id, npc_id, message):
        key = (player_id, npc_id)
        if key not in self.conversations:
            self.conversations[key] = ([], datetime.now())
        conversation, _ = self.conversations[key]
        conversation.append(message)
        self.conversations[key] = (conversation[-50:], datetime.now())