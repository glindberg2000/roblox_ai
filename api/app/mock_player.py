class MockPlayer:
    """Mock player class for NPC-NPC interactions"""
    def __init__(self, display_name: str, npc_id: str, participant_type: str = "npc"):
        self.display_name = display_name
        self.npc_id = npc_id
        self.participant_type = participant_type
        self.Name = display_name  # For compatibility with Player interface
        
    def is_player(self) -> bool:
        return False
        
    def __str__(self) -> str:
        return f"MockPlayer({self.display_name}, {self.npc_id})" 