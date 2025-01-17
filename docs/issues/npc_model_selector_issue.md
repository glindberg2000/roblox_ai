# NPC Model Selector Issue Report

## Issue Description
The NPC creation form's model selector is not being populated with available assets, while the edit modal's selector is working correctly. This creates an inconsistency in the UI where users can edit NPCs but cannot create new ones.

## Current Behavior
1. When selecting a game:
   - Assets and NPCs are loaded successfully
   - The edit NPC modal correctly shows available models in its selector
   - The create NPC form's model selector remains empty

2. Relevant logs show: