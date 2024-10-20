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

# AI-Driven NPC System Development Status (v3.1)

## Current State

1. **Successful Implementation of Structured Outputs**
   - Utilizing OpenAI's beta.chat.completions.parse for structured NPC responses.
   - Implemented NPCResponseV3 Pydantic model for consistent response structure.

2. **Enhanced Error Handling and Logging**
   - Specific handling for OpenAI API errors and model refusals.
   - Improved logging for better debugging and monitoring.

3. **Robust Conversation Management**
   - Implemented ConversationManager for maintaining chat history.
   - Context-aware responses including environment perception and recent memories.

4. **Improved NPC Interaction and Perception**
   - NPCs can perceive their environment, including visible objects and players.
   - Implemented basic memory system for recent interactions.

5. **Integrated FastAPI Backend**
   - Successfully connected Roblox game with FastAPI backend for NPC interactions.
   - Implemented /robloxgpt/v3 endpoint for handling NPC requests.

## Achievements

- **Modular and Maintainable Codebase**: Improved code structure with clear separation of concerns.
- **Enhanced AI Responses**: Utilizing Structured Outputs for more controlled and contextual NPC behaviors.
- **Improved Error Resilience**: Better handling of API errors and edge cases.

## Next Steps and Goals

1. **Refine Greeting Behavior**
   - Implement more sophisticated initial interaction logic.
   - Develop personalized greeting system based on player history.

2. **Enhance Contextual Awareness**
   - Expand the context object to include more game state information.
   - Implement a more robust "mental model" for NPCs.

3. **Optimize Performance**
   - Implement caching mechanisms to reduce API calls.
   - Fine-tune update intervals for smoother NPC behavior.

4. **Expand NPC Capabilities**
   - Implement more complex behavior patterns.
   - Add support for NPC-to-NPC interactions.

5. **Improve Conversation Flow**
   - Implement topic tracking and context-based conversation steering.
   - Develop mechanism for NPCs to remember and reference past interactions.

6. **Enhance Decision-Making Process**
   - Develop a more sophisticated system for NPC action choices.
   - Implement priority-based interaction system for multiple nearby players.

7. **Implement Advanced Logging System**
   - Create tiered logging with separation of technical logs and NPC "thoughts".
   - Develop a system for analyzing NPC behavior patterns over time.

8. **Expand Testing and Quality Assurance**
   - Develop comprehensive unit and integration tests.
   - Implement automated testing for NPC behaviors and interactions.

9. **Enhance Security and Rate Limiting**
   - Implement more robust API key management.
   - Develop rate limiting system to prevent abuse and manage costs.

10. **Improve Documentation and Onboarding**
    - Create comprehensive documentation for the NPC system.
    - Develop tutorials and examples for extending NPC capabilities.

## Current Challenges

- Ensuring consistent and contextually appropriate initial NPC interactions.
- Balancing API call frequency with responsiveness of NPC behaviors.
- Managing the complexity of NPC decision-making while maintaining performance.

## Conclusion

The AI-driven NPC system has made significant progress, particularly in implementing Structured Outputs and improving error handling. The focus now shifts to enhancing the NPCs' contextual awareness, refining their behavior patterns, and optimizing the system's performance and scalability.


# AI-Driven NPC System Development Status (v3.2)

## Current State

1. **Successful Implementation of Structured Outputs**
   - Utilizing OpenAI's beta.chat.completions.parse for structured NPC responses.
   - Implemented NPCResponseV3 Pydantic model for consistent response structure.

2. **Enhanced Error Handling and Logging**
   - Specific handling for OpenAI API errors and model refusals.
   - Improved logging for better debugging and monitoring.

3. **Robust Conversation Management**
   - Implemented ConversationManager for maintaining chat history.
   - Context-aware responses including environment perception and recent memories.

4. **Improved NPC Interaction and Perception**
   - NPCs can perceive their environment, including visible objects and players.
   - Implemented basic memory system for recent interactions.

5. **Integrated FastAPI Backend**
   - Successfully connected Roblox game with FastAPI backend for NPC interactions.
   - Implemented /robloxgpt/v3 endpoint for handling NPC requests.

6. **AssetDB API and Local DB Implementation**
   - Developed AssetDatabase for storing asset information.
   - Created AssetInitializer for populating LocalDB in ReplicatedStorage.
   - Implemented AssetModule for accessing asset data from scripts.

7. **Console Tools for Asset Management**
   - Created update_asset_descriptions.py for managing asset descriptions.
   - Implemented functionality to update JSON and Lua databases.

## Achievements

- **Modular and Maintainable Codebase**: Improved code structure with clear separation of concerns.
- **Enhanced AI Responses**: Utilizing Structured Outputs for more controlled and contextual NPC behaviors.
- **Improved Error Resilience**: Better handling of API errors and edge cases.
- **Efficient Asset Management**: Streamlined process for updating and accessing asset information.

## Next Steps and Goals

1. **Fix Asset Search Glitches**
   - Investigate and resolve issues with certain assets not being detected in-game.
   - Ensure consistent asset visibility across all game environments.

2. **Enhance NPC Vision and Perception**
   - Prioritize newly visible items in NPC perception.
   - Implement immediate, natural reactions to new objects entering NPC's vision.
   - Develop system for NPCs to comment on obvious new elements without player prompting.

3. **Improve Conversation Switching and Locking**
   - Implement clear conversation locking mechanism for multiple nearby NPCs.
   - Enable conversation switching when player calls NPC by name.
   - Refine conversation locking to only activate after player responds to NPC.

4. **Refine Greeting Behavior**
   - Implement more sophisticated initial interaction logic.
   - Develop personalized greeting system based on player history.

5. **Enhance Contextual Awareness**
   - Expand the context object to include more game state information.
   - Implement a more robust "mental model" for NPCs.

6. **Optimize Performance**
   - Implement caching mechanisms to reduce API calls.
   - Fine-tune update intervals for smoother NPC behavior.

7. **Expand NPC Capabilities**
   - Implement more complex behavior patterns.
   - Add support for NPC-to-NPC interactions.

8. **Improve Conversation Flow**
   - Implement topic tracking and context-based conversation steering.
   - Develop mechanism for NPCs to remember and reference past interactions.

9. **Enhance Decision-Making Process**
   - Develop a more sophisticated system for NPC action choices.
   - Implement priority-based interaction system for multiple nearby players.

10. **Implement Advanced Logging System**
    - Create tiered logging with separation of technical logs and NPC "thoughts".
    - Develop a system for analyzing NPC behavior patterns over time.

11. **Expand Testing and Quality Assurance**
    - Develop comprehensive unit and integration tests.
    - Implement automated testing for NPC behaviors and interactions.

12. **Enhance Security and Rate Limiting**
    - Implement more robust API key management.
    - Develop rate limiting system to prevent abuse and manage costs.

13. **Improve Documentation and Onboarding**
    - Create comprehensive documentation for the NPC system.
    - Develop tutorials and examples for extending NPC capabilities.

## Current Challenges

- Ensuring consistent asset detection and visibility in-game.
- Balancing NPC responsiveness to new stimuli with natural conversation flow.
- Managing complex conversation dynamics with multiple NPCs in proximity.
- Optimizing API call frequency while maintaining responsive NPC behaviors.
- Handling the increasing complexity of NPC decision-making while maintaining performance.

## Conclusion

The AI-driven NPC system continues to evolve, with significant improvements in asset management and structured AI responses. The focus for the next development phase is on enhancing the NPCs' perceptual abilities, refining conversation dynamics, and resolving asset visibility issues. These improvements aim to create more natural and engaging NPC interactions, further enhancing the player experience in the game world.