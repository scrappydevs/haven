"""Service for managing wearable devices and vitals."""

import uuid
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from supabase import Client

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from models.wearable import (
    WearableVitals,
    WearableDevice,
    DeviceInfo,
    DevicePairingResponse,
    PairingStatus,
    DeviceType,
    WearableDeviceStatus
)


class WearableService:
    """Handles wearable device operations."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def generate_pairing_code(self) -> str:
        """Generate a unique 6-digit pairing code."""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    def generate_device_id(self) -> str:
        """Generate a unique device ID."""
        return f"WATCH-{uuid.uuid4().hex[:8].upper()}"

    async def initiate_pairing(self, patient_id: str) -> DevicePairingResponse:
        """
        Initiate device pairing by generating a code.

        Args:
            patient_id: Patient to pair device with

        Returns:
            DevicePairingResponse with code and device_id
        """
        pairing_code = self.generate_pairing_code()
        device_id = self.generate_device_id()
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        # Create pending device record
        device_data = {
            "device_id": device_id,
            "patient_id": patient_id,
            "device_type": DeviceType.APPLE_WATCH.value,
            "pairing_code": pairing_code,
            "pairing_status": PairingStatus.PENDING.value,
            "is_online": False,
            "created_at": datetime.utcnow().isoformat()
        }

        result = self.supabase.table("wearable_devices").insert(device_data).execute()

        return DevicePairingResponse(
            pairing_code=pairing_code,
            device_id=device_id,
            expires_at=expires_at
        )

    async def complete_pairing(self, pairing_code: str, device_info: DeviceInfo) -> Dict[str, Any]:
        """
        Complete device pairing using the code.

        Args:
            pairing_code: 6-digit code from dashboard
            device_info: Device information from watch

        Returns:
            Device information including patient_id

        Raises:
            ValueError: If code is invalid or expired
        """
        # Find device with matching code
        result = self.supabase.table("wearable_devices")\
            .select("*")\
            .eq("pairing_code", pairing_code)\
            .eq("pairing_status", PairingStatus.PENDING.value)\
            .execute()

        if not result.data or len(result.data) == 0:
            raise ValueError("Invalid or expired pairing code")

        device = result.data[0]

        # Check expiration (5 minutes)
        created_at = datetime.fromisoformat(device["created_at"].replace('Z', '+00:00'))
        if datetime.utcnow() > created_at + timedelta(minutes=5):
            # Mark as expired
            self.supabase.table("wearable_devices")\
                .update({"pairing_status": PairingStatus.EXPIRED.value})\
                .eq("id", device["id"])\
                .execute()
            raise ValueError("Pairing code has expired")

        # Update device with pairing info
        update_data = {
            "pairing_status": PairingStatus.ACTIVE.value,
            "paired_at": datetime.utcnow().isoformat(),
            "is_online": True,
            "model": device_info.model,
            "os_version": device_info.os_version,
            "device_name": device_info.device_name,
            "pairing_code": None  # Clear code after use
        }

        self.supabase.table("wearable_devices")\
            .update(update_data)\
            .eq("id", device["id"])\
            .execute()

        return {
            "device_id": device["device_id"],
            "patient_id": device["patient_id"],
            "status": PairingStatus.ACTIVE.value,
            "paired_at": update_data["paired_at"]
        }

    async def check_pairing_status(self, pairing_code: str) -> Optional[Dict[str, Any]]:
        """
        Check if a pairing code has been completed.

        Args:
            pairing_code: 6-digit code to check

        Returns:
            Device info if paired, None if still pending
        """
        result = self.supabase.table("wearable_devices")\
            .select("*")\
            .eq("pairing_code", pairing_code)\
            .execute()

        if result.data and len(result.data) > 0:
            device = result.data[0]
            return {
                "status": device["pairing_status"],
                "device_id": device["device_id"],
                "patient_id": device["patient_id"]
            }

        # Code might have been cleared after successful pairing
        # Try to find recently paired device
        result = self.supabase.table("wearable_devices")\
            .select("*")\
            .eq("pairing_status", PairingStatus.ACTIVE.value)\
            .order("paired_at", desc=True)\
            .limit(1)\
            .execute()

        if result.data and len(result.data) > 0:
            device = result.data[0]
            paired_at = datetime.fromisoformat(device["paired_at"].replace('Z', '+00:00'))
            # If paired within last minute, assume it's from this code
            if datetime.utcnow() - paired_at < timedelta(minutes=1):
                return {
                    "status": PairingStatus.ACTIVE.value,
                    "device_id": device["device_id"],
                    "patient_id": device["patient_id"]
                }

        return None

    async def unpair_device(self, device_id: str) -> bool:
        """
        Unpair a device from patient.

        Args:
            device_id: Device to unpair

        Returns:
            True if successful
        """
        update_data = {
            "pairing_status": PairingStatus.UNPAIRED.value,
            "unpaired_at": datetime.utcnow().isoformat(),
            "is_online": False
        }

        result = self.supabase.table("wearable_devices")\
            .update(update_data)\
            .eq("device_id", device_id)\
            .execute()

        return len(result.data) > 0

    async def store_vitals(self, vitals: WearableVitals) -> bool:
        """
        Store wearable vitals in database.

        Args:
            vitals: Vitals data to store

        Returns:
            True if successful
        """
        vitals_data = {
            "patient_id": vitals.patient_id,
            "device_id": vitals.device_id,
            "device_type": "apple_watch",
            "heart_rate": vitals.heart_rate,
            "heart_rate_variability": vitals.heart_rate_variability,
            "spo2": vitals.spo2,
            "respiratory_rate": vitals.respiratory_rate,
            "body_temperature": vitals.body_temperature,
            "timestamp": vitals.timestamp.isoformat(),
            "confidence": vitals.confidence,
            "battery_level": vitals.battery_level,
            "is_active": vitals.is_active
        }

        result = self.supabase.table("wearable_vitals").insert(vitals_data).execute()

        # Update device last_sync_at
        self.supabase.table("wearable_devices")\
            .update({
                "last_sync_at": datetime.utcnow().isoformat(),
                "is_online": True
            })\
            .eq("device_id", vitals.device_id)\
            .execute()

        return len(result.data) > 0

    async def get_patient_devices(self, patient_id: str) -> List[WearableDevice]:
        """
        Get all devices for a patient.

        Args:
            patient_id: Patient ID

        Returns:
            List of devices
        """
        result = self.supabase.table("wearable_devices")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .order("created_at", desc=True)\
            .execute()

        devices = []
        for row in result.data:
            device = WearableDevice(
                id=row["id"],
                patient_id=row["patient_id"],
                device_type=DeviceType(row["device_type"]),
                device_id=row["device_id"],
                device_name=row.get("device_name"),
                pairing_status=PairingStatus(row["pairing_status"]),
                paired_at=datetime.fromisoformat(row["paired_at"].replace('Z', '+00:00')) if row.get("paired_at") else None,
                last_sync_at=datetime.fromisoformat(row["last_sync_at"].replace('Z', '+00:00')) if row.get("last_sync_at") else None,
                is_online=row["is_online"],
                model=row.get("model"),
                os_version=row.get("os_version"),
                created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
            )
            devices.append(device)

        return devices

    async def get_latest_vitals(self, patient_id: str, device_id: Optional[str] = None) -> Optional[WearableVitals]:
        """
        Get most recent vitals for a patient.

        Args:
            patient_id: Patient ID
            device_id: Optional specific device ID

        Returns:
            Latest vitals or None
        """
        query = self.supabase.table("wearable_vitals")\
            .select("*")\
            .eq("patient_id", patient_id)

        if device_id:
            query = query.eq("device_id", device_id)

        result = query.order("timestamp", desc=True).limit(1).execute()

        if not result.data or len(result.data) == 0:
            return None

        row = result.data[0]
        return WearableVitals(
            device_id=row["device_id"],
            patient_id=row["patient_id"],
            timestamp=datetime.fromisoformat(row["timestamp"].replace('Z', '+00:00')),
            heart_rate=row.get("heart_rate"),
            heart_rate_variability=row.get("heart_rate_variability"),
            spo2=row.get("spo2"),
            respiratory_rate=row.get("respiratory_rate"),
            body_temperature=row.get("body_temperature"),
            confidence=row.get("confidence", 1.0),
            battery_level=row.get("battery_level"),
            is_active=row.get("is_active", True)
        )

    async def get_vitals_history(
        self,
        patient_id: str,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[str] = None
    ) -> List[WearableVitals]:
        """
        Get historical vitals within time range.

        Args:
            patient_id: Patient ID
            start_time: Start of time range
            end_time: End of time range
            device_id: Optional specific device ID

        Returns:
            List of vitals
        """
        query = self.supabase.table("wearable_vitals")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .gte("timestamp", start_time.isoformat())\
            .lte("timestamp", end_time.isoformat())

        if device_id:
            query = query.eq("device_id", device_id)

        result = query.order("timestamp", desc=True).execute()

        vitals_list = []
        for row in result.data:
            vitals = WearableVitals(
                device_id=row["device_id"],
                patient_id=row["patient_id"],
                timestamp=datetime.fromisoformat(row["timestamp"].replace('Z', '+00:00')),
                heart_rate=row.get("heart_rate"),
                heart_rate_variability=row.get("heart_rate_variability"),
                spo2=row.get("spo2"),
                respiratory_rate=row.get("respiratory_rate"),
                body_temperature=row.get("body_temperature"),
                confidence=row.get("confidence", 1.0),
                battery_level=row.get("battery_level"),
                is_active=row.get("is_active", True)
            )
            vitals_list.append(vitals)

        return vitals_list

    async def get_device_status(self, device_id: str) -> Optional[WearableDeviceStatus]:
        """
        Get real-time device status.

        Args:
            device_id: Device ID

        Returns:
            Device status or None
        """
        # Get device info
        device_result = self.supabase.table("wearable_devices")\
            .select("*")\
            .eq("device_id", device_id)\
            .execute()

        if not device_result.data or len(device_result.data) == 0:
            return None

        device = device_result.data[0]

        # Get latest vitals
        vitals_result = self.supabase.table("wearable_vitals")\
            .select("*")\
            .eq("device_id", device_id)\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()

        latest_vitals = vitals_result.data[0] if vitals_result.data else None

        return WearableDeviceStatus(
            device_id=device_id,
            patient_id=device["patient_id"],
            is_online=device["is_online"],
            last_sync_at=datetime.fromisoformat(device["last_sync_at"].replace('Z', '+00:00')) if device.get("last_sync_at") else None,
            battery_level=latest_vitals.get("battery_level") if latest_vitals else None,
            latest_heart_rate=latest_vitals.get("heart_rate") if latest_vitals else None,
            latest_spo2=latest_vitals.get("spo2") if latest_vitals else None,
            vitals_updated_at=datetime.fromisoformat(latest_vitals["timestamp"].replace('Z', '+00:00')) if latest_vitals else None
        )
