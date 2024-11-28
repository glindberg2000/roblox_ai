import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from .conversation_managerV2 import ConversationManagerV2

logger = logging.getLogger("ella_app")

class CleanupTasks:
    def __init__(self, conversation_manager: ConversationManagerV2):
        self.conversation_manager = conversation_manager
        self.cleanup_interval = 300  # 5 minutes
        self.task: Optional[asyncio.Task] = None
        self.last_cleanup = datetime.now()

    async def start_cleanup_task(self):
        """Start the background cleanup task"""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._cleanup_loop())
            logger.info("Started conversation cleanup task")

    async def stop_cleanup_task(self):
        """Stop the background cleanup task"""
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped conversation cleanup task")

    async def _cleanup_loop(self):
        """Main cleanup loop"""
        while True:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _perform_cleanup(self):
        """Perform the actual cleanup operations"""
        try:
            start_time = datetime.now()
            cleaned = self.conversation_manager.cleanup_expired()
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Cleanup completed: removed {cleaned} expired conversations "
                f"in {duration:.2f} seconds"
            )
            self.last_cleanup = datetime.now()
        except Exception as e:
            logger.error(f"Error during conversation cleanup: {e}") 