@router.get("/api/games")
async def list_games():
    try:
        games = await database.fetch_all_games()
        for game in games:
            # Enrich game data with counts
            game['asset_count'] = await database.count_assets(game['id'])
            game['npc_count'] = await database.count_npcs(game['id'])
        return JSONResponse(games)
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        return JSONResponse({"error": "Failed to fetch games"}, status_code=500)

@router.post("/api/games")
async def create_game(request: Request):
    try:
        data = await request.json()
        game_slug = slugify(data['title'])
        
        # Create game in database
        game_id = await database.create_game(data['title'], game_slug, data['description'])
        
        # Create game directory structure
        create_game_directory(game_slug)
        
        return JSONResponse({"id": game_id, "slug": game_slug})
    except Exception as e:
        logger.error(f"Error creating game: {str(e)}")
        return JSONResponse({"error": "Failed to create game"}, status_code=500)

@router.delete("/api/games/{slug}")
async def delete_game(slug: str):
    try:
        # Delete game from database
        await database.delete_game(slug)
        
        # Delete game directory
        game_path = Path("games") / slug
        if game_path.exists():
            shutil.rmtree(game_path)
        
        return JSONResponse({"message": "Game deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting game: {str(e)}")
        return JSONResponse({"error": "Failed to delete game"}, status_code=500)

@router.get("/api/games/{slug}")
async def get_game(slug: str):
    try:
        game = await database.fetch_game(slug)
        if not game:
            return JSONResponse({"error": "Game not found"}, status_code=404)
        
        game['asset_count'] = await database.count_assets(game['id'])
        game['npc_count'] = await database.count_npcs(game['id'])
        return JSONResponse(game)
    except Exception as e:
        logger.error(f"Error fetching game: {str(e)}")
        return JSONResponse({"error": "Failed to fetch game"}, status_code=500)

@router.put("/api/games/{slug}")
async def update_game(slug: str, request: Request):
    try:
        data = await request.json()
        await database.update_game(slug, data['title'], data['description'])
        return JSONResponse({"message": "Game updated successfully"})
    except Exception as e:
        logger.error(f"Error updating game: {str(e)}")
        return JSONResponse({"error": "Failed to update game"}, status_code=500)

@router.get("/api/assets")
async def list_assets(game_id: Optional[int] = None):
    try:
        with get_db() as db:
            if game_id:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id
                    WHERE a.game_id = ?
                    GROUP BY a.id
                    ORDER BY a.name
                """, (game_id,))
            else:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id
                    WHERE a.game_id IS NULL
                    GROUP BY a.id
                    ORDER BY a.name
                """)
            assets = [dict(row) for row in cursor.fetchall()]
            return JSONResponse({"assets": assets})
    except Exception as e:
        logger.error(f"Error fetching assets: {str(e)}")
        return JSONResponse({"error": "Failed to fetch assets"}, status_code=500)

@router.get("/api/npcs")
async def list_npcs(game_id: Optional[int] = None):
    try:
        if game_id:
            npcs = await database.fetch_npcs_by_game(game_id)
        else:
            npcs = await database.fetch_all_npcs()
        return JSONResponse(npcs)
    except Exception as e:
        logger.error(f"Error fetching NPCs: {str(e)}")
        return JSONResponse({"error": "Failed to fetch NPCs"}, status_code=500)