# Action System Documentation

## Overview

This document outlines the current action system used in the NPC interaction framework. It explains how actions are generated by the AI, extracted, routed, and executed in the Lua environment. The focus is on the existing `follow` and `unfollow` actions, providing a foundation for future enhancements.

## 1. AI Action Generation

- **AI Response**: The AI generates a response that includes an action. This response is typically structured with a `message`, `action`, and `metadata`.
- **Action Structure**: The action is an object with a `type` and optional `data`. For example:  ```json
  {
    "type": "follow",
    "data": {}
  }  ```

## 2. Action Extraction

- **V4ChatClient**: The AI's response is processed by the `V4ChatClient` module. This module handles the communication with the AI and extracts the action from the response.
- **Adaptation**: The response is adapted from the AI's format to the format used by the Lua system. This involves converting the response into a structure that the Lua scripts can understand and process.

## 3. Action Routing and Execution

- **NPCManagerV3**: The `NPCManagerV3` module is responsible for processing the AI response and executing the action. This is done in the `processAIResponse` function.
- **Action Execution**: The function checks the `action.type` and calls the appropriate method to execute the action. For example:
  - **Follow Action**: If the action type is `follow`, the `startFollowing` method is called.
  - **Unfollow Action**: If the action type is `unfollow`, the `stopFollowing` method is called.

## Example Code Flow

1. **AI Sends Action**: The AI sends a response with an action, such as `follow`.
2. **V4ChatClient Handles Response**: The response is received and processed by `V4ChatClient`.
3. **Adaptation**: The response is adapted to the Lua format.
4. **NPCManagerV3 Processes Action**: The `processAIResponse` function in `NPCManagerV3` checks the action type.
5. **Execute Action**: The corresponding method (`startFollowing` or `stopFollowing`) is called based on the action type.

## Current Limitations

- **Decentralized Handling**: Actions are handled directly within `NPCManagerV3`, which can lead to scattered logic as more actions are added.
- **Limited Action Types**: Currently, only a few action types are supported (`follow`, `unfollow`).

## Future Enhancements

- **Centralized Action Router**: Consider implementing a centralized action router or service to handle actions more efficiently. This would involve creating a dedicated module to route and execute actions, making the system more scalable and maintainable. 