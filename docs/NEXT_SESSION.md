# Next Development Session

## Primary Goal
Create a proper games management system in the dashboard, replacing the current game selector dropdown.

## Tasks

1. Create Games Dashboard Page
   - Add "Games" tab in dashboard.html
   - Create games.js for frontend logic
   - Design card-based layout for games (similar to assets/NPCs)
   - Each game card shows:
     * Title
     * Description
     * Asset count
     * NPC count
     * Edit/Delete buttons

2. Game Management Features
   - Create Game:
     * Form with name, slug, description
     * Option to copy assets from existing game
     * Creates proper directory structure in games/
     * Initializes empty JSON/Lua files
   - Edit Game:
     * Update metadata
     * Configure game settings
   - Delete Game:
     * Remove from database
     * Option to archive game files

3. Backend Updates
   - Add new endpoints in dashboard_router.py:
     * GET /api/games - List all games
     * POST /api/games - Create new game
     * PUT /api/games/{slug} - Update game
     * DELETE /api/games/{slug} - Delete game
   - Update database.py for game operations
   - Add game directory management in utils.py

4. Directory Structure Management
   - Create script to generate game directory structure:
     ```
     games/
     └── {game_slug}/
         ├── src/
         │   ├── assets/
         │   │   └── npcs/
         │   ├── data/
         │   │   ├── AssetDatabase.json
         │   │   ├── AssetDatabase.lua
         │   │   ├── NPCDatabase.json
         │   │   └── NPCDatabase.lua
         │   └── shared/
         │       └── modules/
         └── default.project.json
     ```
   - Handle asset copying between games
   - Manage Rojo project files

5. Testing
   - Add tests for game management endpoints
   - Test directory creation/deletion
   - Test asset migration between games
   - Update existing tests for game context

6. Documentation
   - Update API documentation
   - Add game management section to ROBLOX_DEV.md
   - Document directory structure requirements
   - Add game migration guide

## Technical Details

1. Database Updates
   - games table already exists
   - Need to enforce game_id foreign keys
   - Add indexes for performance

2. File Structure
   - Keep shared modules in game directories
   - Maintain JSON/Lua sync across games
   - Handle asset references between games

3. API Endpoints
   - All game operations in dashboard_router.py
   - Maintain separation from NPC AI endpoints
   - Add proper error handling

4. Frontend
   - Add games.js to static/js/
   - Update dashboard.html layout
   - Add game management modals
   - Improve navigation between games

## Dependencies
- SQLite database schema
- JSON/Lua file structure
- Directory management utilities
- Frontend templates

## Notes
- Keep AI endpoints in routers.py untouched
- Maintain backward compatibility
- Consider future multi-game features
- Document all new endpoints 