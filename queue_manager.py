"""Download queue manager with parallel processing."""
import asyncio
from typing import Optional, Dict, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    """Represents a download task."""
    url: str
    user_id: int
    chat_id: int
    message_id: int
    timestamp: datetime


class DownloadQueue:
    """Manages download queue with parallel processing."""
    
    def __init__(self, max_size: int, parallel_workers: int):
        """Initialize download queue.
        
        Args:
            max_size: Maximum queue size
            parallel_workers: Number of parallel download workers
        """
        self.max_size = max_size
        self.parallel_workers = parallel_workers
        self.queue = asyncio.Queue(maxsize=max_size)
        self.active_downloads: Dict[int, DownloadTask] = {}
        self.workers = []
        self.running = False
    
    async def add_task(self, task: DownloadTask) -> bool:
        """Add task to queue.
        
        Args:
            task: Download task to add
            
        Returns:
            True if added, False if queue is full
        """
        try:
            self.queue.put_nowait(task)
            logger.info(f"Task added to queue: {task.url} for user {task.user_id}")
            return True
        except asyncio.QueueFull:
            logger.warning(f"Queue full, cannot add task: {task.url}")
            return False
    
    def is_full(self) -> bool:
        """Check if queue is full.
        
        Returns:
            True if queue is full
        """
        return self.queue.full()
    
    def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            Number of tasks in queue
        """
        return self.queue.qsize()
    
    def get_active_count(self) -> int:
        """Get number of active downloads.
        
        Returns:
            Number of active downloads
        """
        return len(self.active_downloads)
    
    async def start_workers(self, process_func: Callable):
        """Start worker tasks.
        
        Args:
            process_func: Async function to process each task
        """
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(i, process_func))
            for i in range(self.parallel_workers)
        ]
        logger.info(f"Started {self.parallel_workers} download workers")
    
    async def stop_workers(self):
        """Stop all worker tasks."""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []
        logger.info("All download workers stopped")
    
    async def _worker(self, worker_id: int, process_func: Callable):
        """Worker task that processes downloads from queue.
        
        Args:
            worker_id: Worker identifier
            process_func: Function to process each task
        """
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                
                # Mark as active
                task_id = id(task)
                self.active_downloads[task_id] = task
                
                logger.info(f"Worker {worker_id} processing: {task.url}")
                
                try:
                    # Process the task
                    await process_func(task)
                except Exception as e:
                    logger.error(f"Worker {worker_id} error processing {task.url}: {e}", exc_info=True)
                finally:
                    # Remove from active downloads
                    if task_id in self.active_downloads:
                        del self.active_downloads[task_id]
                    
                    # Mark task as done
                    self.queue.task_done()
                    logger.info(f"Worker {worker_id} completed: {task.url}")
                    
            except asyncio.TimeoutError:
                # No task available, continue waiting
                continue
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} unexpected error: {e}", exc_info=True)
        
        logger.info(f"Worker {worker_id} stopped")
