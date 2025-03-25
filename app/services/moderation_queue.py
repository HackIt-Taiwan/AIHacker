"""
Moderation Queue Service - 處理內容審核隊列

這個模塊提供一個隊列系統，用於處理大量的內容審核請求。
當審核請求超出API負荷時，系統會將請求放入隊列，確保所有請求最終都能被處理。
"""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Set

from app.config import (
    MODERATION_QUEUE_MAX_CONCURRENT,
    MODERATION_QUEUE_CHECK_INTERVAL,
    MODERATION_QUEUE_RETRY_INTERVAL,
    MODERATION_QUEUE_MAX_RETRIES
)

logger = logging.getLogger(__name__)

class ModerationQueue:
    """
    A queue system for handling moderation tasks.
    This helps prevent API rate limiting and ensures all messages are eventually processed.
    """
    
    def __init__(self, 
                 max_concurrent: int = MODERATION_QUEUE_MAX_CONCURRENT,
                 check_interval: float = MODERATION_QUEUE_CHECK_INTERVAL,
                 retry_interval: float = MODERATION_QUEUE_RETRY_INTERVAL,
                 max_retries: int = MODERATION_QUEUE_MAX_RETRIES):
        """
        Initialize the moderation queue.
        
        Args:
            max_concurrent: Maximum number of concurrent tasks
            check_interval: Interval in seconds to check the queue
            retry_interval: Interval in seconds to retry failed tasks
            max_retries: Maximum number of retries for failed tasks
        """
        self.queue = deque()
        self.processing = set()
        self.processed_count = 0
        self.failed_count = 0
        self.max_concurrent = max_concurrent
        self.check_interval = check_interval
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self.running = False
        self.last_status_log = 0
        
    async def start(self):
        """Start processing the queue in a background task"""
        if self.running:
            return
            
        self.running = True
        logger.info("Moderation queue service started")
        
        while self.running:
            await self._process_queue()
            await asyncio.sleep(self.check_interval)
            
    def add_moderation_task(self, task_func: Callable, task_data: Dict[str, Any], task_id: Optional[str] = None):
        """
        Add a moderation task to the queue.
        
        Args:
            task_func: The function to call to execute the task
            task_data: Data needed for the task
            task_id: Optional ID for the task (defaults to timestamp)
        """
        if task_id is None:
            task_id = f"task_{int(time.time())}_{len(self.queue)}"
            
        task = {
            "id": task_id,
            "func": task_func,
            "data": task_data,
            "retries": 0,
            "added_at": datetime.now().isoformat(),
            "last_attempt": None
        }
        
        self.queue.append(task)
        queue_size = len(self.queue)
        processing_count = len(self.processing)
        
        # Log status at most once every 10 seconds to avoid log spam
        current_time = time.time()
        if current_time - self.last_status_log > 10:
            logger.info(
                f"Added moderation task {task_id} to queue. Queue status: "
                f"{queue_size} queued, {processing_count} processing, "
                f"{self.processed_count} processed, {self.failed_count} failed"
            )
            self.last_status_log = current_time
            
    async def _process_queue(self):
        """Process tasks from the queue up to the concurrency limit"""
        if not self.queue:
            return
            
        # Log queue status every minute if there are pending tasks
        current_time = time.time()
        if self.queue and current_time - self.last_status_log > 60:
            logger.info(
                f"Queue status: {len(self.queue)} queued, {len(self.processing)} processing, "
                f"{self.processed_count} processed, {self.failed_count} failed"
            )
            self.last_status_log = current_time
            
        # Start tasks up to the concurrency limit
        while self.queue and len(self.processing) < self.max_concurrent:
            task = self.queue.popleft()
            task_id = task["id"]
            
            # Check if this is a retry attempt
            if task.get("last_attempt"):
                retry_num = task["retries"]
                logger.info(f"Retrying task {task_id} (attempt {retry_num + 1}/{self.max_retries})")
                
            self.processing.add(task_id)
            # Execute the task in the background
            asyncio.create_task(self._execute_task(task))
            
    async def _execute_task(self, task):
        """Execute a single moderation task"""
        task_id = task["id"]
        task_func = task["func"]
        task_data = task["data"]
        retries = task["retries"]
        
        task["last_attempt"] = datetime.now().isoformat()
        
        try:
            # Execute the task
            await task_func(**task_data)
            
            # Task completed successfully
            self.processed_count += 1
            logger.info(f"Successfully processed moderation task {task_id}")
            
        except Exception as e:
            # Log the failure
            logger.error(f"Failed to process moderation task {task_id}: {str(e)}", exc_info=True)
            
            # Check if we should retry
            if retries < self.max_retries:
                # Increment retry count and add back to queue
                task["retries"] = retries + 1
                # Wait before retrying
                await asyncio.sleep(self.retry_interval)
                self.queue.append(task)
                logger.info(f"Scheduled task {task_id} for retry ({retries + 1}/{self.max_retries})")
            else:
                # Max retries reached, mark as failed
                self.failed_count += 1
                logger.error(f"Task {task_id} failed after {self.max_retries} attempts")
        
        finally:
            # Remove from processing set
            if task_id in self.processing:
                self.processing.remove(task_id)
    
    def get_queue_status(self):
        """Get the current status of the queue"""
        return {
            "queue_size": len(self.queue),
            "processing": len(self.processing),
            "processed": self.processed_count,
            "failed": self.failed_count,
            "running": self.running
        }
    
    def stop(self):
        """Stop the queue processing"""
        self.running = False
        logger.info("Moderation queue service stopped")

# Create a global instance of the moderation queue
moderation_queue = ModerationQueue() 

async def start_moderation_queue(bot=None):
    """
    Start the global moderation queue instance.
    
    Args:
        bot: Optional Discord bot instance
    """
    logger.info("Starting global moderation queue service")
    await moderation_queue.start()
    return moderation_queue 