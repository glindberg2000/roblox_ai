# Valid Actions for NPC Tools

This document provides a list of valid actions that can be performed using the NPC tools in the Letta framework. Each action is accompanied by a brief description of its usage.

## List of Valid Actions

1. **emote**
   - **Description**: Play an emote animation.
   - **Usage**: Requires the `type` parameter to specify the emote type (e.g., "wave", "dance").
   - **Example**: `perform_action("emote", "wave", "Alice")` - Waves at Alice.

2. **follow**
   - **Description**: Follow a target player.
   - **Usage**: Requires the `target` parameter to specify the player to follow.
   - **Example**: `perform_action("follow", target="Bob")` - Follows Bob.

3. **unfollow**
   - **Description**: Stop following the current target.
   - **Usage**: No additional parameters required.
   - **Example**: `perform_action("unfollow")` - Stops following.

4. **jump**
   - **Description**: Perform a jump animation.
   - **Usage**: No additional parameters required.
   - **Example**: `perform_action("jump")` - Performs a jump.

5. **walk**
   - **Description**: Walk to a target location.
   - **Usage**: Requires the `target` parameter to specify the location.
   - **Example**: `perform_action("walk", target="market")` - Walks to the market.

6. **run**
   - **Description**: Run to a target location.
   - **Usage**: Requires the `target` parameter to specify the location.
   - **Example**: `perform_action("run", target="garden")` - Runs to the garden.

7. **swim**
   - **Description**: Swim to a target location.
   - **Usage**: Requires the `target` parameter to specify the location.
   - **Example**: `perform_action("swim", target="lake")` - Swims to the lake.

8. **climb**
   - **Description**: Climb to a target location.
   - **Usage**: Requires the `target` parameter to specify the location.
   - **Example**: `perform_action("climb", target="wall")` - Climbs the wall.

## Emote Types

- **wave**: Wave hello/goodbye.
- **dance**: Perform a dance animation.
- **point**: Point at a target.
- **laugh**: Perform a laugh animation.

## Notes

- Ensure that the `target` parameter is provided where required.
- Emote actions require specifying the `type` of emote. 