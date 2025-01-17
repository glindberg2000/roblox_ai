import time
import logging
from typing import Dict, Any, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

logger = logging.getLogger("ella_app")

class ConversationMetrics:
    def __init__(self):
        self.total_conversations = 0
        self.successful_conversations = 0
        self.failed_conversations = 0
        self.average_duration = 0.0
        self.conversation_types: Dict[str, int] = {
            "npc_user": 0,
            "npc_npc": 0,
            "group": 0
        }

class ConversationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.metrics = ConversationMetrics()
        self.active_conversations: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next):
        # Only track conversation endpoints
        if not request.url.path.startswith("/robloxgpt/v"):
            return await call_next(request)

        start_time = time.time()
        conversation_id = None

        try:
            # Extract conversation details from request
            body = await request.json()
            conversation_id = body.get("conversation_id")
            conversation_type = body.get("conversation_type", "npc_user")

            # Track conversation start
            if conversation_id:
                self.active_conversations[conversation_id] = {
                    "start_time": start_time,
                    "type": conversation_type,
                    "message_count": 0
                }

            # Process the request
            response = await call_next(request)

            # Update metrics on successful response
            if response.status_code == 200:
                self._update_metrics(
                    conversation_id,
                    conversation_type,
                    start_time,
                    success=True
                )
            else:
                self._update_metrics(
                    conversation_id,
                    conversation_type,
                    start_time,
                    success=False
                )

            return response

        except Exception as e:
            logger.error(f"Error in conversation middleware: {e}")
            self._update_metrics(
                conversation_id,
                "unknown",
                start_time,
                success=False
            )
            raise

    def _update_metrics(
        self,
        conversation_id: Optional[str],
        conversation_type: str,
        start_time: float,
        success: bool
    ):
        """Update conversation metrics"""
        duration = time.time() - start_time
        
        # Update total counts
        self.metrics.total_conversations += 1
        if success:
            self.metrics.successful_conversations += 1
        else:
            self.metrics.failed_conversations += 1

        # Update conversation type counts
        if conversation_type in self.metrics.conversation_types:
            self.metrics.conversation_types[conversation_type] += 1

        # Update average duration
        current_avg = self.metrics.average_duration
        total = self.metrics.total_conversations
        self.metrics.average_duration = (
            (current_avg * (total - 1) + duration) / total
        )

        # Log metrics
        logger.info(
            f"Conversation processed - "
            f"ID: {conversation_id}, "
            f"Type: {conversation_type}, "
            f"Duration: {duration:.2f}s, "
            f"Success: {success}"
        )

        # Remove from active conversations if completed
        if conversation_id and conversation_id in self.active_conversations:
            conv_data = self.active_conversations.pop(conversation_id)
            logger.debug(
                f"Conversation completed - "
                f"ID: {conversation_id}, "
                f"Messages: {conv_data['message_count']}, "
                f"Duration: {duration:.2f}s"
            ) 