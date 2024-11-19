from fastapi import APIRouter, HTTPException
from ..modules.game_creator import GameCreator
from typing import Optional, Dict

router = APIRouter()
game_creator = GameCreator()

@router.post("/games/create/{game_id}")
async def create_game(
    game_id: str,
    config: Optional[Dict] = None,
    destination: Optional[str] = None
):
    try:
        game_path = await game_creator.create_game(
            game_id=game_id,
            config=config,
            destination=destination
        )
        return {
            "status": "success",
            "game_id": game_id,
            "path": str(game_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 