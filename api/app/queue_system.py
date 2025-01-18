import asyncio
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import logging
import time

logger = logging.getLogger("roblox_app")

class ChatQueueItem(BaseModel):
    npc_id: str
    message: str
    cluster_id: Optional[str]
    timestamp: float
    context: Optional[dict] = None

class SnapshotQueueItem(BaseModel):
    clusters: list
    human_context: dict
    timestamp: float

class QueueSystem:
    def __init__(self):
        self.chat_queue = asyncio.Queue()
        self.snapshot_queue = asyncio.Queue()
        self.is_running = False
        self.total_chats = 0
        self.total_snapshots = 0
        # Add rate tracking
        self.last_snapshot_time = time.time()
        self.snapshot_count_window = []  # Track timestamps in last second
        self.RATE_LIMIT = 1  # max snapshots per second
        self.RATE_WINDOW = 2.0  # window size in seconds
        
    async def enqueue_chat(self, item: ChatQueueItem):
        """Add chat request to queue"""
        await self.chat_queue.put(item)
        self.total_chats += 1
        logger.debug(f"Chat queued. Total: {self.total_chats}")
        
    async def enqueue_snapshot(self, item: SnapshotQueueItem):
        """Add snapshot to queue with rate limiting"""
        current_time = time.time()
        
        # Clean old timestamps (older than rate window)
        self.snapshot_count_window = [t for t in self.snapshot_count_window 
                                    if current_time - t < self.RATE_WINDOW]
        
        # Calculate current rate (snapshots per second)
        rate = len(self.snapshot_count_window) / self.RATE_WINDOW
        
        # Log if rate is high
        if rate > self.RATE_LIMIT:
            logger.warning(f"High snapshot rate detected: {rate:.1f}/sec")
            
        # Add current timestamp and enqueue
        self.snapshot_count_window.append(current_time)
        await self.snapshot_queue.put(item)
        self.total_snapshots += 1
        
        # Log every 10 snapshots instead of 100
        if self.total_snapshots % 10 == 0:
            logger.info(f"Snapshot queued. Total: {self.total_snapshots}, Current rate: {rate:.1f}/sec")
        
    def get_queue_sizes(self) -> Dict[str, int]:
        """Get current queue sizes and rate info"""
        current_rate = len(self.snapshot_count_window)
        return {
            "total_chats": self.total_chats,
            "total_snapshots": self.total_snapshots,
            "current_snapshot_rate": current_rate,
            "queue_age_seconds": time.time() - self.last_snapshot_time
        }

# Global queue system instance
queue_system = QueueSystem() 