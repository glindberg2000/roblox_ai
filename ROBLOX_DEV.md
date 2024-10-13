# AI-Driven NPC System Summary

## Overview
We've developed an AI-driven NPC system for a Roblox game, integrating with a FastAPI backend that uses OpenAI's GPT model for generating responses and behaviors.

## Components

### 1. Roblox Script (NPCManager)
- Manages NPC behavior, movement, and interactions.
- Sends requests to the FastAPI backend for AI-generated responses.
- Handles conversation states and timeouts.

Key features:
- Dynamic movement towards players
- Conversation management
- Click and chat-based interactions

### 2. FastAPI Backend
- Receives requests from the Roblox game
- Interacts with OpenAI's GPT model
- Manages conversation history
- Provides structured responses for chat and behavior updates

Key endpoints:
- `/robloxgpt`: Handles both chat and behavior update requests

### 3. OpenAI Integration
- Uses GPT-4o-mini model for generating responses
- Implements function calling for structured outputs

## Current State

1. Basic Functionality:
   - NPCs can move towards players
   - NPCs respond to player interactions
   - Conversation history is maintained

2. Issues Addressed:
   - Fixed JSON parsing and validation errors
   - Improved error handling and logging
   - Resolved context formatting issues between Roblox and FastAPI

3. Remaining Challenges:
   - Greeting behavior needs refinement
   - Ensure consistent and contextually appropriate initial interactions

## Next Steps

1. Refine Greeting Behavior:
   - Implement a more robust system for initial greetings
   - Ensure NPCs greet players appropriately upon first interaction

2. Enhance Contextual Awareness:
   - Improve the context passed from Roblox to FastAPI
   - Utilize game state information for more relevant NPC behaviors

3. Optimize Performance:
   - Implement caching mechanisms to reduce API calls
   - Fine-tune update intervals for smoother NPC behavior

4. Expand NPC Capabilities:
   - Implement more complex behavior patterns
   - Add support for NPC-to-NPC interactions

5. Improve Error Handling and Resilience:
   - Implement fallback behaviors for API failures
   - Add more comprehensive logging and monitoring

## Code Snippets

Key parts of the system include:

1. Roblox NPCManager initialization
2. FastAPI endpoint for handling NPC requests
3. OpenAI function calling implementation

(Specific code snippets can be added here as needed)

## Testing and Deployment

- Roblox Studio for game testing
- FastAPI server deployed on a cloud platform (e.g., AWS, DigitalOcean)
- Continuous logging and monitoring for both Roblox and server components

## Conclusion

The AI-driven NPC system shows promise in creating dynamic and engaging game characters. With further refinement, particularly in the greeting behavior and contextual awareness, it can significantly enhance the player experience in the Roblox game.

## Brainstorm

Certainly! Let's brainstorm on how to enhance the NPC's greeting behavior and self-awareness. This is an excellent idea to make the interactions more personalized and contextually rich. Here's a breakdown of potential improvements and considerations:

1. Enhanced Context Management:
   - Create a more robust context object that includes:
     a) Player interaction history (summarized)
     b) NPC's current state and recent activities
     c) NPC's routines or schedule
     d) Environmental factors (time of day, location, etc.)

2. Player Interaction History:
   - Implement a persistent storage system (e.g., DataStore) to keep track of:
     a) Number of previous interactions
     b) Topics discussed
     c) Player's interests or characteristics noted
     d) Last interaction timestamp

3. NPC Self-Awareness:
   - Develop a "mental model" for the NPC that includes:
     a) Current goals or tasks
     b) Mood or emotional state
     c) Knowledge of its own backstory and characteristics
     d) Awareness of its role in the game world

4. Decision-Making Process:
   - Implement a more sophisticated decision-making system:
     a) Prioritize players based on interaction history and current context
     b) Decide whether to approach players or continue current activities
     c) Choose appropriate greeting or conversation starters based on history and context

5. Greeting Generation:
   - Create a more dynamic greeting system:
     a) Use templates with placeholders for personalized information
     b) Generate context-aware greetings based on time of day, location, and recent events
     c) Reference previous interactions or shared experiences

6. Logging and Debugging:
   - Implement a tiered logging system:
     a) Debug logs for development (not visible to AI)
     b) "Thought process" logs that contribute to the NPC's self-awareness
     c) Clear separation between technical logs and in-character thoughts

Implementation Strategy:

1. Expand the `context` object in the `getResponseFromAI` function to include more detailed information.
2. Create a new module for managing player interaction history using DataStore.
3. Implement a "mental model" update function that runs periodically to update the NPC's self-awareness.
4. Modify the `updateBehavior` function to include more sophisticated decision-making.
5. Update the AI prompt in the FastAPI backend to include instructions for generating personalized greetings.
6. Implement a new logging system that separates technical logs from in-character thoughts.

Let's look at where we might inject these new strategies:

1. In the `NPCManager.new` function:
   - Initialize the mental model and interaction history
   - Set up periodic updates for the mental model

2. In the `updateBehavior` function:
   - Implement the new decision-making process
   - Include the enhanced context in AI requests

3. In the `handleNPCInteraction` function:
   - Use the enhanced context for generating responses
   - Update the interaction history after each interaction

4. In the FastAPI backend:
   - Modify the AI prompt to include instructions for using the enhanced context
   - Implement more structured output for NPC actions and thoughts

Regarding the logging, we should implement a new logging system that clearly separates:
1. Technical logs (for debugging, not sent to AI)
2. NPC's "thoughts" (sent to AI as part of the context)
3. NPC's speech (visible to players)

This way, we can keep the technical logs for debugging without interfering with the NPC's behavior or self-awareness.

Before we start coding, we should:
1. Clearly define the structure of the enhanced context object
2. Design the player interaction history storage schema
3. Outline the decision-making process for the NPC
4. Create templates for personalized greetings
5. Design the new logging system

