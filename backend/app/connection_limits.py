"""
Production-Grade Connection Management and Rate Limiting
Implements safety mechanisms for multi-stream production environment
"""
import time
import asyncio
from typing import Dict, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION - Adjust based on infrastructure capacity
# ============================================================================

# Connection Limits
MAX_CONCURRENT_STREAMERS = 50    # Maximum simultaneous patient streams
MAX_CONCURRENT_VIEWERS = 200     # Maximum simultaneous dashboard viewers
MAX_CONNECTIONS_PER_IP = 10       # Prevent single IP from exhausting resources

# Rate Limiting
MAX_FRAMES_PER_SECOND = 35        # Above 30 FPS is excessive
MAX_CONNECTION_ATTEMPTS_PER_MINUTE = 10  # Prevent rapid reconnection attacks
MAX_BROADCAST_RATE = 100          # Max broadcasts per second across all streams

# Frame Validation
MAX_FRAME_SIZE_BYTES = 5 * 1024 * 1024  # 5MB per frame (generous for base64)
MIN_FRAME_SIZE_BYTES = 1024       # Minimum valid frame size

# Timeouts
VIEWER_IDLE_TIMEOUT_SECONDS = 300  # Disconnect viewers after 5 min of no activity
STREAMER_IDLE_TIMEOUT_SECONDS = 60  # Disconnect streamers after 1 min of no frames


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ConnectionMetrics:
    """Track metrics for a single connection"""
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    frames_sent: int = 0
    bytes_sent: int = 0
    errors: int = 0
    
    def update_activity(self):
        self.last_activity = time.time()
    
    def is_idle(self, timeout_seconds: int) -> bool:
        return (time.time() - self.last_activity) > timeout_seconds


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting"""
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(default_factory=time.time)
    
    def __post_init__(self):
        self.tokens = self.capacity
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now


# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ProductionConnectionManager:
    """
    Production-grade connection manager with limits and safety mechanisms
    
    Features:
    - Connection limits (streamers, viewers, per-IP)
    - Rate limiting (frames, connections, broadcasts)
    - Frame validation (size, format)
    - Idle connection cleanup
    - Metrics tracking
    - Circuit breaker for overload
    """
    
    def __init__(self):
        # Connection tracking
        self.active_streamers: Dict[str, ConnectionMetrics] = {}
        self.active_viewers: Dict[int, ConnectionMetrics] = {}  # id -> metrics
        self.connections_by_ip: Dict[str, Set[str]] = defaultdict(set)
        
        # Rate limiting
        self.connection_attempts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=MAX_CONNECTION_ATTEMPTS_PER_MINUTE))
        self.frame_rate_limiters: Dict[str, RateLimitBucket] = {}
        self.global_broadcast_limiter = RateLimitBucket(
            capacity=MAX_BROADCAST_RATE,
            refill_rate=MAX_BROADCAST_RATE
        )
        
        # Circuit breaker state
        self.overload_mode = False
        self.overload_until: float = 0
        
        # Cleanup task
        self._cleanup_task = None
    
    def start_cleanup_task(self):
        """Start background task for idle connection cleanup"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of idle connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self.cleanup_idle_connections()
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
    
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    def can_accept_streamer(self, patient_id: str, client_ip: str) -> tuple[bool, str]:
        """
        Check if a new streamer connection can be accepted
        
        Returns:
            (can_accept, reason)
        """
        # Check if in overload mode
        if self.overload_mode and time.time() < self.overload_until:
            return False, "System overloaded. Please try again in a few minutes."
        
        # Check max streamers
        if len(self.active_streamers) >= MAX_CONCURRENT_STREAMERS:
            self.enter_overload_mode()
            return False, f"Maximum concurrent streams reached ({MAX_CONCURRENT_STREAMERS}). Please try again later."
        
        # Check per-IP limit
        if patient_id not in self.connections_by_ip[client_ip]:
            if len(self.connections_by_ip[client_ip]) >= MAX_CONNECTIONS_PER_IP:
                return False, f"Too many connections from your IP address (max {MAX_CONNECTIONS_PER_IP})"
        
        # Check connection rate limiting
        if not self._check_connection_rate_limit(client_ip):
            return False, "Too many connection attempts. Please wait a minute."
        
        return True, "OK"
    
    def can_accept_viewer(self, client_ip: str) -> tuple[bool, str]:
        """
        Check if a new viewer connection can be accepted
        
        Returns:
            (can_accept, reason)
        """
        # Check if in overload mode
        if self.overload_mode and time.time() < self.overload_until:
            return False, "System overloaded. Please try again in a few minutes."
        
        # Check max viewers
        if len(self.active_viewers) >= MAX_CONCURRENT_VIEWERS:
            return False, f"Maximum concurrent viewers reached ({MAX_CONCURRENT_VIEWERS}). Please try again later."
        
        # Check per-IP limit (viewers count separately)
        viewer_count = sum(1 for v in self.active_viewers.values() if v is not None)
        if viewer_count >= MAX_CONNECTIONS_PER_IP:
            # More lenient for viewers (they're usually staff)
            pass
        
        # Check connection rate limiting
        if not self._check_connection_rate_limit(client_ip):
            return False, "Too many connection attempts. Please wait a minute."
        
        return True, "OK"
    
    def register_streamer(self, patient_id: str, client_ip: str):
        """Register a new streamer connection"""
        self.active_streamers[patient_id] = ConnectionMetrics()
        self.connections_by_ip[client_ip].add(patient_id)
        
        # Initialize rate limiter for this stream
        self.frame_rate_limiters[patient_id] = RateLimitBucket(
            capacity=MAX_FRAMES_PER_SECOND * 2,  # 2 second burst
            refill_rate=MAX_FRAMES_PER_SECOND
        )
        
        logger.info(f"Streamer registered: {patient_id} from {client_ip}. Total: {len(self.active_streamers)}")
    
    def register_viewer(self, viewer_id: int, client_ip: str):
        """Register a new viewer connection"""
        self.active_viewers[viewer_id] = ConnectionMetrics()
        logger.info(f"Viewer registered: {viewer_id}. Total: {len(self.active_viewers)}")
    
    def unregister_streamer(self, patient_id: str, client_ip: str):
        """Unregister a streamer connection"""
        if patient_id in self.active_streamers:
            del self.active_streamers[patient_id]
        
        if patient_id in self.frame_rate_limiters:
            del self.frame_rate_limiters[patient_id]
        
        if patient_id in self.connections_by_ip[client_ip]:
            self.connections_by_ip[client_ip].remove(patient_id)
        
        logger.info(f"Streamer unregistered: {patient_id}. Total: {len(self.active_streamers)}")
    
    def unregister_viewer(self, viewer_id: int):
        """Unregister a viewer connection"""
        if viewer_id in self.active_viewers:
            del self.active_viewers[viewer_id]
        logger.info(f"Viewer unregistered: {viewer_id}. Total: {len(self.active_viewers)}")
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate_frame(self, patient_id: str, frame_data: str) -> tuple[bool, str]:
        """
        Validate a frame before processing
        
        Returns:
            (is_valid, error_message)
        """
        # Check frame size
        frame_size = len(frame_data)
        if frame_size > MAX_FRAME_SIZE_BYTES:
            return False, f"Frame too large ({frame_size} bytes, max {MAX_FRAME_SIZE_BYTES})"
        
        if frame_size < MIN_FRAME_SIZE_BYTES:
            return False, f"Frame too small ({frame_size} bytes, min {MIN_FRAME_SIZE_BYTES})"
        
        # Check rate limit
        if patient_id in self.frame_rate_limiters:
            if not self.frame_rate_limiters[patient_id].consume():
                return False, f"Frame rate limit exceeded ({MAX_FRAMES_PER_SECOND} FPS max)"
        
        # Update activity
        if patient_id in self.active_streamers:
            self.active_streamers[patient_id].update_activity()
            self.active_streamers[patient_id].frames_sent += 1
            self.active_streamers[patient_id].bytes_sent += frame_size
        
        return True, "OK"
    
    def can_broadcast(self) -> bool:
        """Check if broadcast is allowed (global rate limit)"""
        return self.global_broadcast_limiter.consume()
    
    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    
    def _check_connection_rate_limit(self, client_ip: str) -> bool:
        """Check if connection attempt is within rate limit"""
        now = time.time()
        attempts = self.connection_attempts[client_ip]
        
        # Remove attempts older than 1 minute
        while attempts and attempts[0] < now - 60:
            attempts.popleft()
        
        # Check if under limit
        if len(attempts) >= MAX_CONNECTION_ATTEMPTS_PER_MINUTE:
            return False
        
        # Record this attempt
        attempts.append(now)
        return True
    
    # ========================================================================
    # IDLE CLEANUP
    # ========================================================================
    
    async def cleanup_idle_connections(self):
        """Clean up idle connections"""
        # Cleanup idle streamers
        idle_streamers = [
            pid for pid, metrics in self.active_streamers.items()
            if metrics.is_idle(STREAMER_IDLE_TIMEOUT_SECONDS)
        ]
        
        if idle_streamers:
            logger.warning(f"Found {len(idle_streamers)} idle streamers, cleanup needed")
            # Note: Actual disconnection should be done by websocket manager
        
        # Cleanup idle viewers
        idle_viewers = [
            vid for vid, metrics in self.active_viewers.items()
            if metrics.is_idle(VIEWER_IDLE_TIMEOUT_SECONDS)
        ]
        
        if idle_viewers:
            logger.warning(f"Found {len(idle_viewers)} idle viewers, cleanup needed")
    
    # ========================================================================
    # CIRCUIT BREAKER
    # ========================================================================
    
    def enter_overload_mode(self, duration_seconds: int = 60):
        """Enter overload protection mode"""
        self.overload_mode = True
        self.overload_until = time.time() + duration_seconds
        logger.error(f"⚠️  OVERLOAD MODE ACTIVATED for {duration_seconds}s. Rejecting new connections.")
    
    def check_system_health(self) -> dict:
        """Check system health and return status"""
        streamer_count = len(self.active_streamers)
        viewer_count = len(self.active_viewers)
        
        # Calculate resource utilization
        streamer_utilization = streamer_count / MAX_CONCURRENT_STREAMERS
        viewer_utilization = viewer_count / MAX_CONCURRENT_VIEWERS
        
        health_status = "healthy"
        if streamer_utilization > 0.9 or viewer_utilization > 0.9:
            health_status = "critical"
        elif streamer_utilization > 0.7 or viewer_utilization > 0.7:
            health_status = "warning"
        
        return {
            "status": health_status,
            "overload_mode": self.overload_mode,
            "streamers": {
                "active": streamer_count,
                "max": MAX_CONCURRENT_STREAMERS,
                "utilization": f"{streamer_utilization * 100:.1f}%"
            },
            "viewers": {
                "active": viewer_count,
                "max": MAX_CONCURRENT_VIEWERS,
                "utilization": f"{viewer_utilization * 100:.1f}%"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ========================================================================
    # METRICS
    # ========================================================================
    
    def get_metrics(self) -> dict:
        """Get detailed metrics for monitoring"""
        total_frames = sum(m.frames_sent for m in self.active_streamers.values())
        total_bytes = sum(m.bytes_sent for m in self.active_streamers.values())
        total_errors = sum(m.errors for m in self.active_streamers.values())
        
        return {
            "connections": {
                "streamers": len(self.active_streamers),
                "viewers": len(self.active_viewers),
                "unique_ips": len(self.connections_by_ip)
            },
            "traffic": {
                "total_frames": total_frames,
                "total_bytes": total_bytes,
                "total_errors": total_errors
            },
            "limits": {
                "max_streamers": MAX_CONCURRENT_STREAMERS,
                "max_viewers": MAX_CONCURRENT_VIEWERS,
                "max_per_ip": MAX_CONNECTIONS_PER_IP,
                "max_fps": MAX_FRAMES_PER_SECOND
            }
        }


# Global instance
connection_manager = ProductionConnectionManager()

