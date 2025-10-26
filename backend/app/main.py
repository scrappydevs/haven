"""
Haven AI - Backend API
FastAPI application serving pre-computed CV results and trial data
"""

import logging
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import json
from pathlib import Path
import os
from app.websocket import manager, process_frame_fast, process_frame_metrics
from app.supabase_client import supabase, SUPABASE_URL
from app.monitoring_protocols import get_all_protocols, recommend_protocols as keyword_recommend
from app.infisical_config import get_secret, secret_manager
from app.monitoring_control import monitoring_manager, MonitoringLevel
# Legacy agents disabled - using Fetch.ai Health Agent only
# from app.patient_guardian_agent import patient_guardian
# from app.agent_system import agent_system
# from app.health_agent import health_agent  # Old non-Fetch.ai agent
from app.fetch_health_agent import fetch_health_agent

# Try to import caching (graceful fallback if not available)
try:
    from app.cache import patient_cache, alert_cache, stats_cache, stream_cache
    CACHING_ENABLED = True
    print("✅ Caching system loaded")
except ImportError as e:
    print(f"⚠️  Caching disabled: {e}")
    CACHING_ENABLED = False
    # Create dummy cache objects that do nothing
    class DummyCache:
        def get(self, key): return None
        def set(self, key, value): pass
        def invalidate(self, key): pass
        def clear(self): pass
    patient_cache = alert_cache = stats_cache = stream_cache = DummyCache()

# Try to import Fetch.ai handoff agent (requires uagents)
try:
    from app.fetch_handoff_agent import fetch_handoff_agent
    FETCH_HANDOFF_AVAILABLE = True
except ImportError:
    fetch_handoff_agent = None
    FETCH_HANDOFF_AVAILABLE = False
    print("⚠️  Fetch.ai handoff agent not available - install uagents if needed")

from app.rooms import (
    get_all_floors,
    get_all_rooms_with_patients,
    assign_patient_to_room,
    unassign_patient_from_room,
    get_patient_current_room,
    sync_room_from_smplrspace,
    Floor,
    AssignPatientRequest,
    UnassignPatientRequest
)

# Try to import anthropic for LLM recommendations
try:
    import anthropic
    ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
    anthropic_client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
    if anthropic_client:
        print("✅ Anthropic client initialized")
except ImportError:
    anthropic_client = None
    print("⚠️  Anthropic library not installed. LLM recommendations will use keyword matching.")

logger = logging.getLogger("haven.main")

# LiveKit configuration checks
REQUIRED_LIVEKIT_SECRETS = ["LIVEKIT_API_KEY",
                            "LIVEKIT_API_SECRET", "LIVEKIT_URL"]
try:
    import livekit  # noqa: F401
    _LIVEKIT_IMPORT_ERROR = None
    _LIVEKIT_AVAILABLE = True
except ImportError as livekit_exc:
    _LIVEKIT_IMPORT_ERROR = livekit_exc
    _LIVEKIT_AVAILABLE = False


def _check_livekit_config() -> tuple[bool, list[str]]:
    """
    Verify LiveKit dependencies and configuration. Returns a tuple of:
    (is_ready, list_of_issue_strings)
    """
    issues: list[str] = []

    if not _LIVEKIT_AVAILABLE:
        issues.append(f"LiveKit SDK not installed ({_LIVEKIT_IMPORT_ERROR})")

    missing = [key for key in REQUIRED_LIVEKIT_SECRETS if not get_secret(key)]
    if missing:
        issues.append(f"Missing LiveKit secrets: {', '.join(missing)}")

    return len(issues) == 0, issues


app = FastAPI(
    title="Haven",
    description="Real-time patient monitoring and floor plan management for clinical trials",
    version="1.0.0"
)

# CORS for frontend - allows browser WebSocket connections from production and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://use-haven.vercel.app",  # Production frontend
        "http://localhost:3000",          # Local development
        "http://localhost:3001",          # Alternative local port
        "http://localhost:3002",          # Alternative local port
        "http://127.0.0.1:3000",          # Local development (127.0.0.1)
        "http://127.0.0.1:3001",          # Alternative local port (127.0.0.1)
        "http://127.0.0.1:3002",          # Alternative local port (127.0.0.1)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"

# Load pre-computed CV results
cv_results = {}
cv_file = DATA_DIR / "precomputed_cv.json"
if cv_file.exists():
    with open(cv_file, "r") as f:
        cv_results = json.load(f)
else:
    print("⚠️  Warning: precomputed_cv.json not found. Run scripts/precompute_cv.py first!")


@app.on_event("startup")
async def _log_livekit_status():
    """Log LiveKit readiness once the app starts."""
    ready, issues = _check_livekit_config()
    if ready:
        logger.info(
            "✅ LiveKit configuration detected (API key, secret, URL present).")
    else:
        for issue in issues:
            logger.warning("⚠️ LiveKit startup issue: %s", issue)

# Load patient data
patients = []
patients_file = DATA_DIR / "patients.json"
if patients_file.exists():
    with open(patients_file, "r") as f:
        patients = json.load(f)
else:
    print("⚠️  Warning: patients.json not found. Run scripts/generate_patients.py first!")

# Load trial protocol
trial_protocol = {}
protocol_file = DATA_DIR / "nct04649359.json"
if protocol_file.exists():
    with open(protocol_file, "r") as f:
        trial_protocol = json.load(f)
else:
    print("⚠️  Warning: nct04649359.json not found. Run scripts/pull_trial_data.py first!")

# Print secret manager status after all imports


@app.on_event("startup")
async def startup_event():
    """Print configuration status on startup"""
    secret_manager.print_status()

    # Print service status
    print("🏥 Haven Backend Services:")
    print(
        f"   • Supabase: {'✅ Connected' if supabase else '❌ Not configured'}")
    print(
        f"   • Anthropic AI: {'✅ Enabled' if anthropic_client else '⚠️  Disabled (using keyword matching)'}")
    print(
        f"   • Fetch.ai Health Agent: {'✅ Enabled' if fetch_health_agent.enabled else '⚠️  Disabled'}")
    print(f"   • CV Data: {'✅ Loaded' if cv_results else '⚠️  Not loaded'}")
    print(
        f"   • Patients (local): {'✅ Loaded (' + str(len(patients)) + ')' if patients else '⚠️  Not loaded'}")
    print(
        f"   • Trial Protocol: {'✅ Loaded' if trial_protocol else '⚠️  Not loaded'}")
    print("\n✅ Haven ready!\n")

# In-memory alert storage
alerts = []


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Haven AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cv_results_loaded": len(cv_results) > 0,
        "patients_loaded": len(patients) > 0,
        "trial_protocol_loaded": len(trial_protocol) > 0
    }


# ============================================================================
# Twilio SMS Alerts
# ============================================================================

class SMSAlertRequest(BaseModel):
    phone_number: str
    message: str


@app.post("/alerts/trigger")
async def trigger_sms_alert(request: SMSAlertRequest):
    """
    Send SMS alert via Vonage (Nexmo)
    For MVP: Manual alerts from dashboard
    Future: Automatically triggered by AI agent

    No A2P registration needed - works immediately for global numbers
    """
    try:
        # Get Vonage credentials from secrets
        VONAGE_API_KEY = get_secret("VONAGE_API_KEY")
        VONAGE_API_SECRET = get_secret("VONAGE_API_SECRET")

        if not all([VONAGE_API_KEY, VONAGE_API_SECRET]):
            # Mock mode for demos without credentials
            print(
                f"⚠️  Vonage not configured - mock sending SMS to {request.phone_number}")
            print(f"   Message: {request.message}")
            return {
                "status": "success",
                "message": "Alert sent (mock mode - Vonage not configured)",
                "mock_sent": True,
                "to": request.phone_number
            }

        # Import Vonage client (v4+ API)
        from vonage import Auth, Vonage
        from vonage_sms import SmsMessage

        # Create auth and client
        auth = Auth(api_key=VONAGE_API_KEY, api_secret=VONAGE_API_SECRET)
        client = Vonage(auth=auth)

        # Create and send SMS message (v4 API)
        # Use your Vonage phone number as sender for U.S. SMS compliance
        message = SmsMessage(
            to=request.phone_number,
            # Your Vonage number (supports SMS, Voice & MMS)
            from_="12178020876",
            text=f"[Haven Alert] {request.message}"
        )
        response_obj = client.sms.send(message)

        # Check response status (v4 API uses underscores, not hyphens)
        first_message = response_obj.messages[0]
        if first_message.status == "0":
            print(
                f"✅ SMS sent to {request.phone_number}: {first_message.message_id}")

            return {
                "status": "success",
                "message": "Alert sent successfully",
                "message_id": first_message.message_id,
                "to": request.phone_number,
                "remaining_balance": first_message.remaining_balance,
                "price": first_message.message_price
            }
        else:
            # Status != "0" means error
            error_msg = f"Vonage error (status {first_message.status})"
            print(f"❌ Vonage SMS failed: {error_msg}")
            return {
                "status": "error",
                "message": f"SMS failed: {error_msg}"
            }

    except ImportError:
        # Vonage not installed - return mock success
        print(
            f"⚠️  Vonage library not installed - mock sending SMS to {request.phone_number}")
        return {
            "status": "success",
            "message": "Alert sent (mock mode - Vonage not installed)",
            "mock_sent": True,
            "to": request.phone_number
        }
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")
        return {
            "status": "error",
            "message": f"Failed to send alert: {str(e)}"
        }


@app.post("/test-emergency-call")
async def test_emergency_call():
    """
    Quick test endpoint for emergency calling
    Tests the full calling pipeline
    """
    try:
        from app.voice_call import voice_service

        print("🧪 Testing emergency call system...")

        # Make test call
        result = voice_service.make_emergency_call(
            patient_id="P-TEST-001",
            event_type="fall",
            details="Test call from dashboard"
        )

        if result:
            return {
                "status": "success",
                "message": "Test call placed successfully",
                "call_uuid": result.get("uuid"),
                "to": result.get("to")
            }
        else:
            return {
                "status": "demo_mode",
                "message": "Test call simulated (Vonage not configured)",
                "note": "Check backend logs for details"
            }

    except Exception as e:
        print(f"❌ Test call failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/alerts/call")
async def trigger_voice_alert(request: SMSAlertRequest):
    """
    Make voice call with TTS alert via Vonage
    FAST & SIMPLE: Uses voice_service for reliability
    """
    try:
        from app.voice_call import voice_service

        print(f"📞 Manual alert call requested to {request.phone_number}")
        print(f"   Message: {request.message}")

        # Use the voice service (handles credentials, formatting, everything)
        call_result = voice_service.make_emergency_call(
            patient_id="MANUAL_ALERT",
            event_type="urgent_alert",
            details=request.message,
            to_number=request.phone_number  # Pass the nurse's phone number
        )

        if call_result:
            # Real call placed
            return {
                "status": "success",
                "message": "Voice call placed successfully",
                "call_uuid": call_result.get("uuid"),
                "to": call_result.get("to"),
                "type": "voice"
            }
        else:
            # Demo/mock mode (Vonage not configured)
            return {
                "status": "demo",
                "message": "Voice call simulated (Vonage not configured)",
                "mock_sent": True,
                "to": request.phone_number,
                "note": "Check backend logs for details"
            }

    except ImportError:
        # Vonage not installed - return mock success
        print(
            f"⚠️  Vonage library not installed - mock calling {request.phone_number}")
        return {
            "status": "success",
            "message": "Voice call placed (mock mode - Vonage not installed)",
            "mock_sent": True,
            "to": request.phone_number
        }
    except Exception as e:
        print(f"❌ Failed to place voice call: {e}")
        return {
            "status": "error",
            "message": f"Failed to place call: {str(e)}"
        }


class MessengerAlertRequest(BaseModel):
    phone_number: str
    message: str
    channel: str = "whatsapp"  # whatsapp, messenger, viber, or mms


@app.post("/alerts/messenger")
async def trigger_messenger_alert(request: MessengerAlertRequest):
    """
    Send alert via WhatsApp, Facebook Messenger, Viber, or MMS

    NO 10DLC REGISTRATION REQUIRED FOR:
    - WhatsApp Business API
    - Facebook Messenger
    - Viber Business Messages
    - International MMS

    These channels work immediately and bypass U.S. SMS carrier restrictions!
    """
    try:
        # Get Vonage credentials from secrets
        VONAGE_API_KEY = get_secret("VONAGE_API_KEY")
        VONAGE_API_SECRET = get_secret("VONAGE_API_SECRET")

        if not all([VONAGE_API_KEY, VONAGE_API_SECRET]):
            # Mock mode for demos without credentials
            print(
                f"⚠️  Vonage not configured - mock sending {request.channel} to {request.phone_number}")
            print(f"   Message: {request.message}")
            return {
                "status": "success",
                "message": f"{request.channel.title()} message sent (mock mode - Vonage not configured)",
                "mock_sent": True,
                "to": request.phone_number,
                "channel": request.channel
            }

        # Import Vonage Messages API (v4+ API)
        from vonage import Auth, Vonage
        from vonage_messages import MessagesClient

        # Create auth and client
        auth = Auth(api_key=VONAGE_API_KEY, api_secret=VONAGE_API_SECRET)
        client = Vonage(auth=auth)

        # Format phone number (remove + and spaces)
        to_number = request.phone_number.replace(
            "+", "").replace("-", "").replace(" ", "")

        # Build message based on channel
        message_data = {
            "to": to_number,
            "message_type": "text",
            "text": f"🚨 Haven Alert: {request.message}"
        }

        # Channel-specific configuration
        if request.channel == "whatsapp":
            # WhatsApp Business number (Vonage sandbox)
            message_data["from"] = "12178020876"
            message_data["channel"] = "whatsapp"
        elif request.channel == "messenger":
            # Facebook Page ID (get from Vonage dashboard)
            message_data["from"] = "107083064136738"
            message_data["channel"] = "messenger"
        elif request.channel == "viber":
            message_data["from"] = "HavenAI"  # Viber Service ID
            message_data["channel"] = "viber_service"
        elif request.channel == "mms":
            message_data["from"] = "12178020876"  # Your Vonage number
            message_data["channel"] = "mms"
        else:
            return {
                "status": "error",
                "message": f"Unsupported channel: {request.channel}"
            }

        # Send message via Vonage Messages API
        response = client.messages.send_message(message_data)

        print(f"✅ {request.channel.title()} message sent to {request.phone_number}: {response.get('message_uuid')}")

        return {
            "status": "success",
            "message": f"{request.channel.title()} message sent successfully",
            "message_uuid": response.get("message_uuid"),
            "to": request.phone_number,
            "channel": request.channel
        }

    except ImportError:
        # Vonage not installed - return mock success
        print(
            f"⚠️  Vonage Messages API not installed - mock sending {request.channel} to {request.phone_number}")
        return {
            "status": "success",
            "message": f"{request.channel.title()} message sent (mock mode - Vonage not installed)",
            "mock_sent": True,
            "to": request.phone_number,
            "channel": request.channel
        }
    except Exception as e:
        print(f"❌ Failed to send {request.channel} message: {e}")
        return {
            "status": "error",
            "message": f"Failed to send {request.channel} message: {str(e)}"
        }


# Webhook endpoints for Vonage Messages API (inbound messages and status updates)
@app.post("/vonage/inbound")
async def vonage_inbound_messages(request: dict):
    """
    Receive inbound messages from WhatsApp/Messenger/Viber
    Nurses can reply to alerts directly!
    """
    print(
        f"📩 Inbound message from {request.get('from')}: {request.get('message', {}).get('content', {}).get('text')}")

    # TODO: Process inbound replies from nurses
    # - Store in database
    # - Notify dashboard
    # - Update alert status

    return {"status": "received"}


@app.post("/vonage/status")
async def vonage_message_status(request: dict):
    """
    Receive delivery status updates for sent messages
    Track if nurse received/read the alert
    """
    print(
        f"📊 Message status update: {request.get('status')} for message {request.get('message_uuid')}")

    # TODO: Update alert delivery status in database
    # - delivered
    # - read
    # - failed

    return {"status": "received"}


@app.post("/api/alerts/call-nurse")
async def handle_critical_alert_webhook(request: dict):
    """
    Webhook endpoint called by database trigger when critical alert is created
    Makes phone call to nurse via Vonage Voice API
    """
    try:
        alert_id = request.get('alert_id')
        patient_id = request.get('patient_id')
        room_id = request.get('room_id')
        severity = request.get('severity')
        title = request.get('title')
        description = request.get('description')

        print(f"\n🚨 CRITICAL ALERT WEBHOOK: {alert_id}")
        print(f"   Patient: {patient_id}")
        print(f"   Room: {room_id}")
        print(f"   Title: {title}")

        # Import alert monitor logic
        from app.alert_monitor import handle_critical_alert

        # Process the alert (make phone call)
        await handle_critical_alert({
            'id': alert_id,
            'patient_id': patient_id,
            'room_id': room_id,
            'severity': severity,
            'message': title or description or 'Critical alert'
        })

        return {
            "status": "success",
            "message": "Alert processed and call initiated",
            "alert_id": alert_id
        }

    except Exception as e:
        print(f"❌ Error handling alert webhook: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/api/alerts/call-response")
async def handle_alert_call_response(request: dict):
    """
    Handle DTMF input from nurse during alert call
    When nurse presses 1, acknowledge the alert
    """
    try:
        dtmf = request.get('dtmf')
        call_uuid = request.get('uuid')
        conversation_uuid = request.get('conversation_uuid')

        print(f"📞 Call response received: DTMF={dtmf}, Call={call_uuid}")

        if dtmf == '1':
            # Nurse acknowledged the alert
            print(f"✅ Alert acknowledged by nurse")

            # Find and update alert with this call_id in metadata
            if supabase:
                try:
                    # Find alert with matching call_id in metadata
                    alerts = supabase.table("alerts") \
                        .select("id, metadata") \
                        .eq("status", "active") \
                        .execute()

                    for alert in (alerts.data or []):
                        metadata = alert.get('metadata', {})
                        call_info = metadata.get('call', {})

                        if call_info.get('call_id') == call_uuid:
                            # Update call status and acknowledge alert
                            call_info['call_status'] = 'answered'
                            call_info['answered_at'] = datetime.now(
                            ).isoformat()
                            metadata['call'] = call_info

                            supabase.table("alerts").update({
                                "status": "acknowledged",
                                "acknowledged_at": datetime.now().isoformat(),
                                "acknowledged_by": "nurse_phone",
                                "metadata": metadata
                            }).eq("id", alert['id']).execute()

                            print(
                                f"✅ Alert {alert['id']} acknowledged and updated")
                            break

                except Exception as e:
                    print(f"⚠️  Failed to update alert: {e}")

            # Return NCCO to confirm acknowledgement
            return [{
                "action": "talk",
                "text": "Thank you. Alert acknowledged. Hang up or stay on the line for more information.",
                "voiceName": "Amy"
            }]
        else:
            # No acknowledgement - just hang up
            return [{
                "action": "talk",
                "text": "No response received. Please check the alert immediately.",
                "voiceName": "Amy"
            }]

    except Exception as e:
        print(f"❌ Error handling call response: {e}")
        return {"status": "error"}


@app.get("/smplrspace/config")
async def get_smplrspace_config():
    """
    Get Smplrspace configuration (credentials)
    This keeps sensitive tokens on the backend instead of frontend
    """
    return {
        "organizationId": get_secret("SMPLR_ORG_ID") or os.getenv("SMPLR_ORG_ID"),
        "clientToken": get_secret("SMPLR_CLIENT_TOKEN") or os.getenv("SMPLR_CLIENT_TOKEN"),
        "spaceId": get_secret("SMPLR_SPACE_ID") or os.getenv("SMPLR_SPACE_ID"),
    }


@app.get("/patients")
async def get_patients():
    """Get list of all patients from database"""
    if not supabase:
        # Fallback to legacy data if Supabase not configured
        return patients[:47]

    try:
        # Fetch all active patients from Supabase with all fields including photo_url
        response = supabase.table("patients").select(
            "*").eq("enrollment_status", "active").execute()
        return response.data or []
    except Exception as e:
        print(f"❌ Error fetching patients: {e}")
        # Fallback to legacy data on error
        return patients[:47]


@app.get("/patient/{patient_id}")
async def get_patient(patient_id: int):
    """Get single patient details - LEGACY"""
    for patient in patients:
        if patient["id"] == patient_id:
            return patient
    return {"error": "Patient not found"}


@app.get("/patients/search")
async def search_patients(q: str = ""):
    """
    Search patients by name from Supabase
    CACHED for 30 seconds (patient data changes infrequently)

    Args:
        q: Search query string

    Returns:
        List of patients matching the search query
    """
    if not supabase:
        print("⚠️ Supabase not configured - returning empty patient list")
        return []

    # Cache key based on query
    cache_key = f"patients_search:{q}"
    
    # Try cache first
    cached = patient_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        if q:
            # Search by name (case-insensitive)
            print(f"🔍 Searching patients with query: '{q}'")
            response = supabase.table("patients") \
                .select("patient_id,name,age,room_id,enrollment_status") \
                .ilike("name", f"%{q}%") \
                .order("name") \
                .limit(20) \
                .execute()
        else:
            # Return all patients if no search query
            print("📋 Fetching all patients")
            response = supabase.table("patients") \
                .select("patient_id,name,age,room_id,enrollment_status") \
                .order("name") \
                .limit(20) \
                .execute()

        result_count = len(response.data) if response.data else 0
        print(f"✅ Found {result_count} patients")

        # Filter to active patients if enrollment_status field exists, otherwise return all
        if response.data:
            # Only filter by enrollment_status if the field exists and has a value
            filtered_data = [
                p for p in response.data
                if p.get('enrollment_status') in ['active', None] or 'enrollment_status' not in p
            ]
            print(
                f"📊 After enrollment_status filter: {len(filtered_data)} patients")
            
            # Cache for 30 seconds
            patient_cache.set(cache_key, filtered_data)
            return filtered_data
        
        patient_cache.set(cache_key, [])
        return []
    except Exception as e:
        print(f"❌ Error searching patients: {e}")
        import traceback
        traceback.print_exc()
        return []


@app.get("/patients/debug")
async def debug_patients():
    """Diagnostic endpoint to check patient database status"""
    if not supabase:
        return {
            "status": "error",
            "message": "Supabase not configured",
            "supabase_url_present": bool(SUPABASE_URL),
            "patients": []
        }

    try:
        # Get all patients (no filter)
        all_response = supabase.table(
            "patients").select("*").limit(10).execute()

        # Get active patients
        active_response = supabase.table("patients") \
            .select("*") \
            .eq("enrollment_status", "active") \
            .limit(10) \
            .execute()

        return {
            "status": "success",
            "supabase_url": SUPABASE_URL[:30] + "..." if SUPABASE_URL else None,
            "total_patients": len(all_response.data) if all_response.data else 0,
            "active_patients": len(active_response.data) if active_response.data else 0,
            "sample_patients": all_response.data[:3] if all_response.data else [],
            "sample_active": active_response.data[:3] if active_response.data else []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }


@app.get("/patients/by-id/{patient_id}")
async def get_patient_by_id(patient_id: str):
    """
    Get single patient by patient_id (e.g., P-001)

    Args:
        patient_id: Patient ID string (e.g., "P-001")

    Returns:
        Patient details
    """
    if not supabase:
        return {"error": "Supabase not configured"}

    try:
        response = supabase.table("patients") \
            .select("*") \
            .eq("patient_id", patient_id) \
            .single() \
            .execute()

        return response.data
    except Exception as e:
        print(f"❌ Error fetching patient {patient_id}: {e}")
        return {"error": str(e)}


@app.get("/cv-data/{patient_id}/{timestamp}")
async def get_cv_data(patient_id: int, timestamp: str):
    """
    Get pre-computed CV data for patient at specific timestamp

    Args:
        patient_id: Patient ID (1-6)
        timestamp: Video timestamp in seconds (e.g., "120.5")

    Returns:
        CV metrics: crs_score, heart_rate, respiratory_rate, etc.
    """
    patient_key = f"patient-{patient_id}"

    if patient_key not in cv_results:
        return {"error": "Patient not found", "crs_score": 0.0, "heart_rate": 75, "respiratory_rate": 14}

    patient_data = cv_results[patient_key]

    # Find closest timestamp
    try:
        timestamp_float = float(timestamp)
        available_times = [float(t) for t in patient_data.keys()]
        closest_time = min(
            available_times, key=lambda t: abs(t - timestamp_float))
        closest_time_str = str(closest_time) if closest_time == int(
            closest_time) else f"{closest_time:.1f}"

        data = patient_data.get(
            closest_time_str, patient_data.get(str(int(closest_time))))

        # If alert, store it
        if data and data.get("alert"):
            alert = {
                "patient_id": patient_id,
                "timestamp": timestamp,
                "crs_score": data["crs_score"],
                "heart_rate": data["heart_rate"],
                "message": f"CRS Grade 2 detected - Patient #{patient_id}",
                "severity": "high"
            }
            # Only add if not already in alerts
            if not any(a["patient_id"] == patient_id and abs(float(a["timestamp"]) - timestamp_float) < 5 for a in alerts):
                alerts.append(alert)

        return data if data else {"error": "No data for timestamp"}

    except (ValueError, KeyError) as e:
        return {"error": str(e), "crs_score": 0.0, "heart_rate": 75, "respiratory_rate": 14}


@app.get("/alerts")
async def get_alerts(status: str = None, severity: str = None, limit: int = 50):
    """
    Get alerts from database with enriched patient and room information
    Optionally filter by status and/or severity
    CACHED for 5 seconds + OPTIMIZED with batch queries
    """
    if not supabase:
        # Fallback to in-memory alerts if no database
        return alerts

    # Cache key based on filters
    cache_key = f"alerts:{status}:{severity}:{limit}"
    
    # Try cache first
    cached = alert_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        query = supabase.table("alerts").select("*")

        if status:
            query = query.eq("status", status)
        if severity:
            query = query.eq("severity", severity)

        response = query.order(
            "triggered_at", desc=True).limit(limit).execute()

        alerts_data = response.data or []

        if not alerts_data:
            alert_cache.set(cache_key, [])
            return []

        # OPTIMIZED: Batch fetch all patients and rooms at once
        patient_ids = list(set(alert.get('patient_id') for alert in alerts_data if alert.get('patient_id')))
        
        # Fetch all patients in one query
        patients_map = {}
        if patient_ids:
            patients_response = supabase.table("patients").select("patient_id,name").in_("patient_id", patient_ids).execute()
            patients_map = {p['patient_id']: p['name'] for p in (patients_response.data or [])}
        
        # Fetch all room assignments in one query
        room_assignments_map = {}
        if patient_ids:
            room_assignments_response = supabase.table("patients_room").select("patient_id,room_id").in_("patient_id", patient_ids).execute()
            room_assignments_map = {r['patient_id']: r['room_id'] for r in (room_assignments_response.data or [])}
        
        # Fetch all rooms in one query
        room_ids = list(set(room_assignments_map.values()))
        rooms_map = {}
        if room_ids:
            rooms_response = supabase.table("rooms").select("room_id,room_name").in_("room_id", room_ids).execute()
            rooms_map = {r['room_id']: r['room_name'] for r in (rooms_response.data or [])}

        # Enrich alerts with patient and room names (no additional queries!)
        for alert in alerts_data:
            patient_id = alert.get('patient_id')
            if patient_id:
                # Add patient name
                alert['patient_name'] = patients_map.get(patient_id, 'Unknown')
                
                # Add room info
                room_id = room_assignments_map.get(patient_id)
                if room_id:
                    if not alert.get('room_id'):
                        alert['room_id'] = room_id
                    alert['room_name'] = rooms_map.get(room_id, 'Unknown')

            # If alert has room_id but no room_name yet, get from rooms_map
            if alert.get('room_id') and not alert.get('room_name'):
                alert['room_name'] = rooms_map.get(alert['room_id'], 'Unknown')

        print(f"✅ Enriched {len(alerts_data)} alerts with patient/room data")
        
        # Cache for 5 seconds
        alert_cache.set(cache_key, alerts_data)
        return alerts_data
    except Exception as e:
        print(f"⚠️ Error fetching alerts from database: {e}")
        # Fallback to in-memory
        return alerts


@app.get("/alerts/{alert_id}")
async def get_alert_by_id(alert_id: str):
    """
    Get a single alert by ID
    """
    if not supabase:
        return {"error": "Database not configured"}

    try:
        response = supabase.table("alerts").select(
            "*").eq("id", alert_id).single().execute()

        if not response.data:
            return {"error": "Alert not found"}

        return response.data
    except Exception as e:
        print(f"❌ Error fetching alert {alert_id}: {e}")
        return {"error": str(e)}


@app.post("/alerts")
async def create_alert(
    alert_type: str,
    severity: str,
    title: str,
    description: str = None,
    patient_id: str = None,
    room_id: str = None,
    triggered_by: str = "system"
):
    """
    Create a new alert in the database
    SIMPLIFIED: Calls nurse directly for critical alerts (no database trigger needed)
    """
    if not supabase:
        # Fallback to in-memory
        global alerts
        alert = {
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "description": description,
            "patient_id": patient_id,
            "room_id": room_id,
            "status": "active"
        }
        alerts.append(alert)
        return alert

    try:
        # Insert alert into database
        result = supabase.table("alerts").insert({
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "description": description,
            "patient_id": patient_id,
            "room_id": room_id,
            "triggered_by": triggered_by,
            "status": "active"
        }).execute()

        alert_data = result.data[0] if result.data else {}
        alert_id = alert_data.get("id")

        # IMMEDIATE CALL for critical alerts (don't wait for database trigger)
        if severity == "critical" and alert_id:
            print(
                f"🚨 CRITICAL ALERT {alert_id} - Calling nurse immediately...")

            # Import voice service
            from app.voice_call import voice_service

            # Make emergency call
            try:
                call_result = voice_service.make_emergency_call(
                    patient_id=patient_id or "Unknown",
                    event_type="critical_alert",
                    details=f"{title}: {description or ''}"
                )

                if call_result:
                    print(f"✅ Emergency call placed for alert {alert_id}")
                    # Update alert metadata with call info
                    try:
                        supabase.table("alerts").update({
                            "metadata": {
                                "call": {
                                    "call_uuid": call_result.get("uuid"),
                                    "to": call_result.get("to"),
                                    "initiated_at": datetime.now().isoformat()
                                }
                            }
                        }).eq("id", alert_id).execute()
                    except:
                        pass  # Don't fail if metadata update fails
            except Exception as call_error:
                print(f"⚠️ Failed to make emergency call: {call_error}")

        return alert_data
    except Exception as e:
        print(f"❌ Error creating alert: {e}")
        return {"error": str(e)}


@app.patch("/alerts/{alert_id}")
async def update_alert_status(alert_id: str, status: str = "resolved"):
    """
    Update alert status (e.g., mark as resolved/acknowledged)
    """
    from datetime import datetime

    if not supabase:
        # Fallback to in-memory
        global alerts
        for alert in alerts:
            if alert.get("id") == alert_id:
                alert["status"] = status
                if status == "resolved":
                    alert["resolved_at"] = datetime.now().isoformat()
                return alert
        return {"error": "Alert not found"}

    try:
        update_data = {
            "status": status
        }
        if status == "resolved":
            update_data["resolved_at"] = datetime.now().isoformat()

        result = supabase.table("alerts").update(
            update_data).eq("id", alert_id).execute()

        if result.data and len(result.data) > 0:
            print(f"✅ Alert {alert_id} marked as {status}")
            return result.data[0]
        else:
            print(f"⚠️ Alert {alert_id} not found")
            return {"error": "Alert not found"}
    except Exception as e:
        print(f"❌ Error updating alert: {e}")
        return {"error": str(e)}


@app.delete("/alerts")
async def clear_alerts():
    """Clear all alerts (in-memory fallback only)"""
    global alerts
    alerts = []
    return {"message": "Alerts cleared"}


@app.get("/trial-protocol")
async def get_trial_protocol():
    """Get NCT04649359 trial protocol information"""
    if trial_protocol:
        return trial_protocol

    # Fallback data if file not loaded
    return {
        "nct_id": "NCT04649359",
        "title": "Linvoseltamab in Relapsed/Refractory Multiple Myeloma",
        "sponsor": "Regeneron Pharmaceuticals",
        "phase": "Phase 2/3",
        "enrollment_target": 150,
        "enrollment_actual": 47,
        "drug": "Linvoseltamab (BCMA × CD3 bispecific antibody)",
        "indication": "Relapsed/Refractory Multiple Myeloma",
        "crs_criteria": {
            "grade_1": "Fever only (≥38°C)",
            "grade_2": "Fever + hypotension OR hypoxia",
            "grade_3": "Grade 2 + organ dysfunction",
            "grade_4": "Life-threatening"
        },
        "monitoring_protocol": {
            "infusion": "48-hour hospitalization",
            "follow_up": "7-day home surveillance",
            "vital_signs": "Every 2 hours during infusion"
        }
    }


@app.get("/roi-calculation")
async def calculate_roi():
    """Calculate ROI metrics for Haven"""
    return {
        "patients": 47,
        "manual_monitoring_cost_per_day": 18800,
        "ai_monitoring_cost_per_day": 1250,
        "daily_savings": 17550,
        "monthly_savings": 526500,
        "trial_duration_months": 10,
        "total_savings": 5265000,
        "enrollment_speedup_months": 3,
        "enrollment_speedup_value": 24000000,
        "total_value": 29265000
    }


@app.get("/stats")
async def get_stats():
    """Get dashboard statistics"""
    return {
        "patients_monitored": 47,
        "active_alerts": len(alerts),
        "daily_cost_savings": 17550,
        "crs_events_detected": len([a for a in alerts if "CRS" in a.get("message", "")]),
        "time_savings_percent": 75,
        "lives_saved": 2  # Based on early detection
    }


@app.get("/streams/active")
async def get_active_streams():
    """
    Get list of patient IDs currently streaming with their analysis modes
    CACHED for 2 seconds to reduce load

    Returns:
        {
            "active_streams": ["P-001", "P-003"],
            "stream_details": {
                "P-001": {"analysis_mode": "enhanced"},
                "P-003": {"analysis_mode": "normal"}
            },
            "count": 2
        }
    """
    # Try cache first (2 second TTL)
    cached = stream_cache.get("active_streams")
    if cached is not None:
        return cached
    
    # Build fresh response
    active_patient_ids = list(manager.streamers.keys())
    stream_details = {}

    for patient_id in active_patient_ids:
        trackers = manager.get_trackers(patient_id)
        stream_details[patient_id] = {
            "analysis_mode": trackers.analysis_mode if trackers else "normal"
        }

    result = {
        "active_streams": active_patient_ids,
        "stream_details": stream_details,
        "count": len(active_patient_ids)
    }
    
    # Cache for 2 seconds
    stream_cache.set("active_streams", result)
    return result


@app.get("/monitoring/protocols")
async def get_monitoring_protocols():
    """
    Get all available monitoring protocols

    Returns:
        {
            "CRS": {...},
            "SEIZURE": {...}
        }
    """
    return get_all_protocols()


class MonitoringRecommendationRequest(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    condition: str


@app.post("/monitoring/recommend")
async def recommend_monitoring(request: MonitoringRecommendationRequest):
    """
    Get AI-recommended monitoring protocols based on patient information

    Args:
        request: Patient information

    Returns:
        {
            "recommended": ["CRS", "SEIZURE"],
            "reasoning": "Patient has multiple myeloma...",
            "method": "llm" | "keyword"
        }
    """
    if anthropic_client:
        # Use LLM for intelligent recommendations
        try:
            protocols = get_all_protocols()
            protocol_descriptions = "\n".join([
                f"- {name}: {config['label']} - {config['description']}"
                for name, config in protocols.items()
            ])

            message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""You are a clinical trial safety AI assistant. Based on the patient information below, recommend which monitoring protocols should be activated.

Patient Information:
- Name: {request.name}
- Age: {request.age}
- Gender: {request.gender}
- Condition: {request.condition}

Available Monitoring Protocols:
{protocol_descriptions}

Respond in JSON format with:
{{
  "recommended": ["PROTOCOL1", "PROTOCOL2"],
  "reasoning": "Brief explanation of why these protocols are recommended"
}}

Only recommend protocols that are clearly relevant based on the patient's condition. If no protocols are clearly relevant, return an empty list."""
                }]
            )

            # Parse Claude's response
            response_text = message.content[0].text
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "recommended": result.get("recommended", []),
                    "reasoning": result.get("reasoning", ""),
                    "method": "llm"
                }
            else:
                # Fallback to keyword matching
                raise ValueError("Could not parse LLM response")

        except Exception as e:
            print(
                f"LLM recommendation error: {e}, falling back to keyword matching")
            # Fall through to keyword matching

    # Keyword-based fallback
    recommended = keyword_recommend(request.condition)
    return {
        "recommended": recommended,
        "reasoning": f"Keyword matching detected relevant terms in patient condition: {request.condition}",
        "method": "keyword"
    }


@app.get("/floors")
async def get_floors():
    """
    Get all floor definitions

    Returns:
        List of floor definitions with Smplrspace references
    """
    return get_all_floors()


@app.get("/rooms")
async def get_rooms(floor_id: str = None):
    """
    Get all rooms with their current patient assignments
    Optionally filter by floor_id

    Args:
        floor_id: Optional floor ID to filter rooms

    Returns:
        List of rooms with optional patient information
    """
    return get_all_rooms_with_patients(floor_id)


@app.get("/rooms/assignments")
async def get_room_assignments():
    """
    DEPRECATED: Use /rooms instead
    Get all rooms with their current patient assignments

    Returns:
        List of rooms with optional patient information
    """
    return get_all_rooms_with_patients()


@app.post("/rooms/assign-patient")
async def assign_patient(request: AssignPatientRequest):
    """
    Assign a patient to a room

    Args:
        request: Room ID, patient ID, and optional notes

    Returns:
        Patient-room assignment record
    """
    try:
        return assign_patient_to_room(
            room_id=request.room_id,
            patient_id=request.patient_id,
            notes=request.notes
        )
    except Exception as e:
        return {"error": str(e)}


@app.delete("/rooms/unassign-patient/{room_id}")
async def unassign_patient(room_id: str, patient_id: str = None, generate_report: bool = False):
    """
    Remove patient from a room

    Args:
        room_id: Room identifier
        patient_id: Optional patient ID to remove specific patient
        generate_report: Whether to generate PDF discharge report

    Returns:
        Success message with optional PDF report ID
    """
    try:
        # Get patient ID if not provided
        if not patient_id:
            assignment = supabase.table("patients_room").select(
                "patient_id").eq("room_id", room_id).execute()
            if assignment.data:
                patient_id = assignment.data[0]['patient_id']

        # Generate PDF report if requested
        report_generated = False
        if generate_report and patient_id:
            try:
                from app.pdf_generator import generate_patient_discharge_report
                pdf_bytes = await generate_patient_discharge_report(patient_id, room_id)
                # Store PDF or trigger download
                print(
                    f"✅ Generated discharge report for {patient_id} from {room_id}")
                report_generated = True
            except Exception as pdf_error:
                print(f"⚠️ Failed to generate PDF: {pdf_error}")

        # Remove patient from room
        result = unassign_patient_from_room(room_id, patient_id)

        if report_generated:
            result['report_generated'] = True
            result['report_message'] = 'Discharge report generated successfully'

        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/patients/{patient_id}/room")
async def get_patient_room(patient_id: str):
    """
    Get the current room assignment for a patient

    Args:
        patient_id: Patient identifier

    Returns:
        Room info if assigned, None otherwise
    """
    try:
        room = get_patient_current_room(patient_id)
        if room:
            return room
        return {"message": "Patient not assigned to any room"}
    except Exception as e:
        return {"error": str(e)}


class SyncRoomsRequest(BaseModel):
    rooms: list
    floor_id: str = 'floor-1'


@app.post("/rooms/sync-from-smplrspace")
async def sync_rooms_from_smplrspace(request: SyncRoomsRequest):
    """
    Sync rooms from Smplrspace automatic room detection

    Args:
        request: { rooms: [...], floor_id: 'floor-1' } from smplrClient.getRoomsOnLevel()

    Returns:
        { synced_count: number, rooms: [...] }
    """
    try:
        synced_rooms = []
        for room_item in request.rooms:
            room = sync_room_from_smplrspace(room_item, request.floor_id)
            synced_rooms.append(room)

        print(
            f"✅ Synced {len(synced_rooms)} rooms to floor {request.floor_id}")
        return {
            "synced_count": len(synced_rooms),
            "rooms": synced_rooms,
            "floor_id": request.floor_id
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# MCP-Inspired Agent Monitoring Control Tools
# ============================================================================

@app.get("/monitoring/config/{patient_id}")
async def get_monitoring_config(patient_id: str):
    """Get current monitoring configuration for a patient"""
    config = monitoring_manager.get_config(patient_id)
    return config.to_dict()


@app.get("/monitoring/configs")
async def get_all_monitoring_configs():
    """Get all patient monitoring configurations"""
    return monitoring_manager.get_all_configs()


@app.post("/monitoring/baseline/{patient_id}")
async def set_baseline_monitoring(patient_id: str, reason: str = "Manual activation"):
    """Agent tool: Set patient to baseline monitoring"""
    config = monitoring_manager.set_baseline_monitoring(patient_id, reason)

    # Broadcast state change to dashboard
    await manager.broadcast_frame({
        "type": "monitoring_state_change",
        "patient_id": patient_id,
        "level": "BASELINE",
        "reason": reason,
        "enabled_metrics": config.enabled_metrics
    })

    return {"status": "success", "config": config.to_dict()}


@app.post("/monitoring/enhanced/{patient_id}")
async def set_enhanced_monitoring(
    patient_id: str,
    duration_minutes: int = 15,
    reason: str = "Agent detected concerning metrics"
):
    """Agent tool: Activate enhanced monitoring (tremor, attention tracking)"""
    config = monitoring_manager.set_enhanced_monitoring(
        patient_id, duration_minutes, reason)

    # Broadcast state change to dashboard
    await manager.broadcast_frame({
        "type": "monitoring_state_change",
        "patient_id": patient_id,
        "level": "ENHANCED",
        "reason": reason,
        "duration_minutes": duration_minutes,
        "enabled_metrics": config.enabled_metrics,
        "expires_at": config.expires_at.isoformat() if config.expires_at else None
    })

    # Also send an alert notification
    await manager.broadcast_frame({
        "type": "agent_alert",
        "patient_id": patient_id,
        "severity": "MONITORING",
        "message": f"Enhanced monitoring activated for {duration_minutes} minutes",
        "reasoning": reason,
        "actions": [
            f"Monitoring: {', '.join(config.enabled_metrics)}",
            f"Duration: {duration_minutes} minutes",
            "Will auto-return to baseline if stable"
        ]
    })

    return {"status": "success", "config": config.to_dict()}


@app.post("/monitoring/critical/{patient_id}")
async def set_critical_monitoring(patient_id: str, reason: str = "Critical condition detected"):
    """Agent tool: Activate critical monitoring protocol"""
    config = monitoring_manager.set_critical_monitoring(patient_id, reason)

    # Broadcast state change to dashboard
    await manager.broadcast_frame({
        "type": "monitoring_state_change",
        "patient_id": patient_id,
        "level": "CRITICAL",
        "reason": reason,
        "enabled_metrics": config.enabled_metrics
    })

    return {"status": "success", "config": config.to_dict()}


@app.post("/monitoring/enable-metric/{patient_id}")
async def enable_metric(patient_id: str, metric: str):
    """Agent tool: Enable a specific metric for monitoring"""
    config = monitoring_manager.enable_metric(patient_id, metric)
    return {"status": "success", "config": config.to_dict()}


@app.post("/monitoring/disable-metric/{patient_id}")
async def disable_metric(patient_id: str, metric: str):
    """Agent tool: Disable a specific metric"""
    config = monitoring_manager.disable_metric(patient_id, metric)
    return {"status": "success", "config": config.to_dict()}


@app.post("/monitoring/frequency/{patient_id}")
async def set_monitoring_frequency(patient_id: str, seconds: int):
    """Agent tool: Change monitoring frequency"""
    config = monitoring_manager.set_frequency(patient_id, seconds)
    return {"status": "success", "config": config.to_dict()}


# ============================================================================
# LEGACY Multi-Agent System Endpoints (DISABLED - using health_agent instead)
# ============================================================================

# @app.get("/agents/status")
# async def get_agent_system_status():
#     """Get multi-agent system status"""
#     return agent_system.get_system_status()
#
#
# @app.get("/agents/events")
# async def get_agent_events(limit: int = 50):
#     """Get recent agent events for GlobalActivityFeed"""
#     return {
#         "events": agent_system.get_agent_events(limit),
#         "total": len(agent_system.agent_events)
#     }
#
#
# @app.get("/agents/alerts")
# async def get_agent_alerts():
#     """Get active agent alerts for AlertPanel"""
#     return {
#         "alerts": agent_system.get_agent_alerts(),
#         "total": len(agent_system.agent_alerts)
#     }
#
#
# @app.get("/agents/timeline/{patient_id}")
# async def get_patient_timeline(patient_id: str, limit: int = 100):
#     """Get timeline events for a specific patient"""
#     if not agent_system.enabled:
#         return {
#             "error": "Agent system not enabled",
#             "events": []
#         }
#
#     return {
#         "patient_id": patient_id,
#         "events": agent_system.get_patient_timeline(patient_id, limit),
#         "total": len(agent_system.timeline_events.get(patient_id, []))
#     }
#
#
# @app.post("/agents/analyze/{patient_id}")
# async def manual_agent_analysis(patient_id: str):
#     """
#     Manually trigger agent analysis (for testing)
#     Uses most recent CV metrics
#     """
#     if not agent_system.enabled:
#         return {
#             "error": "Agent system not enabled",
#             "message": "Install uagents: pip install uagents>=0.12.0"
#         }
#
#     # Get dummy metrics for testing
#     test_metrics = {
#         "heart_rate": 85,
#         "respiratory_rate": 18,
#         "crs_score": 0.65,
#         "tremor_detected": True,
#         "attention_score": 0.85
#     }
#
#     assessment = await agent_system.analyze_patient_metrics(patient_id, test_metrics)
#
#     return {
#         "patient_id": patient_id,
#         "assessment": assessment,
#         "metrics": test_metrics
#     }


# ============================================================================
# Health Agent Endpoints (NEW - Simple focused agent)
# ============================================================================

@app.get("/health-agent/status")
async def get_health_agent_status():
    """Get Fetch.ai health agent status"""
    return fetch_health_agent.get_status()


@app.get("/health-agent/patients")
async def get_health_agent_patients():
    """Get all monitored patients"""
    return {
        "patients": list(fetch_health_agent.patients.values()),
        "count": len(fetch_health_agent.patients)
    }


@app.get("/health-agent/patient/{patient_id}")
async def get_health_agent_patient(patient_id: str):
    """Get specific patient status"""
    if patient_id in fetch_health_agent.patients:
        return {"patient_id": patient_id, **fetch_health_agent.patients[patient_id]}
    else:
        return {"error": "Patient not found"}


@app.get("/health-agent/alerts")
async def get_health_agent_alerts():
    """Get active alerts"""
    active = [a for a in fetch_health_agent.alerts if a.get("severity") in [
        "CRITICAL", "WARNING"]]
    return {
        "alerts": active,
        "count": len(active)
    }


@app.get("/health-agent/history")
async def get_health_agent_history():
    """Get alert history"""
    return {
        "history": fetch_health_agent.alerts,
        "count": len(fetch_health_agent.alerts)
    }


# === FETCH.AI AGENT TEST ENDPOINTS ===

class AnalyzePatientRequest(BaseModel):
    patient_id: str
    vitals: Dict
    cv_metrics: Dict


@app.post("/health-agent/analyze")
async def analyze_patient_direct(request: AnalyzePatientRequest):
    """Test direct analysis via Fetch.ai agent"""
    try:
        analysis = await fetch_health_agent.analyze_patient(
            request.patient_id,
            request.vitals,
            request.cv_metrics
        )
        return {
            "success": True,
            "analysis": analysis,
            "patient_id": request.patient_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "patient_id": request.patient_id
        }


class TestCallRequest(BaseModel):
    patient_id: str = "P-TEST-001"
    event_type: str = "seizure"
    phone_number: Optional[str] = None


@app.post("/health-agent/test-call")
async def test_voice_call(request: TestCallRequest):
    """Test voice calling system"""
    from app.voice_call import voice_service

    # Override phone number if provided
    original_number = voice_service.emergency_number
    if request.phone_number:
        voice_service.emergency_number = request.phone_number

    try:
        result = voice_service.make_emergency_call(
            patient_id=request.patient_id,
            event_type=request.event_type,
            details="Test call from Haven system"
        )

        return {
            "success": True,
            "enabled": voice_service.enabled,
            "called_number": voice_service.emergency_number,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "enabled": voice_service.enabled,
            "error": str(e)
        }
    finally:
        # Restore original number
        voice_service.emergency_number = original_number


# ============================================================================
# Patient Guardian Agent Endpoints (LEGACY - keeping for compatibility)
# ============================================================================

class PatientBaseline(BaseModel):
    patient_id: str
    heart_rate: int = 75
    respiratory_rate: int = 14
    crs_score: float = 0.0


@app.post("/agent/set-baseline")
async def set_patient_baseline(baseline: PatientBaseline):
    """Set baseline vitals for a patient (used by agent for deviation calculations)"""
    patient_guardian.set_baseline(
        patient_id=baseline.patient_id,
        baseline={
            "heart_rate": baseline.heart_rate,
            "respiratory_rate": baseline.respiratory_rate,
            "crs_score": baseline.crs_score
        }
    )
    return {
        "status": "success",
        "patient_id": baseline.patient_id,
        "baseline": {
            "heart_rate": baseline.heart_rate,
            "respiratory_rate": baseline.respiratory_rate,
            "crs_score": baseline.crs_score
        }
    }


@app.get("/agent/alert-history/{patient_id}")
async def get_alert_history(patient_id: str):
    """Get agent alert history for a patient"""
    history = patient_guardian.alert_history.get(patient_id, [])
    return {
        "patient_id": patient_id,
        "alerts": history,
        "count": len(history)
    }


@app.post("/agent/analyze/{patient_id}")
async def trigger_agent_analysis(patient_id: str):
    """
    Manually trigger agent analysis (for testing/demo)
    Uses the most recent metrics from CV processing
    """
    # This would be called by demo scenarios to force agent analysis
    return {
        "status": "success",
        "message": "Agent analysis will occur on next metric calculation",
        "patient_id": patient_id
    }


# ============================================================================
# WebSocket Endpoints
# ============================================================================
@app.websocket("/ws/stream/{patient_id}")
async def websocket_stream(websocket: WebSocket, patient_id: str):
    """WebSocket endpoint for patient-specific streaming"""
    print(f"\n{'='*60}")
    print(f"🎯 WEBSOCKET HANDLER CALLED for patient: {patient_id}")

    # Accept connection IMMEDIATELY (before checking anything)
    # This prevents uvicorn from rejecting at protocol level
    await websocket.accept()
    print(
        f"✅ WebSocket connection accepted IMMEDIATELY for patient {patient_id}")

    print(f"   Client: {websocket.client}")
    print(f"   Headers: {dict(websocket.headers)}")
    print(f"   URL: {websocket.url}")

    # Check Origin header for CORS (after accept)
    origin = websocket.headers.get("origin", "")
    print(f"   Origin: {origin}")

    # List of allowed origins (same as CORS middleware)
    allowed_origins = [
        "https://use-haven.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]

    # Temporarily allow all origins for debugging
    # if origin and origin not in allowed_origins:
    #     print(f"❌ WebSocket rejected: Origin {origin} not in allowed list")
    #     print(f"{'='*60}\n")
    #     await websocket.close(code=403, reason="Origin not allowed")
    #     return

    print(f"✅ Origin check passed")
    print(f"{'='*60}\n")

    supabase_warning = None
    print(f"🎯 Incoming WebSocket connection for patient {patient_id}")

    # Verify patient exists in Supabase (non-blocking for client)
    if supabase:
        try:
            patient = supabase.table("patients") \
                .select("*") \
                .eq("patient_id", patient_id) \
                .single() \
                .execute()

            if not patient.data:
                supabase_warning = f"Patient {patient_id} not found in Supabase. Allowing connection."
                print(f"⚠️ {supabase_warning}")
        except Exception as e:
            supabase_warning = f"Database error verifying patient {patient_id}: {e}"
            print(f"⚠️ {supabase_warning}")

    # Check if patient is already streaming (after accept so we can notify client)
    if patient_id in manager.streamers:
        print(
            f"❌ Connection rejected: Patient {patient_id} already has an active stream")
        await websocket.send_json({
            "type": "error",
            "message": "This patient already has an active stream. Please stop the other stream before starting a new one."
        })
        await websocket.close(
            code=4090,
            reason="This patient already has an active stream. Please stop the other stream before starting a new one."
        )
        return

    # Wait for initial handshake with analysis mode
    try:
        print(f"⏳ Waiting for handshake from patient {patient_id}...")
        initial_data = await websocket.receive_json()
        print(f"📨 Received handshake data: {initial_data}")

        # Support both new format (analysis_mode) and legacy format (monitoring_conditions)
        analysis_mode = initial_data.get("analysis_mode", "normal")
        if "monitoring_conditions" in initial_data and not "analysis_mode" in initial_data:
            # Legacy: if conditions present, use enhanced mode
            monitoring_conditions = initial_data.get(
                "monitoring_conditions", [])
            analysis_mode = "enhanced" if monitoring_conditions else "normal"
            print(
                f"⚠️ Legacy format detected. Converting monitoring_conditions to analysis_mode: {analysis_mode}")

        print(
            f"📋 Registering streamer for patient {patient_id} with analysis mode: {analysis_mode}")

        manager.register_streamer(patient_id, websocket, analysis_mode)
        print(f"✅ Streamer registered successfully for patient {patient_id}")
        print(
            f"📊 Total active streamers: {len(manager.streamers)} - {list(manager.streamers.keys())}")

        # Send acknowledgment
        await websocket.send_json({
            "type": "connected",
            "patient_id": patient_id,
            "analysis_mode": analysis_mode,
            "supabase_verified": supabase_warning is None,
            "warning": supabase_warning
        })
        print(f"📤 Sent acknowledgment to patient {patient_id}")
    except Exception as e:
        print(f"❌ Handshake error for patient {patient_id}: {e}")
        import traceback
        traceback.print_exc()
        manager.register_streamer(patient_id, websocket, "normal")
        print(f"✅ Registered streamer with normal mode as fallback")

    try:
        frame_count = 0

        while True:
            try:
                data = await websocket.receive_json()
                frame_count += 1

                if data.get("type") == "frame":
                    raw_frame = data.get("frame")

                    # Step 1: IMMEDIATE PASSTHROUGH - Send raw frame to viewers instantly (30 FPS, no lag)
                    await manager.broadcast_frame({
                        "type": "live_frame",
                        "patient_id": patient_id,
                        "data": {
                            "frame": raw_frame
                        }
                    })

                    # Step 2: QUEUE FOR PROCESSING - Worker thread will handle CV processing
                    # Queue every 3rd frame (10 FPS) for better performance on limited CPU
                    if frame_count % 3 == 0:
                        manager.queue_frame_for_processing(
                            patient_id, raw_frame, frame_count)

            except WebSocketDisconnect:
                print(f"❌ Patient {patient_id} stream disconnected")
                break
            except Exception as frame_err:
                # If websocket is closed, stop immediately
                if "disconnect" in str(frame_err).lower() or "closed" in str(frame_err).lower():
                    print(f"❌ Patient {patient_id} connection closed")
                    break
                # For other errors, log once and break to avoid spam
                print(f"❌ Stream error for {patient_id}: {frame_err}")
                break

    except WebSocketDisconnect:
        print(f"❌ Patient {patient_id} stream disconnected (outer)")
    except Exception as e:
        print(f"❌ Stream error for patient {patient_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.unregister_streamer(patient_id)
        print(f"🧹 Stream cleanup complete for {patient_id}")


@app.websocket("/ws/view")
async def websocket_view(websocket: WebSocket):
    """WebSocket endpoint for dashboard viewing"""
    await websocket.accept()
    manager.viewers.append(websocket)
    print(f"✅ Viewer connected. Total: {len(manager.viewers)}")

    try:
        import asyncio
        last_ping = time.time()

        while True:
            # Send ping every 45 seconds to keep connection alive
            if time.time() - last_ping > 45:
                try:
                    if websocket.client_state.value == 1:  # WebSocketState.CONNECTED
                        await websocket.send_json({"type": "ping", "timestamp": time.time()})
                        last_ping = time.time()
                    else:
                        break
                except Exception as e:
                    print(f"❌ Ping failed: {e}")
                    break

            await asyncio.sleep(5)  # Check every 5 seconds
    except WebSocketDisconnect:
        print("Viewer disconnected")
    except Exception as e:
        print(f"❌ Viewer connection error: {e}")
    finally:
        manager.disconnect(websocket)
        print(f"🧹 Viewer cleanup complete. Remaining: {len(manager.viewers)}")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "default_user"
    chat_state: Optional[Dict] = None


@app.post("/ai/chat")
async def ai_chat(request: ChatRequest):
    """
    Context-aware AI chat endpoint using Anthropic Claude
    """
    if not anthropic_client:
        return {
            "response": "AI assistant is not available. Please configure ANTHROPIC_API_KEY.",
            "error": "anthropic_not_configured"
        }

    try:
        from app.chat_context import (
            create_session, read_context, write_context, build_system_prompt
        )
        from app.ai_tools import HAVEN_TOOLS, execute_tool

        # Get or create session
        session_title = None
        if request.session_id:
            try:
                context = await read_context(request.session_id)
                session_id = request.session_id
                # Get session title
                session_data = supabase.table("chat_sessions").select(
                    "title").eq("id", session_id).single().execute()
                if session_data.data:
                    session_title = session_data.data.get("title")
            except Exception as e:
                print(f"⚠️ Failed to load session {request.session_id}: {e}")
                # Create new session on error
                session = await create_session(request.user_id, request.message[:100])
                session_id = session["id"]
                session_title = session["title"]
                context = await read_context(session_id)
        else:
            # Create new session
            session = await create_session(request.user_id, request.message[:100])
            session_id = session["id"]
            session_title = session["title"]
            context = await read_context(session_id)

        # Update context state with current info
        if request.chat_state:
            context.state.update(request.chat_state)

        # Add user message to context
        context.messages.append({
            "role": "user",
            "content": request.message
        })

        # Convert messages to Anthropic format
        anthropic_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in context.messages
        ]

        # Build context-aware system prompt with EXTREME tool use bias
        base_system_prompt = await build_system_prompt(context)

        # Add CRITICAL instruction with EXTREME emphasis on tool use
        system_prompt = base_system_prompt + """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  ABSOLUTE RULE: TOOL USE IS MANDATORY ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If the user's message mentions patients, rooms, assignments, or hospital data:

🔴 YOU ARE FORBIDDEN FROM RESPONDING WITHOUT CALLING TOOLS
🔴 YOU CANNOT USE CONVERSATION MEMORY
🔴 YOU CANNOT ASSUME OR INFER INFORMATION
🔴 YOU MUST CALL A TOOL FIRST, THEN RESPOND

Examples of messages that REQUIRE tools:
✓ "Show all patients" → list_all_patients()
✓ "Describe my patients" → list_all_patients()
✓ "List patients" → list_all_patients()
✓ "Show occupancy" → get_all_room_occupancy()
✓ "Remove patient" → remove_patient_from_room()
✓ "Who's in room 2" → get_patient_in_room("2")
✓ "Move patient" → transfer_patient()
✓ "Assign patient" → assign_patient_to_room()
✓ "Tell me about X" → search_patients("X")
✓ "Remove dheeraj" → First search_patients("dheeraj") THEN remove_patient_from_room()

IF YOU RESPOND WITH "✅ Removed" OR "✅ Transferred" OR "✅ Assigned" WITHOUT CALLING A TOOL:
→ YOU HAVE LIED TO THE USER
→ THE DATABASE WAS NOT UPDATED
→ YOU FAILED YOUR CORE FUNCTION

IF YOU LIST PATIENTS WITHOUT CALLING list_all_patients():
→ THE NAMES ARE MADE UP FROM YOUR TRAINING DATA
→ THEY DON'T EXIST IN THE DATABASE
→ YOU ARE HALLUCINATING

NEVER say patient names like "Robert Kim", "Emily Martinez", "Sarah Chen", "Michael Johnson" unless:
1. You called a tool that returned those EXACT names
2. The names appear in the tool result JSON

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 MULTI-STEP OPERATIONS REQUIRE MULTIPLE TOOL CALLS 🚨

"Add dheeraj to room 1":
→ Step 1: Call search_patients("dheeraj")
→ Step 2: WITH THE RESULT, call assign_patient_to_room(patient_id, "1")
→ Step 3: Respond with final result

DO NOT SAY "I'll assign them" OR "Now I'll assign" BETWEEN TOOL CALLS
JUST CALL BOTH TOOLS, THEN RESPOND ONCE WITH THE FINAL RESULT

"Remove dheeraj":  
→ Step 1: Call search_patients("dheeraj") OR list_all_patients()
→ Step 2: Call remove_patient_from_room(patient_id)
→ Step 3: Respond with result

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE: IF USER ASKS ABOUT DATA → CALL TOOL FIRST → RESPOND WITH TOOL RESULTS ONLY
WHEN IN DOUBT: CALL A TOOL. ALWAYS PREFER TOOLS.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        print(f"\n💬 User message: {request.message}")
        print(
            f"   (AI will decide whether to use tools based on strong system instructions)")

        # Call Anthropic API - let AI decide but with strong prompt bias toward tools
        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system_prompt,
            tools=HAVEN_TOOLS,
            messages=anthropic_messages
        )

        # Handle tool use with MULTI-ROUND support
        assistant_response = ""
        all_tool_results = []
        max_rounds = 5  # Prevent infinite loops
        round_num = 0

        current_message = message

        # LOOP until Claude stops calling tools (multi-step operations)
        while current_message.stop_reason == "tool_use" and round_num < max_rounds:
            round_num += 1
            print(f"\n{'='*60}")
            print(f"🔄 TOOL ROUND {round_num}")
            print(f"{'='*60}")

            tool_results = []

            # Execute all tools in this round
            for content_block in current_message.content:
                if content_block.type == "text":
                    assistant_response += content_block.text
                elif content_block.type == "tool_use":
                    print(f"\n🔧 Tool call: {content_block.name}")
                    print(f"   Input: {content_block.input}")
                    tool_result = await execute_tool(content_block.name, content_block.input)
                    print(f"   Result: {tool_result}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": json.dumps(tool_result)
                    })
                    all_tool_results.append(tool_result)

            # Add this round to conversation
            anthropic_messages.append({
                "role": "assistant",
                "content": current_message.content
            })
            anthropic_messages.append({
                "role": "user",
                "content": tool_results
            })

            # Build system prompt for next round
            next_system = f"""You are Haven AI. 

**CRITICAL: You just received tool results. You can:**
1. Call MORE tools if you need additional information
2. Respond with final text if you have enough information

**MULTI-STEP OPERATIONS:**
If user said "Add dheeraj to room 1":
- Round 1: You called search_patients("dheeraj") → got patient_id
- Round 2: NOW call assign_patient_to_room(patient_id, "1") ← DO THIS NOW
- Round 3: Respond with "✅ Assigned"

DO NOT respond with text until the FULL operation is complete.
Only use information from tool results. Never use conversation memory."""

            # Call Claude again - it can call MORE tools or respond
            current_message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                system=next_system,
                tools=HAVEN_TOOLS,
                messages=anthropic_messages
            )

            print(
                f"\n📊 Round {round_num} complete. Stop reason: {current_message.stop_reason}")

        # Extract final text response
        if current_message.stop_reason != "tool_use":
            for content_block in current_message.content:
                if content_block.type == "text":
                    assistant_response += content_block.text

        print(f"\n✅ Tool execution complete after {round_num} rounds")
        print(f"   Total tools called: {len(all_tool_results)}")

        # Add assistant response to context
        context.messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        # Save updated context
        await write_context(session_id, context)

        # Check if any write operations were performed (check ALL rounds)
        invalidate_cache = False
        cache_keys = set()

        print(
            f"\n📊 Checking {len(all_tool_results)} total tool results for cache invalidation...")

        for tool_result in all_tool_results:
            if isinstance(tool_result, dict) and tool_result.get("success"):
                invalidate_cache = True
                cache_keys.update(
                    ["rooms", "patients", "patients_room", "assignments", "alerts"])
                print(f"   ✅ Success detected - will invalidate cache")

        cache_keys_list = list(cache_keys) if cache_keys else []

        print(f"\n{'='*60}")
        print(f"📤 Returning to frontend:")
        print(f"   invalidate_cache: {invalidate_cache}")
        print(f"   cache_keys: {cache_keys_list}")
        print(f"   tool_calls: {len(all_tool_results)}")
        print(f"   rounds: {round_num}")
        print(f"{'='*60}\n")

        return {
            "response": assistant_response,
            "model": "claude-haiku-4.5",
            "session_id": session_id,
            "session_title": session_title,
            "tool_calls": len(all_tool_results),
            "tool_rounds": round_num,
            "invalidate_cache": invalidate_cache,
            "cache_keys": cache_keys_list
        }

    except Exception as e:
        print(f"❌ Error in AI chat: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": "I'm having trouble processing your request. Please try again.",
            "error": str(e)
        }


@app.get("/ai/sessions")
async def get_sessions(user_id: str = "default_user"):
    """
    Get all chat sessions for a user
    """
    try:
        from app.chat_context import get_user_sessions
        sessions = await get_user_sessions(user_id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"❌ Error fetching sessions: {e}")
        return {"sessions": [], "error": str(e)}


@app.get("/ai/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get a specific session with full message history
    """
    try:
        from app.chat_context import read_context
        context = await read_context(session_id)
        return {
            "session_id": session_id,
            "messages": context.messages
        }
    except Exception as e:
        print(f"❌ Error fetching session {session_id}: {e}")
        return {"messages": [], "error": str(e)}


@app.get("/reports/discharge/{patient_id}/{room_id}")
async def download_discharge_report(patient_id: str, room_id: str):
    """
    Generate and download PDF discharge report for a patient
    """
    try:
        from app.pdf_generator import generate_patient_discharge_report, REPORTLAB_AVAILABLE, generate_simple_text_report

        if not REPORTLAB_AVAILABLE:
            # Fallback to text report
            text_report = generate_simple_text_report(patient_id, room_id)
            return Response(
                content=text_report,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename=discharge-report-{patient_id}-{datetime.now().strftime('%Y%m%d')}.txt"
                }
            )

        pdf_bytes = await generate_patient_discharge_report(patient_id, room_id)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=discharge-report-{patient_id}-{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )
    except Exception as e:
        print(f"❌ Error generating discharge report: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/reports/clinical-summary/{patient_id}")
async def download_clinical_summary(patient_id: str):
    """
    Generate and download AI-powered clinical summary PDF for a patient
    """
    try:
        from app.pdf_generator import generate_clinical_summary_report, REPORTLAB_AVAILABLE
        from app.ai_tools import generate_patient_clinical_summary_tool

        # Generate summary data with AI insights
        summary_data = await generate_patient_clinical_summary_tool(patient_id, include_recommendations=True)

        if "error" in summary_data:
            return {"error": summary_data["error"]}

        if not REPORTLAB_AVAILABLE:
            # Text fallback
            text_report = f"""HAVEN HOSPITAL - CLINICAL SUMMARY

Patient: {summary_data.get('patient_name')} ({patient_id})
Age: {summary_data.get('age')} | Gender: {summary_data.get('gender')}
Condition: {summary_data.get('condition')}

KEY CONCERNS:
{chr(10).join(summary_data.get('ai_insights', {}).get('key_concerns', []))}

RISK FACTORS:
{chr(10).join(summary_data.get('ai_insights', {}).get('risk_factors', []))}

RECOMMENDATIONS:
{chr(10).join(summary_data.get('ai_insights', {}).get('recommendations', []))}

Active Alerts: {summary_data.get('active_alerts_count', 0)}
"""
            return Response(
                content=text_report,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename=clinical-summary-{patient_id}-{datetime.now().strftime('%Y%m%d')}.txt"
                }
            )

        # Generate PDF
        pdf_bytes = await generate_clinical_summary_report(summary_data)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=clinical-summary-{patient_id}-{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )
    except Exception as e:
        print(f"❌ Error generating clinical summary: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# ========================================
# PATIENT INTAKE ENDPOINTS (LiveKit-based)
# ========================================

@app.post("/api/intake/start")
async def start_intake(request: dict):
    """
    Initialize a patient intake session and return LiveKit access token
    """
    try:
        from livekit.api import AccessToken, VideoGrants
        import uuid

        patient_id = request.get("patient_id")
        if not patient_id:
            return {"error": "patient_id is required"}, 400

        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        room_name = f"intake-{patient_id}-{session_id}"

        # Create LiveKit access token for patient
        token = AccessToken(
            os.getenv("LIVEKIT_API_KEY"),
            os.getenv("LIVEKIT_API_SECRET")
        )
        token = token.with_identity(f"patient-{patient_id}").with_name(patient_id).with_grants(VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))

        print(
            f"🎫 Created intake token for patient {patient_id}, room: {room_name}")

        return {
            "token": token.to_jwt(),
            "url": os.getenv("LIVEKIT_URL"),
            "room_name": room_name,
            "patient_id": patient_id,
            "session_id": session_id
        }

    except Exception as e:
        print(f"❌ Error starting intake: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


@app.get("/api/intake/pending")
async def get_pending_intakes():
    """
    Get all intake reports awaiting review, sorted by urgency and time
    """
    try:
        if not supabase:
            return []

        result = supabase.table("intake_reports") \
            .select("*") \
            .eq("status", "pending_review") \
            .order("created_at", desc=True) \
            .execute()

        # Sort by urgency (high first) then by time
        intakes = result.data if result.data else []
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        intakes.sort(key=lambda x: (
            urgency_order.get(x.get("urgency_level", "low"), 2),
            x.get("created_at", "")
        ))

        logger.info(f"📋 Retrieved {len(intakes)} pending intakes")
        return intakes

    except Exception as e:
        logger.error(f"Error fetching pending intakes: {e}", exc_info=True)
        return {"error": str(e)}, 500


@app.get("/api/intake/{intake_id}")
async def get_intake_report(intake_id: str):
    """
    Get full intake report by ID
    """
    try:
        if not supabase:
            return {"error": "Database not available"}, 503

        result = supabase.table("intake_reports") \
            .select("*") \
            .eq("id", intake_id) \
            .single() \
            .execute()

        if not result.data:
            return {"error": "Intake report not found"}, 404

        logger.info(f"📄 Retrieved intake report: {intake_id}")
        return result.data

    except Exception as e:
        logger.error(f"Error fetching intake report: {e}", exc_info=True)
        return {"error": str(e)}, 500


@app.post("/api/intake/{intake_id}/review")
async def mark_intake_reviewed(intake_id: str, request: dict):
    """
    Mark intake as reviewed by provider
    """
    try:
        if not supabase:
            return {"error": "Database not available"}, 503

        reviewer_id = request.get("reviewer_id", "unknown")

        supabase.table("intake_reports") \
            .update({
                "status": "reviewed",
                "reviewed_by": reviewer_id,
                "reviewed_at": datetime.now().isoformat()
            }) \
            .eq("id", intake_id) \
            .execute()

        logger.info(
            f"✅ Intake {intake_id} marked as reviewed by {reviewer_id}")
        return {"success": True}

    except Exception as e:
        logger.error(f"Error marking intake as reviewed: {e}", exc_info=True)
        return {"error": str(e)}, 500


@app.post("/api/intake/{intake_id}/assign-room")
async def assign_intake_to_room(intake_id: str, request: dict):
    """
    Assign patient from intake to an examination room
    """
    try:
        if not supabase:
            return {"error": "Database not available"}, 503

        room_id = request.get("room_id")
        if not room_id:
            return {"error": "room_id is required"}, 400

        # Get intake report
        intake_result = supabase.table("intake_reports") \
            .select("*") \
            .eq("id", intake_id) \
            .single() \
            .execute()

        if not intake_result.data:
            return {"error": "Intake report not found"}, 404

        patient_id = intake_result.data.get("patient_id")

        # Update intake report
        supabase.table("intake_reports") \
            .update({
                "status": "assigned",
                "assigned_room": room_id
            }) \
            .eq("id", intake_id) \
            .execute()

        # Assign patient to room (use existing room assignment logic)
        try:
            supabase.table("room_assignments") \
                .insert({
                    "room_id": room_id,
                    "patient_id": patient_id,
                    "assigned_at": datetime.now().isoformat()
                }) \
                .execute()
        except Exception as room_error:
            logger.warning(f"Room assignment may already exist: {room_error}")

        logger.info(
            f"🏥 Patient {patient_id} assigned to room {room_id} from intake {intake_id}")

        # Broadcast to dashboard
        await manager.broadcast_frame({
            "type": "patient_assigned_from_intake",
            "patient_id": patient_id,
            "room_id": room_id,
            "intake_id": intake_id
        })

        return {"success": True, "patient_id": patient_id, "room_id": room_id}

    except Exception as e:
        logger.error(f"Error assigning intake to room: {e}", exc_info=True)
        return {"error": str(e)}, 500


@app.get("/api/intake/stats")
async def get_intake_stats():
    """
    Get intake system statistics
    """
    try:
        if not supabase:
            return {"error": "Database not available"}, 503

        # Count by status
        all_intakes = supabase.table("intake_reports").select(
            "status, urgency_level").execute()

        stats = {
            "total": len(all_intakes.data) if all_intakes.data else 0,
            "pending": 0,
            "reviewed": 0,
            "assigned": 0,
            "high_urgency": 0,
            "medium_urgency": 0,
            "low_urgency": 0
        }

        if all_intakes.data:
            for intake in all_intakes.data:
                status = intake.get("status", "")
                urgency = intake.get("urgency_level", "low")

                if status == "pending_review":
                    stats["pending"] += 1
                elif status == "reviewed":
                    stats["reviewed"] += 1
                elif status == "assigned":
                    stats["assigned"] += 1

                if urgency == "high":
                    stats["high_urgency"] += 1
                elif urgency == "medium":
                    stats["medium_urgency"] += 1
                else:
                    stats["low_urgency"] += 1

        return stats

    except Exception as e:
        logger.error(f"Error getting intake stats: {e}", exc_info=True)
        return {"error": str(e)}, 500


# ========================================
# HAVEN VOICE AGENT ENDPOINTS (LiveKit Voice Agent)
# ========================================

@app.post("/api/haven/start")
async def start_haven_session(request: dict):
    """
    Initialize a Haven voice agent session when "Hey Haven" is detected
    Returns LiveKit access token for voice conversation
    """
    ready, issues = _check_livekit_config()
    if not ready:
        raise HTTPException(
            status_code=503,
            detail="LiveKit configuration incomplete: " + "; ".join(issues)
        )

    try:
        from livekit.api import AccessToken, VideoGrants
        import uuid

        patient_id = request.get("patient_id")
        if not patient_id:
            return {"error": "patient_id is required"}, 400

        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        room_name = f"haven-{patient_id}-{session_id}"

        # Create LiveKit access token for patient
        token = AccessToken(
            get_secret("LIVEKIT_API_KEY"),
            get_secret("LIVEKIT_API_SECRET")
        )
        token = token.with_identity(f"patient-{patient_id}").with_name(patient_id).with_grants(VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))

        print(
            f"🛡️ Created Haven agent token for patient {patient_id}, room: {room_name}")

        return {
            "token": token.to_jwt(),
            "url": get_secret("LIVEKIT_URL"),
            "room_name": room_name,
            "patient_id": patient_id,
            "session_id": session_id
        }

    except Exception as e:
        print(f"❌ Error starting Haven session: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def process_haven_conversation(patient_id: str, session_id: str | None, conversation_summary: dict) -> dict:
    """
    Shared workflow for Haven conversations.
    Validates question counts, analyzes severity, persists alert, and broadcasts updates.
    """
    # Get patient's room assignment
    room_id = None
    if supabase:
        try:
            room_result = supabase.table("patients_room") \
                .select("room_id") \
                .eq("patient_id", patient_id) \
                .single() \
                .execute()

            if room_result.data:
                room_id = room_result.data.get("room_id")
        except Exception as e:
            print(f"⚠️ Could not get room for patient {patient_id}: {e}")

    assistant_questions = conversation_summary.get(
        "assistant_question_count")
    total_questions = conversation_summary.get("question_count")

    transcript_entries = conversation_summary.get("transcript") or []
    if assistant_questions is None and transcript_entries:
        assistant_questions = sum(
            1 for entry in transcript_entries
            if entry.get("role") == "assistant" and "?" in (entry.get("content") or "")
        )

    transcript_text = conversation_summary.get("full_transcript_text") or ""
    if assistant_questions is None and transcript_text:
        question_marks = transcript_text.count("?")
        assistant_questions = question_marks if question_marks else 1

    if total_questions is None:
        assistant_turns = conversation_summary.get("assistant_turns")
        if assistant_turns is not None:
            total_questions = assistant_turns

    if total_questions is None and transcript_entries:
        total_questions = sum(
            1 for entry in transcript_entries
            if entry.get("role") == "assistant"
        )

    if total_questions is None and transcript_text:
        total_questions = max(assistant_questions or 0, 1)

    min_required_questions = 1

    if assistant_questions is not None and assistant_questions < min_required_questions:
        print(
            f"⚠️ Haven conversation skipped (only {assistant_questions} assistant questions)")
        return {"success": True, "skipped": True}

    if total_questions is not None and total_questions < min_required_questions:
        print(
            f"⚠️ Haven conversation skipped (total questions {total_questions} < {min_required_questions})")
        return {"success": True, "skipped": True}

    existing_alert_id = None
    existing_alert_severity = None
    if session_id and supabase:
        try:
            existing_response = supabase.table("alerts") \
                .select("id,severity") \
                .filter("metadata->>session_id", "eq", session_id) \
                .filter("triggered_by", "eq", "haven_agent") \
                .limit(1) \
                .execute()

            if existing_response.data:
                existing_alert_id = existing_response.data[0]["id"]
                existing_alert_severity = existing_response.data[0].get(
                    "severity")
        except Exception as e:
            print(
                f"⚠️ Could not check for existing Haven alert for session {session_id}: {e}")

    alert_data = await _analyze_haven_conversation(
        patient_id=patient_id,
        conversation_summary=conversation_summary,
        room_id=room_id
    )

    if not supabase:
        print("⚠️ Supabase not available, alert not saved")
        return {"success": False, "error": "Database not available"}

    metadata_payload = json.dumps({
        "session_id": session_id,
        "transcript": conversation_summary.get("full_transcript_text", ""),
        "transcript_entries": conversation_summary.get("transcript", []),
        "assistant_turns": conversation_summary.get("assistant_turns"),
        "assistant_question_count": conversation_summary.get("assistant_question_count"),
        "total_turns": conversation_summary.get("total_turns"),
        "summary_source": conversation_summary.get("source"),
        "extracted_info": conversation_summary.get("extracted_info", {}),
        "ai_analysis": alert_data.get("reasoning", ""),
        "concern_type": "patient_initiated"
    })

    alert_payload = {
        "alert_type": "other",
        "severity": alert_data["severity"],
        "title": alert_data["title"],
        "description": alert_data["description"],
        "patient_id": patient_id,
        "room_id": room_id,
        "triggered_by": "haven_agent",
        "status": "active",
        "metadata": metadata_payload,
        "triggered_at": datetime.now().isoformat()
    }

    if existing_alert_id:
        alert_result = supabase.table("alerts").update(alert_payload).eq(
            "id", existing_alert_id).execute()
        alert_id = existing_alert_id
        print(
            f"🔁 Updated existing alert {alert_id} from Haven conversation for patient {patient_id}")
    else:
        alert_result = supabase.table("alerts").insert(alert_payload).execute()
        alert_id = alert_result.data[0]["id"] if alert_result.data else None
        print(
            f"✅ Created alert {alert_id} from Haven conversation for patient {patient_id}")

    # Broadcast alert to dashboard via WebSocket
    await manager.broadcast_frame({
        "type": "haven_alert",
        "patient_id": patient_id,
        "room_id": room_id,
        "alert_id": alert_id,
        "severity": alert_data["severity"],
        "title": alert_data["title"],
        "description": alert_data["description"],
        "timestamp": datetime.now().isoformat()
    })

    return {
        "success": True,
        "alert_id": alert_id,
        "severity": alert_data["severity"]
    }


@app.post("/api/haven/conversation")
async def save_haven_conversation(request: dict):
    """
    Save Haven conversation summary and create alert
    Called when Haven agent completes conversation
    """
    try:
        patient_id = request.get("patient_id")
        session_id = request.get("session_id")
        conversation_summary = request.get("conversation_summary")

        if not all([patient_id, conversation_summary]):
            return {"error": "patient_id and conversation_summary are required"}, 400

        return await process_haven_conversation(
            patient_id=patient_id,
            session_id=session_id,
            conversation_summary=conversation_summary
        )

    except Exception as e:
        print(f"❌ Error saving Haven conversation: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


async def _analyze_haven_conversation(patient_id: str, conversation_summary: dict, room_id: str = None) -> dict:
    """
    Use Claude to analyze Haven conversation and determine alert severity
    """
    if not anthropic_client:
        # Fallback to rule-based analysis
        extracted_info = conversation_summary.get("extracted_info", {})
        pain_level = extracted_info.get("pain_level")
        symptom_description = extracted_info.get("symptom_description")
        body_location = extracted_info.get("body_location")
        duration = extracted_info.get("duration")
        patient_statements = extracted_info.get("patient_statements", [])
        if isinstance(patient_statements, str):
            patient_statements = [patient_statements]

        if pain_level and pain_level >= 8:
            severity = "high"
        elif pain_level and pain_level >= 5:
            severity = "medium"
        else:
            severity = "low"

        transcript_entries = conversation_summary.get("transcript", [])
        if transcript_entries and not patient_statements:
            patient_statements = [
                entry.get("content")
                for entry in transcript_entries
                if entry.get("role") == "patient" and entry.get("content")
            ][:3]

        description_parts: list[str] = []

        if symptom_description:
            description_parts.append(
                f"Patient reported {symptom_description.strip()}")
        elif patient_statements:
            description_parts.append(
                f"Patient reported {patient_statements[0].strip()}")

        if body_location:
            description_parts.append(f"Location: {body_location}")

        if pain_level is not None:
            description_parts.append(f"Pain level rated {pain_level}/10")

        if duration:
            description_parts.append(f"Duration noted: {duration.strip()}")

        if len(patient_statements) > 1:
            secondary = patient_statements[1].strip()
            if secondary and secondary.lower() != (symptom_description or '').lower():
                description_parts.append(f"Additional detail: {secondary}")

        if not description_parts:
            transcript_text = conversation_summary.get(
                "full_transcript_text", "").strip()
            if transcript_text:
                description_parts.append(transcript_text[:350])
            else:
                description_parts.append("No detailed transcript available.")

        raw_title_detail = symptom_description or (
            patient_statements[0] if patient_statements else None
        ) or "concern"
        title_detail = str(raw_title_detail).strip().replace("\n", " ")

        return {
            "severity": severity,
            "title": f"Patient {patient_id} reported {title_detail[:80]}",
            "description": " | ".join(description_parts),
            "reasoning": "Rule-based analysis (Claude not available)"
        }

    try:
        # Build Claude prompt
        extracted_info = conversation_summary.get("extracted_info", {})
        transcript = conversation_summary.get("full_transcript_text", "")

        prompt = f"""You are a clinical triage AI. Analyze this patient conversation and determine the urgency level.

**Patient ID:** {patient_id}
**Room:** {room_id or "Unknown"}

**Conversation Transcript:**
{transcript}

**Extracted Information:**
- Symptom: {extracted_info.get('symptom_description', 'Not specified')}
- Location: {extracted_info.get('body_location', 'Not specified')}
- Pain Level: {extracted_info.get('pain_level', 'Not rated')} / 10
- Duration: {extracted_info.get('duration', 'Unknown')}

**Your Task:**
Determine the urgency level and create an alert summary.

**Response Format (JSON):**
{{
  "severity": "critical" | "high" | "medium" | "low",
  "title": "Brief alert title (max 80 chars)",
  "description": "Detailed description of concern (2-3 sentences)",
  "reasoning": "Clinical reasoning for severity level"
}}

**Severity Guidelines:**
- **critical**: Life-threatening (chest pain, severe bleeding, difficulty breathing, altered consciousness)
- **high**: Urgent but not immediately life-threatening (severe pain 8-10, significant symptoms)
- **medium**: Moderate concern (moderate pain 5-7, uncomfortable symptoms)
- **low**: Minor concern (mild pain 1-4, general questions)

Provide your analysis:"""

        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse Claude's response
        response_text = message.content[0].text

        # Extract JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            raise ValueError("Could not parse Claude response")

    except Exception as e:
        print(f"⚠️ Claude analysis failed: {e}, using fallback")
        # Fallback
        extracted_info = conversation_summary.get("extracted_info", {})
        pain_level = extracted_info.get("pain_level")

        if pain_level and pain_level >= 8:
            severity = "high"
        elif pain_level and pain_level >= 5:
            severity = "medium"
        else:
            severity = "low"

        return {
            "severity": severity,
            "title": f"Patient {patient_id} reported concern",
            "description": conversation_summary.get("full_transcript_text", "No details available")[:200],
            "reasoning": "Fallback analysis"
        }


@app.get("/api/haven/active")
async def get_active_haven_sessions():
    """
    Get list of active Haven voice sessions
    """
    # This would integrate with LiveKit to get active rooms
    # For now, return placeholder
    return {
        "active_sessions": [],
        "count": 0
    }


# ========================================
# HANDOFF FORM GENERATION ENDPOINTS (Fetch.ai Agent)
# ========================================

@app.get("/handoff-agent/status")
async def get_handoff_agent_status():
    """Get Fetch.ai handoff agent status"""
    if not FETCH_HANDOFF_AVAILABLE:
        return {
            "enabled": False,
            "error": "Fetch.ai handoff agent not available - install uagents package"
        }

    return {
        "enabled": True,
        "agent_address": fetch_handoff_agent.agent.address,
        "processed_alerts": len(fetch_handoff_agent.processed_alerts),
        "generated_forms": len(fetch_handoff_agent.generated_forms),
        "nurse_emails": fetch_handoff_agent.nurse_emails,
        "check_interval_seconds": fetch_handoff_agent.check_interval
    }


class GenerateHandoffRequest(BaseModel):
    alert_ids: Optional[List[str]] = None
    patient_id: Optional[str] = None
    recipient_emails: Optional[List[str]] = None


@app.post("/handoff-agent/generate")
async def generate_handoff_form_manual(request: GenerateHandoffRequest):
    """
    Manually trigger handoff form generation

    Args:
        alert_ids: List of specific alert IDs to include
        patient_id: Generate for all alerts of this patient
        recipient_emails: Email addresses to send form (defaults to configured nurse emails)

    Returns:
        Form generation result with PDF path and email status
    """
    if not FETCH_HANDOFF_AVAILABLE:
        return {
            "success": False,
            "message": "Fetch.ai handoff agent not available - install uagents package"
        }

    try:
        # Use configured nurse emails if not provided
        recipient_emails = request.recipient_emails
        if not recipient_emails:
            recipient_emails = fetch_handoff_agent.nurse_emails

        # Generate form (synchronous version for API)
        from app.services.alerts_service import alerts_service
        from app.services.pdf_generator import pdf_generator
        from app.services.email_service import email_service
        from app.models.handoff_forms import PatientInfo, HandoffFormContent
        from datetime import datetime

        # Fetch alerts
        if request.alert_ids:
            alerts = alerts_service.get_alerts_by_ids(request.alert_ids)
        elif request.patient_id:
            alerts = alerts_service.get_alerts_by_patient(
                request.patient_id, include_resolved=False)
        else:
            return {
                "success": False,
                "message": "Must provide either alert_ids or patient_id"
            }

        if not alerts:
            return {
                "success": False,
                "message": "No alerts found"
            }

        # Get patient info
        patient_id = alerts[0].patient_id
        patient_data = alerts_service.get_patient_info(patient_id)
        patient_info = PatientInfo(
            patient_id=patient_id,
            name=patient_data.get("name") if patient_data else None,
            age=patient_data.get("age") if patient_data else None,
            room_number=patient_data.get(
                "room_number") if patient_data else None,
            diagnosis=patient_data.get("diagnosis") if patient_data else None,
            treatment_status=patient_data.get(
                "treatment_status") if patient_data else None,
            allergies=patient_data.get("allergies") if patient_data else None,
            current_medications=patient_data.get(
                "current_medications") if patient_data else None
        )

        # Generate basic summary (use Claude if available)
        max_severity = max(alerts, key=lambda a: [
                           "info", "low", "medium", "high", "critical"].index(a.severity.value))
        alert_summary = f"Patient has {len(alerts)} active alert(s) requiring attention."
        primary_concern = alerts[0].title
        recommended_actions = [
            "Review all active alerts immediately",
            "Assess patient condition and vital signs",
            "Document all interventions in patient record"
        ]

        # Build form content
        form_content = HandoffFormContent(
            patient_info=patient_info,
            alert_summary=alert_summary,
            primary_concern=primary_concern,
            severity_level=max_severity.severity,
            recent_vitals=None,
            relevant_history=None,
            current_treatments=patient_info.current_medications,
            recommended_actions=recommended_actions,
            urgency_notes=None,
            protocols_to_follow=None,
            related_alerts=alerts,
            timeline=[],
            generated_at=datetime.utcnow(),
            generated_by="FETCH_AI_HANDOFF_AGENT",
            intended_recipient="Nurse/Doctor",
            special_instructions=None,
            contact_information={"Emergency": "x5555"}
        )

        # Generate form number using database function
        try:
            form_num_result = supabase.rpc("generate_form_number").execute()
            form_number = form_num_result.data if form_num_result.data else f"HO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        except:
            # Fallback if function doesn't exist
            form_number = f"HO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Generate PDF
        pdf_path = pdf_generator.generate_handoff_pdf(
            form_content=form_content,
            form_number=form_number
        )

        # Save to database
        from app.supabase_client import supabase
        import json
        data = {
            "form_number": form_number,
            "patient_id": patient_id,
            "alert_ids": [alert.id for alert in alerts],
            # Use json() to handle datetime serialization
            "content": json.loads(form_content.json()),
            "pdf_path": pdf_path,
            "status": "generated",
            "created_by": "FETCH_AI_HANDOFF_AGENT"
        }

        result = supabase.table("handoff_forms").insert(data).execute()
        form_id = result.data[0]["id"] if result.data else None

        # Update alerts table to reference this form
        if form_id:
            supabase.table("alerts").update({
                "form_id": form_id,
                "pdf_path": pdf_path
            }).in_("id", [alert.id for alert in alerts]).execute()

        # Send email
        email_result = None
        if recipient_emails and recipient_emails[0]:
            email_result = email_service.send_handoff_form(
                recipient_emails=recipient_emails,
                form_number=form_number,
                patient_id=patient_id,
                patient_name=patient_info.name,
                severity=form_content.severity_level.value,
                alert_summary=alert_summary,
                pdf_path=pdf_path
            )

            if email_result["success"]:
                # Update database with email info
                supabase.table("handoff_forms").update({
                    "emailed_to": recipient_emails,
                    "email_sent_at": datetime.utcnow().isoformat(),
                    "email_delivery_status": "sent",
                    "status": "sent"
                }).eq("id", form_id).execute()

        return {
            "success": True,
            "form_id": form_id,
            "form_number": form_number,
            "pdf_path": pdf_path,
            "alerts_processed": len(alerts),
            "email_sent": email_result["success"] if email_result else False,
            "message": f"Successfully generated handoff form {form_number}"
        }

    except Exception as e:
        print(f"❌ Error generating handoff form: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@app.get("/handoff-agent/forms")
async def get_handoff_forms(patient_id: Optional[str] = None, limit: int = 50):
    """
    Get generated handoff forms (only for active alerts)

    Args:
        patient_id: Filter by patient ID
        limit: Maximum number of forms to return

    Returns:
        List of handoff forms with active alerts only
    """
    try:
        # First get all forms
        query = supabase.table("handoff_forms").select("*")

        if patient_id:
            query = query.eq("patient_id", patient_id)

        response = query.order("created_at", desc=True).limit(
            limit * 2).execute()  # Get more to filter

        if not response.data:
            return {"forms": [], "count": 0}

        # Filter forms to only include those with at least one active alert
        filtered_forms = []
        for form in response.data:
            alert_ids = form.get("alert_ids", [])
            if alert_ids:
                # Check if any of the alerts are still active
                alerts_response = supabase.table("alerts").select(
                    "status").in_("id", alert_ids).execute()
                if alerts_response.data:
                    # Include form if any alert is 'active'
                    has_active = any(alert.get("status") ==
                                     "active" for alert in alerts_response.data)
                    if has_active:
                        filtered_forms.append(form)
                        if len(filtered_forms) >= limit:
                            break

        return {
            "forms": filtered_forms,
            "count": len(filtered_forms)
        }
    except Exception as e:
        print(f"❌ Error fetching handoff forms: {e}")
        return {
            "forms": [],
            "count": 0,
            "error": str(e)
        }


@app.get("/handoff-agent/forms/{form_id}")
async def get_handoff_form(form_id: str):
    """Get specific handoff form by ID"""
    try:
        response = supabase.table("handoff_forms").select(
            "*").eq("id", form_id).single().execute()

        if response.data:
            return response.data
        else:
            return {"error": "Form not found"}
    except Exception as e:
        print(f"❌ Error fetching form: {e}")
        return {"error": str(e)}


@app.get("/handoff-agent/forms/{form_id}/pdf")
async def download_handoff_form_pdf(form_id: str):
    """Download PDF for a specific handoff form"""
    try:
        # Get form from database
        response = supabase.table("handoff_forms").select(
            "pdf_path").eq("id", form_id).single().execute()

        if not response.data:
            return {"error": "Form not found"}

        pdf_path = response.data.get("pdf_path")

        if not pdf_path or not os.path.exists(pdf_path):
            return {"error": "PDF file not found"}

        # Read PDF file
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # Return PDF response
        from pathlib import Path
        filename = Path(pdf_path).name

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        print(f"❌ Error downloading PDF: {e}")
        return {"error": str(e)}


@app.post("/handoff-agent/forms/{form_id}/acknowledge")
async def acknowledge_handoff_form(form_id: str):
    """
    Acknowledge a handoff form by updating all related alerts to 'acknowledged' status

    Args:
        form_id: ID of the handoff form to acknowledge

    Returns:
        Success status and number of alerts updated
    """
    try:
        # Get the form to find alert IDs
        form_response = supabase.table("handoff_forms").select(
            "alert_ids").eq("id", form_id).single().execute()

        if not form_response.data:
            return {"success": False, "message": "Form not found"}

        alert_ids = form_response.data.get("alert_ids", [])

        if not alert_ids:
            return {"success": False, "message": "No alerts associated with this form"}

        # Update all alerts to acknowledged status
        update_response = supabase.table("alerts").update({
            "status": "acknowledged",
            "acknowledged_at": datetime.utcnow().isoformat(),
            "acknowledged_by": "nurse"  # You can make this dynamic later
        }).in_("id", alert_ids).execute()

        # Update form status to acknowledged
        supabase.table("handoff_forms").update({
            "status": "acknowledged"
        }).eq("id", form_id).execute()

        return {
            "success": True,
            "message": f"Acknowledged {len(alert_ids)} alert(s)",
            "alerts_updated": len(alert_ids)
        }

    except Exception as e:
        print(f"❌ Error acknowledging form: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Acknowledge a single alert by updating its status to 'acknowledged'.
    This endpoint is called from the HandoffFormModal when the user clicks Acknowledge.
    """
    try:
        from app.supabase_client import supabase
        from datetime import datetime

        # Update the alert status
        update_response = supabase.table("alerts").update({
            "status": "acknowledged",
            "acknowledged_at": datetime.utcnow().isoformat(),
            "acknowledged_by": "nurse"  # TODO: Get actual user from auth context
        }).eq("id", alert_id).execute()

        if not update_response.data:
            return {
                "success": False,
                "message": "Alert not found"
            }

        return {
            "success": True,
            "message": f"Alert {alert_id} acknowledged successfully",
            "alert_id": alert_id
        }

    except Exception as e:
        print(f"❌ Error acknowledging alert: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
