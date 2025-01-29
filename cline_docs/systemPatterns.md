# System Patterns: NPC Interaction System

## Core Components
1. NPCManagerV3
   - Central management of NPCs
   - Handles interactions and state
   - Manages conversation flow

2. InteractionService
   - Proximity detection
   - Cluster formation
   - Position tracking

3. GameStateService
   - State synchronization
   - Snapshot management
   - Backend communication

## Key Patterns
1. Event-Driven Architecture
   - System messages trigger interactions
   - Proximity events drive state changes
   - Message-based communication

2. State Management
   - Regular snapshots
   - Immediate critical updates
   - Cluster-based state tracking

3. Service Pattern
   - Separated concerns
   - Clear interfaces
   - Modular design 