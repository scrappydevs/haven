"""Pydantic models for wearable device data and vitals."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DeviceType(str, Enum):
    """Supported wearable device types."""
    APPLE_WATCH = "apple_watch"
    FITBIT = "fitbit"
    GARMIN = "garmin"
    OTHER = "other"


class PairingStatus(str, Enum):
    """Device pairing status."""
    PENDING = "pending"
    ACTIVE = "active"
    DISCONNECTED = "disconnected"
    UNPAIRED = "unpaired"
    EXPIRED = "expired"


class WearableVitals(BaseModel):
    """Real-time vitals data from wearable device."""
    device_id: str
    patient_id: str
    timestamp: datetime

    # Vitals (all optional - device may not support all metrics)
    heart_rate: Optional[int] = Field(None, ge=30, le=220, description="Heart rate in BPM")
    heart_rate_variability: Optional[float] = Field(None, ge=0, le=300, description="HRV in milliseconds")
    spo2: Optional[int] = Field(None, ge=70, le=100, description="Blood oxygen saturation percentage")
    respiratory_rate: Optional[int] = Field(None, ge=5, le=60, description="Breaths per minute")
    body_temperature: Optional[float] = Field(None, ge=35.0, le=42.0, description="Body temperature in Celsius")

    # Metadata
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Data quality score")
    battery_level: Optional[int] = Field(None, ge=0, le=100, description="Device battery percentage")
    is_active: bool = Field(True, description="Device is currently active/worn")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "WATCH-ABC123",
                "patient_id": "P-001",
                "timestamp": "2025-10-25T14:30:00Z",
                "heart_rate": 72,
                "heart_rate_variability": 45.3,
                "spo2": 98,
                "respiratory_rate": 16,
                "body_temperature": 37.2,
                "confidence": 0.95,
                "battery_level": 85,
                "is_active": True
            }
        }


class WearableVitalsBatch(BaseModel):
    """Batch upload of vitals (for offline sync)."""
    device_id: str
    vitals: List[WearableVitals]


class DeviceInfo(BaseModel):
    """Device information for pairing."""
    device_type: DeviceType = DeviceType.APPLE_WATCH
    model: Optional[str] = Field(None, description="Device model (e.g., 'Apple Watch Series 9')")
    os_version: Optional[str] = Field(None, description="Operating system version")
    device_name: Optional[str] = Field(None, description="User-friendly device name")


class DevicePairingRequest(BaseModel):
    """Request to initiate device pairing."""
    patient_id: str


class DevicePairingResponse(BaseModel):
    """Response with pairing code and QR data."""
    pairing_code: str = Field(..., min_length=6, max_length=6, description="6-digit pairing code")
    device_id: str = Field(..., description="Generated device ID")
    expires_at: datetime = Field(..., description="Code expiration time (5 minutes)")

    class Config:
        json_schema_extra = {
            "example": {
                "pairing_code": "123456",
                "device_id": "WATCH-ABC123",
                "expires_at": "2025-10-25T14:35:00Z"
            }
        }


class DevicePairingComplete(BaseModel):
    """Request to complete pairing from device."""
    pairing_code: str = Field(..., min_length=6, max_length=6)
    device_info: DeviceInfo


class DevicePairingCompleteResponse(BaseModel):
    """Response after successful pairing."""
    device_id: str
    patient_id: str
    status: PairingStatus
    paired_at: datetime


class WearableDevice(BaseModel):
    """Complete device information."""
    id: str
    patient_id: Optional[str]
    device_type: DeviceType
    device_id: str
    device_name: Optional[str]

    pairing_status: PairingStatus
    paired_at: Optional[datetime]
    last_sync_at: Optional[datetime]
    is_online: bool

    model: Optional[str]
    os_version: Optional[str]
    created_at: datetime


class WearableDeviceStatus(BaseModel):
    """Real-time device status for dashboard."""
    device_id: str
    patient_id: str
    is_online: bool
    last_sync_at: Optional[datetime]
    battery_level: Optional[int]
    signal_strength: Optional[str] = Field(None, description="WiFi/cellular signal")

    # Latest vitals summary
    latest_heart_rate: Optional[int]
    latest_spo2: Optional[int]
    vitals_updated_at: Optional[datetime]


class WearableVitalsQuery(BaseModel):
    """Query parameters for historical vitals."""
    patient_id: str
    start_time: datetime
    end_time: datetime
    device_id: Optional[str] = None
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to retrieve")


class WearableAlert(BaseModel):
    """Alert generated from wearable vitals."""
    patient_id: str
    device_id: str
    alert_type: str  # "low_spo2", "high_hr", "low_battery", etc.
    severity: str  # "critical", "high", "medium", "low"
    message: str
    vitals_snapshot: WearableVitals
    timestamp: datetime
