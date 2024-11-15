from fastapi import FastAPI, HTTPException
from . import database

app = FastAPI()

@app.get("/items/")
async def read_items(game_id: int = None):
    return database.get_items(game_id)

@app.get("/export/lua")
async def export_lua(game_id: int = None):
    return database.export_to_lua(game_id) 