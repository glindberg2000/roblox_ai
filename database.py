async def fetch_all_games(self):
    """Fetch all games from the database"""
    query = """
        SELECT id, title, slug, description 
        FROM games 
        ORDER BY title
    """
    return await self.fetch_all(query)

async def create_game(self, title: str, slug: str, description: str):
    """Create a new game entry"""
    query = """
        INSERT INTO games (title, slug, description)
        VALUES (?, ?, ?)
        RETURNING id
    """
    result = await self.execute(query, (title, slug, description))
    return result['id']

async def count_assets(self, game_id: int):
    """Count assets for a specific game"""
    query = "SELECT COUNT(*) as count FROM assets WHERE game_id = ?"
    result = await self.fetch_one(query, (game_id,))
    return result['count'] if result else 0

async def count_npcs(self, game_id: int):
    """Count NPCs for a specific game"""
    query = "SELECT COUNT(*) as count FROM npcs WHERE game_id = ?"
    result = await self.fetch_one(query, (game_id,))
    return result['count'] if result else 0

async def fetch_game(self, slug: str):
    """Fetch a single game by slug"""
    query = """
        SELECT id, title, slug, description 
        FROM games 
        WHERE slug = ?
    """
    return await self.fetch_one(query, (slug,))

async def update_game(self, slug: str, title: str, description: str):
    """Update a game's details"""
    query = """
        UPDATE games 
        SET title = ?, description = ?
        WHERE slug = ?
    """
    await self.execute(query, (title, description, slug))

async def fetch_assets_by_game(self, game_id: int):
    """Fetch assets for a specific game"""
    query = """
        SELECT * FROM assets 
        WHERE game_id = ?
        ORDER BY name
    """
    return await self.fetch_all(query, (game_id,))

async def fetch_npcs_by_game(self, game_id: int):
    """Fetch NPCs for a specific game"""
    query = """
        SELECT * FROM npcs 
        WHERE game_id = ?
        ORDER BY display_name
    """
    return await self.fetch_all(query, (game_id,))

async def create_asset(self, data: dict, game_id: int):
    """Create a new asset with game_id"""
    query = """
        INSERT INTO assets (name, asset_id, game_id, description)
        VALUES (?, ?, ?, ?)
        RETURNING id
    """
    result = await self.execute(
        query, 
        (data['name'], data['assetId'], game_id, data.get('description', ''))
    )
    return result['id']

async def create_npc(self, data: dict, game_id: int):
    """Create a new NPC with game_id"""
    query = """
        INSERT INTO npcs (display_name, asset_id, game_id, system_prompt, response_radius)
        VALUES (?, ?, ?, ?, ?)
        RETURNING id
    """
    result = await self.execute(
        query,
        (data['displayName'], data['assetId'], game_id, data['systemPrompt'], data['responseRadius'])
    )
    return result['id'] 