"""
Production Health Checks and System Monitoring
Comprehensive health status for all subsystems
"""
import time
import psutil
import threading
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# HEALTH STATUS TYPES
# ============================================================================

@dataclass
class SubsystemHealth:
    """Health status for a single subsystem"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy", "unknown"
    message: str
    latency_ms: float = 0
    last_check: float = 0
    details: dict = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "last_check": datetime.fromtimestamp(self.last_check).isoformat(),
            "details": self.details or {}
        }


# ============================================================================
# HEALTH CHECK MANAGER
# ============================================================================

class HealthCheckManager:
    """
    Comprehensive health monitoring for all system components
    
    Checks:
    - System resources (CPU, memory, disk)
    - Database connectivity (Supabase)
    - WebSocket connections
    - CV worker threads
    - Agent processing
    - External services (Agentverse, Vonage)
    """
    
    def __init__(self):
        self.subsystem_health: Dict[str, SubsystemHealth] = {}
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    # ========================================================================
    # INDIVIDUAL HEALTH CHECKS
    # ========================================================================
    
    def check_system_resources(self) -> SubsystemHealth:
        """Check CPU, memory, and disk usage"""
        start = time.time()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status
            status = "healthy"
            issues = []
            
            if cpu_percent > 90:
                status = "degraded"
                issues.append(f"High CPU: {cpu_percent}%")
            elif cpu_percent > 95:
                status = "unhealthy"
                issues.append(f"Critical CPU: {cpu_percent}%")
            
            if memory.percent > 85:
                status = "degraded" if status == "healthy" else status
                issues.append(f"High memory: {memory.percent}%")
            elif memory.percent > 95:
                status = "unhealthy"
                issues.append(f"Critical memory: {memory.percent}%")
            
            if disk.percent > 90:
                status = "degraded" if status == "healthy" else status
                issues.append(f"Low disk: {disk.percent}% used")
            
            message = "; ".join(issues) if issues else "All resources within normal ranges"
            
            return SubsystemHealth(
                name="system_resources",
                status=status,
                message=message,
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time(),
                details={
                    "cpu_percent": round(cpu_percent, 1),
                    "memory_percent": round(memory.percent, 1),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": round(disk.percent, 1),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                }
            )
            
        except Exception as e:
            return SubsystemHealth(
                name="system_resources",
                status="unknown",
                message=f"Failed to check system resources: {e}",
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time()
            )
    
    def check_database(self, supabase) -> SubsystemHealth:
        """Check Supabase database connectivity"""
        start = time.time()
        
        if not supabase:
            return SubsystemHealth(
                name="database",
                status="degraded",
                message="Supabase not configured (using fallback mode)",
                latency_ms=0,
                last_check=time.time()
            )
        
        try:
            # Simple ping query
            response = supabase.table("patients").select("patient_id").limit(1).execute()
            latency = (time.time() - start) * 1000
            
            status = "healthy"
            if latency > 500:
                status = "degraded"
            elif latency > 2000:
                status = "unhealthy"
            
            return SubsystemHealth(
                name="database",
                status=status,
                message=f"Connected (latency: {latency:.0f}ms)",
                latency_ms=latency,
                last_check=time.time(),
                details={
                    "latency_ms": round(latency, 2),
                    "connected": True
                }
            )
            
        except Exception as e:
            return SubsystemHealth(
                name="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)[:100]}",
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time()
            )
    
    def check_websocket_connections(self, manager) -> SubsystemHealth:
        """Check WebSocket connection health"""
        start = time.time()
        
        try:
            streamer_count = len(manager.streamers) if hasattr(manager, 'streamers') else 0
            viewer_count = len(manager.viewers) if hasattr(manager, 'viewers') else 0
            
            status = "healthy"
            message = f"{streamer_count} streams, {viewer_count} viewers"
            
            # Check for overload
            if streamer_count > 40:  # 80% of max (50)
                status = "degraded"
                message += " (approaching capacity)"
            
            if viewer_count > 160:  # 80% of max (200)
                status = "degraded" if status == "healthy" else status
                message += " (high viewer count)"
            
            return SubsystemHealth(
                name="websocket_connections",
                status=status,
                message=message,
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time(),
                details={
                    "active_streamers": streamer_count,
                    "active_viewers": viewer_count
                }
            )
            
        except Exception as e:
            return SubsystemHealth(
                name="websocket_connections",
                status="unknown",
                message=f"Failed to check WebSocket status: {e}",
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time()
            )
    
    def check_cv_workers(self, manager) -> SubsystemHealth:
        """Check CV worker thread health"""
        start = time.time()
        
        try:
            worker_threads = getattr(manager, 'worker_threads', {})
            active_workers = sum(1 for t in worker_threads.values() if t.is_alive())
            total_workers = len(worker_threads)
            
            status = "healthy"
            message = f"{active_workers} active CV workers"
            
            # Check for stuck workers
            if total_workers > 0 and active_workers < total_workers:
                status = "degraded"
                message += f" ({total_workers - active_workers} stopped/stuck)"
            
            if active_workers > 40:  # 80% of max
                status = "degraded" if status == "healthy" else status
                message += " (high worker count)"
            
            return SubsystemHealth(
                name="cv_workers",
                status=status,
                message=message,
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time(),
                details={
                    "active_workers": active_workers,
                    "total_workers": total_workers
                }
            )
            
        except Exception as e:
            return SubsystemHealth(
                name="cv_workers",
                status="unknown",
                message=f"Failed to check CV workers: {e}",
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time()
            )
    
    def check_agent_service(self, fetch_health_agent) -> SubsystemHealth:
        """Check Fetch.ai health agent status"""
        start = time.time()
        
        try:
            if not fetch_health_agent.enabled:
                return SubsystemHealth(
                    name="agent_service",
                    status="degraded",
                    message="uAgents not available (using fallback analysis)",
                    latency_ms=0,
                    last_check=time.time()
                )
            
            patient_count = len(fetch_health_agent.patients)
            alert_count = len([a for a in fetch_health_agent.alerts if a.get("severity") in ["CRITICAL", "WARNING"]])
            
            status = "healthy"
            message = f"Monitoring {patient_count} patients, {alert_count} active alerts"
            
            if patient_count > 40:
                status = "degraded"
                message += " (high patient load)"
            
            return SubsystemHealth(
                name="agent_service",
                status=status,
                message=message,
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time(),
                details={
                    "enabled": fetch_health_agent.enabled,
                    "patients_monitored": patient_count,
                    "active_alerts": alert_count
                }
            )
            
        except Exception as e:
            return SubsystemHealth(
                name="agent_service",
                status="unknown",
                message=f"Failed to check agent service: {e}",
                latency_ms=(time.time() - start) * 1000,
                last_check=time.time()
            )
    
    # ========================================================================
    # AGGREGATE HEALTH CHECK
    # ========================================================================
    
    def check_all_subsystems(self, supabase=None, manager=None, fetch_health_agent=None) -> Dict[str, SubsystemHealth]:
        """Run all health checks and return results"""
        with self._lock:
            # System resources
            self.subsystem_health["system_resources"] = self.check_system_resources()
            
            # Database
            if supabase:
                self.subsystem_health["database"] = self.check_database(supabase)
            
            # WebSocket connections
            if manager:
                self.subsystem_health["websocket_connections"] = self.check_websocket_connections(manager)
                self.subsystem_health["cv_workers"] = self.check_cv_workers(manager)
            
            # Agent service
            if fetch_health_agent:
                self.subsystem_health["agent_service"] = self.check_agent_service(fetch_health_agent)
            
            return self.subsystem_health.copy()
    
    def get_overall_status(self) -> Dict:
        """Get overall system health status"""
        with self._lock:
            subsystems = list(self.subsystem_health.values())
            
            if not subsystems:
                return {
                    "status": "unknown",
                    "message": "No health checks run yet"
                }
            
            # Aggregate status
            unhealthy_count = sum(1 for s in subsystems if s.status == "unhealthy")
            degraded_count = sum(1 for s in subsystems if s.status == "degraded")
            
            if unhealthy_count > 0:
                status = "unhealthy"
                message = f"{unhealthy_count} subsystem(s) unhealthy"
            elif degraded_count > 0:
                status = "degraded"
                message = f"{degraded_count} subsystem(s) degraded"
            else:
                status = "healthy"
                message = "All subsystems operational"
            
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            uptime_hours = uptime_seconds / 3600
            
            return {
                "status": status,
                "message": message,
                "uptime_hours": round(uptime_hours, 2),
                "uptime_seconds": round(uptime_seconds, 1),
                "subsystems": {name: health.to_dict() for name, health in self.subsystem_health.items()},
                "timestamp": datetime.utcnow().isoformat()
            }


# Global instance
health_monitor = HealthCheckManager()

