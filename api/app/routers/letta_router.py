@router.post("/chat")
async def chat(request: LettaRequest):
    logger.info(f"Processing chat request for NPC {request.npc_id}")
    
    response = await process_chat(request)
    logger.info(f"Generated response for NPC {request.npc_id}")
    logger.debug(f"Response details: {response}")  # Keep details at debug level 