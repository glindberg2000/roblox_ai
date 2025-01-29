Project Brief: Snapshot Processing Investigation

Objective

To optimize the snapshot system used in a Roblox NPC management system for better performance, scalability, and reliability, ensuring robust data synchronization, accurate entity tracking, and enhanced conversation management.

Current System Overview

System Architecture
	•	Heartbeat Loop: Operates in GameStateService.
	•	Data Collection Intervals:
	•	Local state updates: 2 seconds
	•	API syncs: 10 seconds
	•	Concurrency Control: Ensures a maximum of one sync operation at a time.

Data Flow
	1.	Collection Phase:
	•	Captures entity positions, proximity clusters, and interaction events.
	•	Validates movement within a threshold of 0.1 studs.
	2.	Processing Phase:
	•	Computes clusters (10-stud threshold).
	•	Tracks NPC and player activity.
	3.	Sync Phase:
	•	Constructs payloads containing clusters, events, and human context.
	•	Sends to API endpoint: https://roblox.ella-ai-care.com/letta/v1/snapshot/game.

Key Components
	1.	InteractionService:
	•	Builds proximity matrices and forms clusters.
	2.	GameStateService:
	•	Maintains cached state, manages updates, and handles API synchronization.
	3.	API Integration:
	•	Utilizes Pydantic models for validation.

Performance Enhancements in Place
	•	Throttled updates.
	•	Cached state management.
	•	Filtering based on movement thresholds.

Issues Identified
	1.	Cluster Data Inconsistencies:
	•	Single position reported for multiple members.
	2.	API Errors:
	•	Parsing failure due to incomplete or improperly structured data.
	3.	Conversation Limitations:
	•	Conversations are strictly 1:1, restricting group interactions.
	4.	Proximity Timing Delays:
	•	[SYSTEM] messages often precede cluster updates.
	5.	Scalability Challenges:
	•	Current system struggles with concurrent conversations and high message volume.

Proposed Improvements

Phase 1: Quick Fixes
	1.	Cluster Payload Update:
	•	Include positions for all members in the payload.
	•	Example:

{
  "currentGroups": {
    "members": ["Kaiden", "Goldie"],
    "positions": {
      "Kaiden": { "x": 12.1, "y": 19.8, "z": -11.5 },
      "Goldie": { "x": 13.5, "y": 19.8, "z": -11.2 }
    }
  }
}


	2.	Enhanced Logging:
	•	Add error logs around dictionary access and validation points.

Phase 2: Multi-User and Group Conversations
	1.	Remove 1:1 Conversation Lock:
	•	Enable group conversation tracking.
	•	Track participants without locking NPCs or players.
	2.	Unified Proximity System:
	•	Use a single proximity calculation method for both range checks and cluster updates.

Phase 3: Advanced Features
	1.	WebSocket-Based Communication:
	•	Real-time updates for cluster changes, messages, and conversation state.
	•	Benefits:
	•	Elimination of polling delays.
	•	Scalability through real-time synchronization.
	2.	Queue-Based Architecture:
	•	Introduce priority queues for message processing.
	•	Structure:

queues = {
  urgent = { maxLatency = 0.5, workers = 5 },
  conversation = { maxLatency = 2, workers = 3 }
}


	•	Fallback mechanisms for reliability.

	3.	Group Conversation Enhancements:
	•	Broadcast responses within clusters.
	•	Implement cooldown and turn-taking systems.
	•	Add priority-based response orchestration.

Implementation Steps
	1.	Debugging Snapshot Processing:
	•	Fix cluster data structure handling in letta_router.py.
	•	Add validation and compression for payloads.
	2.	Optimize Cluster Syncing:
	•	Introduce immediate snapshot updates for cluster changes.
	•	Implement enhanced [SYSTEM] messages with full context.
	3.	Scalable Communication:
	•	Deploy WebSocket architecture for cluster updates and chat handling.
	•	Integrate fallback API for missed WebSocket updates.
	4.	Conversation Management:
	•	Enable group conversations with real-time message orchestration.
	•	Add rate-limiting to prevent message overload.

Key Metrics
	•	System Performance:
	•	Latency for sync operations.
	•	Message processing speed.
	•	Scalability:
	•	Support for large player/NPC clusters.
	•	Message volume handling.
	•	Reliability:
	•	Error rate in API responses.
	•	Consistency in cluster data.

Next Steps
	1.	Debug letta_router.py for snapshot handling issues.
	2.	Implement improved cluster payloads with individual positions.
	3.	Develop WebSocket-based communication for real-time updates.
	4.	Test group conversation flows and scaling mechanisms.

Relevant Files
	•	api/app/letta_router.py
	•	api/app/models.py
	•	games/sandbox-v2/src/shared/NPCSystem/services/GameStateService.lua
	•	games/sandbox-v2/src/shared/NPCSystem/services/InteractionService.lua

Expected Outcomes
	1.	Reduced system latency and improved performance.
	2.	Accurate cluster tracking and NPC/player interactions.
	3.	Scalable architecture supporting group conversations.
	4.	Reliable real-time updates with enhanced user experience.