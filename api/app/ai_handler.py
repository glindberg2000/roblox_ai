# app/ai_handler.py

import asyncio
import logging
from typing import List, Dict, Any
from openai import OpenAI
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger("ella_app")

class NPCAction(BaseModel):
    type: str = Field(..., pattern="^(follow|unfollow|stop_talking|none)$")
    data: Dict[str, Any] = Field(default_factory=dict)

class NPCResponse(BaseModel):
    message: str
    action: NPCAction
    internal_state: Dict[str, Any] = Field(default_factory=dict)

class AIHandler:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.response_cache = {}
        self.max_parallel_requests = 5
        self.semaphore = asyncio.Semaphore(self.max_parallel_requests)

        # Define the response schema once
        self.response_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "npc_response",
                "description": "NPC response format including message and action",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The NPC's spoken response"
                        },
                        "action": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["follow", "unfollow", "stop_talking", "none"],
                                    "description": "The type of action to take"
                                },
                                "data": {
                                    "type": "object",
                                    "description": "Additional data for the action",
                                    "default": {}
                                }
                            },
                            "required": ["type"],
                            "additionalProperties": False
                        },
                        "internal_state": {
                            "type": "object",
                            "description": "NPC's internal state updates",
                            "default": {}
                        }
                    },
                    "required": ["message", "action"],
                    "additionalProperties": False
                }
            }
        }

    async def get_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        max_tokens: int = 200
    ) -> NPCResponse:
        """Get structured response from OpenAI"""
        try:
            async with self.semaphore:
                completion = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model="gpt-4o-mini",  # Update to newer model when available
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *messages
                    ],
                    max_tokens=max_tokens,
                    response_format=self.response_schema,
                    temperature=0.7
                )

                # Check for refusal
                if hasattr(completion.choices[0].message, 'refusal') and completion.choices[0].message.refusal:
                    logger.warning("AI refused to respond")
                    return NPCResponse(
                        message="I cannot respond to that request.",
                        action=NPCAction(type="none")
                    )

                # Check for incomplete response
                if completion.choices[0].finish_reason != "stop":
                    logger.warning(f"Response incomplete: {completion.choices[0].finish_reason}")
                    return NPCResponse(
                        message="I apologize, but I was unable to complete my response.",
                        action=NPCAction(type="none")
                    )

                # Parse the response into our Pydantic model
                response_data = completion.choices[0].message.content
                logger.debug(f"Raw AI response: {response_data}")
                
                return NPCResponse.parse_raw(response_data)

        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}", exc_info=True)
            return NPCResponse(
                message="Hello! How can I help you today?",
                action=NPCAction(type="none")
            )

    async def process_parallel_responses(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[NPCResponse]:
        """Process multiple requests in parallel"""
        tasks = [
            self.get_response(
                req["messages"],
                req["system_prompt"],
                req.get("max_tokens", 200)
            )
            for req in requests
        ]
        
        return await asyncio.gather(*tasks)