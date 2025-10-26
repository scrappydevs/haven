"""
Production-Grade Thread Pool for CV Workers
Replaces ad-hoc thread creation with managed executor service
"""
import asyncio
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional, Callable
import time
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

MAX_CV_WORKERS = 50  # Maximum concurrent CV processing threads
MAX_AGENT_WORKERS = 20  # Maximum concurrent agent analysis threads
THREAD_KEEPALIVE_SECONDS = 300  # Thread idle timeout


# ============================================================================
# MANAGED BROADCAST QUEUE
# ============================================================================

class BroadcastQueue:
    """
    Thread-safe queue for broadcasting frames without creating event loops
    Uses a single persistent event loop in a dedicated thread
    """
    
    def __init__(self):
        self.queue = asyncio.Queue(maxsize=1000)
        self.loop = None
        self.thread = None
        self._shutdown = threading.Event()
    
    def start(self):
        """Start the broadcast worker thread"""
        if self.thread is None or not self.thread.is_alive():
            self._shutdown.clear()
            self.thread = threading.Thread(
                target=self._run_loop,
                daemon=False,  # Non-daemon for graceful shutdown
                name="BroadcastWorker"
            )
            self.thread.start()
            logger.info("✅ Broadcast worker started")
    
    def _run_loop(self):
        """Run the event loop in this thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._broadcast_worker())
        except Exception as e:
            logger.error(f"Broadcast worker error: {e}")
        finally:
            self.loop.close()
    
    async def _broadcast_worker(self):
        """Process broadcast queue"""
        while not self._shutdown.is_set():
            try:
                # Wait for broadcast task with timeout
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                coro, callback = task
                
                # Execute the broadcast coroutine
                try:
                    result = await coro
                    if callback:
                        callback(result)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Broadcast worker exception: {e}")
    
    def schedule_broadcast(self, coro, callback: Optional[Callable] = None):
        """
        Schedule a broadcast coroutine to be executed
        Non-blocking, safe to call from any thread
        """
        if self.loop and self.loop.is_running():
            # Use thread-safe call
            asyncio.run_coroutine_threadsafe(
                self.queue.put((coro, callback)),
                self.loop
            )
        else:
            logger.warning("Broadcast loop not running, skipping broadcast")
    
    def shutdown(self, timeout: float = 5.0):
        """Graceful shutdown of broadcast worker"""
        logger.info("Shutting down broadcast worker...")
        self._shutdown.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
            if self.thread.is_alive():
                logger.warning("Broadcast worker did not shutdown cleanly")
            else:
                logger.info("✅ Broadcast worker stopped")


# ============================================================================
# WORKER POOL MANAGER
# ============================================================================

class WorkerPoolManager:
    """
    Manages thread pools for CV processing and agent analysis
    Replaces ad-hoc daemon thread creation with bounded executor services
    """
    
    def __init__(self):
        # Thread pools
        self.cv_executor = ThreadPoolExecutor(
            max_workers=MAX_CV_WORKERS,
            thread_name_prefix="CV-Worker"
        )
        self.agent_executor = ThreadPoolExecutor(
            max_workers=MAX_AGENT_WORKERS,
            thread_name_prefix="Agent-Worker"
        )
        
        # Track active workers
        self.active_cv_workers: Dict[str, Future] = {}
        self.active_agent_workers: Dict[str, Future] = {}
        
        # Worker stop flags
        self.worker_stop_flags: Dict[str, threading.Event] = {}
        
        # Broadcast queue
        self.broadcast_queue = BroadcastQueue()
        self.broadcast_queue.start()
        
        # Metrics
        self.total_cv_tasks = 0
        self.total_agent_tasks = 0
        self.cv_task_errors = 0
        self.agent_task_errors = 0
        
        logger.info(f"✅ Worker pool initialized: CV={MAX_CV_WORKERS}, Agent={MAX_AGENT_WORKERS}")
    
    # ========================================================================
    # CV WORKER MANAGEMENT
    # ========================================================================
    
    def start_cv_worker(self, patient_id: str, worker_func: Callable, *args, **kwargs) -> bool:
        """
        Start a CV worker for a patient using thread pool
        
        Args:
            patient_id: Patient identifier
            worker_func: Worker function to execute
            *args, **kwargs: Arguments to pass to worker
        
        Returns:
            bool: True if started successfully
        """
        if patient_id in self.active_cv_workers:
            logger.warning(f"CV worker already exists for {patient_id}")
            return False
        
        # Create stop flag
        self.worker_stop_flags[patient_id] = threading.Event()
        
        # Submit to thread pool
        try:
            future = self.cv_executor.submit(
                self._cv_worker_wrapper,
                patient_id,
                worker_func,
                *args,
                **kwargs
            )
            self.active_cv_workers[patient_id] = future
            self.total_cv_tasks += 1
            logger.info(f"✅ CV worker started for {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start CV worker for {patient_id}: {e}")
            self.cv_task_errors += 1
            return False
    
    def _cv_worker_wrapper(self, patient_id: str, worker_func: Callable, *args, **kwargs):
        """Wrapper for CV worker to handle errors"""
        try:
            worker_func(patient_id, *args, **kwargs)
        except Exception as e:
            logger.error(f"CV worker error for {patient_id}: {e}", exc_info=True)
            self.cv_task_errors += 1
        finally:
            # Cleanup
            if patient_id in self.active_cv_workers:
                del self.active_cv_workers[patient_id]
            logger.info(f"CV worker stopped for {patient_id}")
    
    def stop_cv_worker(self, patient_id: str, timeout: float = 2.0) -> bool:
        """
        Stop a CV worker gracefully
        
        Args:
            patient_id: Patient identifier
            timeout: Maximum time to wait for worker to stop
        
        Returns:
            bool: True if stopped successfully
        """
        if patient_id not in self.active_cv_workers:
            return True
        
        # Set stop flag
        if patient_id in self.worker_stop_flags:
            self.worker_stop_flags[patient_id].set()
        
        # Wait for future to complete
        future = self.active_cv_workers.get(patient_id)
        if future:
            try:
                future.result(timeout=timeout)
                logger.info(f"✅ CV worker stopped gracefully for {patient_id}")
                return True
            except Exception as e:
                logger.warning(f"CV worker stop timeout for {patient_id}: {e}")
                future.cancel()
                return False
        
        return True
    
    # ========================================================================
    # AGENT WORKER MANAGEMENT
    # ========================================================================
    
    def submit_agent_task(self, patient_id: str, task_func: Callable, *args, **kwargs) -> Optional[Future]:
        """
        Submit an agent analysis task to the thread pool
        
        Args:
            patient_id: Patient identifier
            task_func: Task function to execute
            *args, **kwargs: Arguments to pass to task
        
        Returns:
            Future or None if submission failed
        """
        try:
            future = self.agent_executor.submit(
                self._agent_task_wrapper,
                patient_id,
                task_func,
                *args,
                **kwargs
            )
            self.total_agent_tasks += 1
            return future
            
        except Exception as e:
            logger.error(f"Failed to submit agent task for {patient_id}: {e}")
            self.agent_task_errors += 1
            return None
    
    def _agent_task_wrapper(self, patient_id: str, task_func: Callable, *args, **kwargs):
        """Wrapper for agent task to handle errors"""
        try:
            return task_func(patient_id, *args, **kwargs)
        except Exception as e:
            logger.error(f"Agent task error for {patient_id}: {e}", exc_info=True)
            self.agent_task_errors += 1
            return None
    
    # ========================================================================
    # BROADCAST MANAGEMENT
    # ========================================================================
    
    def schedule_broadcast(self, coro, callback: Optional[Callable] = None):
        """
        Schedule a broadcast operation (thread-safe, non-blocking)
        
        Args:
            coro: Coroutine to execute for broadcast
            callback: Optional callback after broadcast completes
        """
        self.broadcast_queue.schedule_broadcast(coro, callback)
    
    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    
    def shutdown(self, wait: bool = True, timeout: float = 10.0):
        """
        Graceful shutdown of all workers
        
        Args:
            wait: Whether to wait for workers to complete
            timeout: Maximum time to wait
        """
        logger.info("🛑 Shutting down worker pools...")
        
        # Stop all CV workers
        for patient_id in list(self.active_cv_workers.keys()):
            self.stop_cv_worker(patient_id, timeout=2.0)
        
        # Shutdown executors
        self.cv_executor.shutdown(wait=wait, cancel_futures=not wait)
        self.agent_executor.shutdown(wait=wait, cancel_futures=not wait)
        
        # Shutdown broadcast queue
        self.broadcast_queue.shutdown(timeout=timeout)
        
        logger.info("✅ Worker pools shut down")
    
    # ========================================================================
    # METRICS
    # ========================================================================
    
    def get_metrics(self) -> dict:
        """Get worker pool metrics"""
        return {
            "cv_workers": {
                "active": len(self.active_cv_workers),
                "max": MAX_CV_WORKERS,
                "total_tasks": self.total_cv_tasks,
                "errors": self.cv_task_errors
            },
            "agent_workers": {
                "active": len([f for f in self.active_agent_workers.values() if not f.done()]),
                "max": MAX_AGENT_WORKERS,
                "total_tasks": self.total_agent_tasks,
                "errors": self.agent_task_errors
            },
            "broadcast_queue": {
                "size": self.broadcast_queue.queue.qsize() if self.broadcast_queue.queue else 0,
                "running": self.broadcast_queue.thread and self.broadcast_queue.thread.is_alive()
            }
        }
    
    def get_stop_flag(self, patient_id: str) -> Optional[threading.Event]:
        """Get stop flag for a worker"""
        return self.worker_stop_flags.get(patient_id)


# Global instance
worker_pool = WorkerPoolManager()

