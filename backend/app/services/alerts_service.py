"""
Service layer for querying and managing alerts from Supabase
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.supabase_client import supabase
from app.models.handoff_forms import AlertInfo, AlertSeverity, AlertStatus, AlertType
import logging
import json

logger = logging.getLogger(__name__)


def _parse_alert_metadata(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Parse metadata field from JSON string to dict if needed"""
    if isinstance(alert.get('metadata'), str):
        try:
            alert['metadata'] = json.loads(alert['metadata'])
        except:
            alert['metadata'] = {}
    elif alert.get('metadata') is None:
        alert['metadata'] = {}
    return alert


class AlertsService:
    """Service for querying alerts from Supabase"""

    @staticmethod
    def get_alert_by_id(alert_id: str) -> Optional[AlertInfo]:
        """Get a single alert by ID"""
        try:
            response = supabase.table("alerts").select("*").eq("id", alert_id).execute()

            if response.data and len(response.data) > 0:
                alert = _parse_alert_metadata(response.data[0])
                return AlertInfo(**alert)
            return None
        except Exception as e:
            logger.error(f"Error fetching alert {alert_id}: {e}")
            return None

    @staticmethod
    def get_alerts_by_patient(
        patient_id: str,
        status_filter: Optional[List[AlertStatus]] = None,
        severity_filter: Optional[List[AlertSeverity]] = None,
        include_resolved: bool = False,
        limit: Optional[int] = None
    ) -> List[AlertInfo]:
        """Get all alerts for a specific patient with optional filters"""
        try:
            query = supabase.table("alerts").select("*").eq("patient_id", patient_id)

            # Filter by status
            if status_filter:
                status_values = [s.value for s in status_filter]
                query = query.in_("status", status_values)
            elif not include_resolved:
                # By default exclude resolved and dismissed
                query = query.in_("status", ["active", "acknowledged"])

            # Filter by severity
            if severity_filter:
                severity_values = [s.value for s in severity_filter]
                query = query.in_("severity", severity_values)

            # Order by triggered_at descending (most recent first)
            query = query.order("triggered_at", desc=True)

            # Apply limit if specified
            if limit:
                query = query.limit(limit)

            response = query.execute()

            if response.data:
                return [AlertInfo(**_parse_alert_metadata(alert)) for alert in response.data]
            return []
        except Exception as e:
            logger.error(f"Error fetching alerts for patient {patient_id}: {e}")
            return []

    @staticmethod
    def get_alerts_by_ids(alert_ids: List[str]) -> List[AlertInfo]:
        """Get multiple alerts by their IDs"""
        try:
            response = supabase.table("alerts").select("*").in_("id", alert_ids).execute()

            if response.data:
                return [AlertInfo(**_parse_alert_metadata(alert)) for alert in response.data]
            return []
        except Exception as e:
            logger.error(f"Error fetching alerts by IDs: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_recent_alerts(
        hours: int = 24,
        severity_filter: Optional[List[AlertSeverity]] = None,
        status_filter: Optional[List[AlertStatus]] = None,
        alert_type_filter: Optional[List[AlertType]] = None
    ) -> List[AlertInfo]:
        """Get all recent alerts within specified hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            cutoff_iso = cutoff_time.isoformat()

            query = supabase.table("alerts").select("*").gte("triggered_at", cutoff_iso)

            if severity_filter:
                severity_values = [s.value for s in severity_filter]
                query = query.in_("severity", severity_values)

            if status_filter:
                status_values = [s.value for s in status_filter]
                query = query.in_("status", status_values)

            if alert_type_filter:
                type_values = [t.value for t in alert_type_filter]
                query = query.in_("alert_type", type_values)

            query = query.order("triggered_at", desc=True)

            response = query.execute()

            if response.data:
                return [AlertInfo(**_parse_alert_metadata(alert)) for alert in response.data]
            return []
        except Exception as e:
            logger.error(f"Error fetching recent alerts: {e}")
            return []

    @staticmethod
    def get_unhandled_alerts() -> List[AlertInfo]:
        """Get all active alerts that haven't been acknowledged"""
        try:
            response = (
                supabase.table("alerts")
                .select("*")
                .eq("status", "active")
                .order("severity", desc=True)  # Critical first
                .order("triggered_at", desc=True)
                .execute()
            )

            if response.data:
                return [AlertInfo(**_parse_alert_metadata(alert)) for alert in response.data]
            return []
        except Exception as e:
            logger.error(f"Error fetching unhandled alerts: {e}")
            return []

    @staticmethod
    def get_critical_alerts(
        include_acknowledged: bool = True
    ) -> List[AlertInfo]:
        """Get all critical and high severity alerts"""
        try:
            query = (
                supabase.table("alerts")
                .select("*")
                .in_("severity", ["critical", "high"])
            )

            if not include_acknowledged:
                query = query.eq("status", "active")

            query = query.order("triggered_at", desc=True)

            response = query.execute()

            if response.data:
                return [AlertInfo(**_parse_alert_metadata(alert)) for alert in response.data]
            return []
        except Exception as e:
            logger.error(f"Error fetching critical alerts: {e}")
            return []

    @staticmethod
    def get_patient_info(patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient information from patients table"""
        try:
            response = (
                supabase.table("patients")
                .select("*")
                .eq("patient_id", patient_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching patient info for {patient_id}: {e}")
            return None

    @staticmethod
    def get_room_info(room_id: str) -> Optional[Dict[str, Any]]:
        """Get room information from rooms table"""
        try:
            response = (
                supabase.table("rooms")
                .select("*")
                .eq("room_id", room_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching room info for {room_id}: {e}")
            return None

    @staticmethod
    def get_alerts_requiring_handoff() -> List[AlertInfo]:
        """
        Get alerts that require handoff form generation.
        Criteria: All active or acknowledged alerts that are critical/high severity,
        or any new alerts from the last hour.
        """
        try:
            # Get critical/high alerts that are active or acknowledged
            critical_response = (
                supabase.table("alerts")
                .select("*")
                .in_("severity", ["critical", "high"])
                .in_("status", ["active", "acknowledged"])
                .order("triggered_at", desc=True)
                .execute()
            )

            # Get all recent alerts from last hour
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            cutoff_iso = cutoff_time.isoformat()

            recent_response = (
                supabase.table("alerts")
                .select("*")
                .gte("triggered_at", cutoff_iso)
                .order("triggered_at", desc=True)
                .execute()
            )

            alerts_dict = {}

            # Combine and deduplicate
            if critical_response.data:
                for alert in critical_response.data:
                    parsed_alert = _parse_alert_metadata(alert)
                    alerts_dict[alert["id"]] = AlertInfo(**parsed_alert)

            if recent_response.data:
                for alert in recent_response.data:
                    parsed_alert = _parse_alert_metadata(alert)
                    alerts_dict[alert["id"]] = AlertInfo(**parsed_alert)

            return list(alerts_dict.values())
        except Exception as e:
            logger.error(f"Error fetching alerts requiring handoff: {e}")
            return []


# Create singleton instance
alerts_service = AlertsService()
