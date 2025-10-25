"""
Haven AI - Backend API
FastAPI application serving pre-computed CV results and trial data
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
import json
from pathlib import Path
import os
from app.websocket import manager, process_frame_fast, process_frame_metrics
from app.supabase_client import supabase, SUPABASE_URL
from app.monitoring_protocols import get_all_protocols, recommend_protocols as keyword_recommend
from app.infisical_config import get_secret, secret_manager
from app.monitoring_control import monitoring_manager, MonitoringLevel
from app.patient_guardian_agent import patient_guardian
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


@app.post("/alerts/call")
async def trigger_voice_alert(request: SMSAlertRequest):
    """
    Make voice call with TTS alert via Vonage
    No 10DLC registration required - works immediately!

    Voice calls bypass SMS carrier restrictions
    """
    try:
        # Get Vonage credentials from secrets
        VONAGE_API_KEY = get_secret("VONAGE_API_KEY")
        VONAGE_API_SECRET = get_secret("VONAGE_API_SECRET")
        VONAGE_APPLICATION_ID = get_secret("VONAGE_APPLICATION_ID")
        VONAGE_PRIVATE_KEY = get_secret("VONAGE_PRIVATE_KEY")

        if not all([VONAGE_API_KEY, VONAGE_API_SECRET, VONAGE_APPLICATION_ID, VONAGE_PRIVATE_KEY]):
            # Mock mode for demos without credentials
            print(f"⚠️  Vonage Voice not fully configured - mock calling {request.phone_number}")
            print(f"   Message: {request.message}")
            return {
                "status": "success",
                "message": "Voice call placed (mock mode - Vonage Voice not configured)",
                "mock_sent": True,
                "to": request.phone_number,
                "note": "Voice API requires Vonage Application setup - see dashboard"
            }

        # Convert escaped newlines to actual newlines in private key
        private_key_formatted = VONAGE_PRIVATE_KEY.replace("\\n", "\n")

        # Import Vonage client (v4+ API)
        from vonage import Auth, Vonage
        
        # Create auth with application credentials for Voice API
        auth = Auth(
            api_key=VONAGE_API_KEY,
            api_secret=VONAGE_API_SECRET,
            application_id=VONAGE_APPLICATION_ID,
            private_key=private_key_formatted
        )
        client = Vonage(auth=auth)

        # Create voice call with TTS
        # NCCO = Nexmo Call Control Objects
        ncco = [
            {
                "action": "talk",
                "text": f"This is an urgent alert from Haven AI. {request.message}. I repeat: {request.message}. Please check the dashboard immediately.",
                "voiceName": "Amy",  # US English female voice
                "bargeIn": False  # Don't allow user to interrupt
            }
        ]

        # Remove '+' from phone numbers for Voice API
        to_number = request.phone_number.replace(
            "+", "").replace("-", "").replace(" ", "")

        response = client.voice.create_call({
            "to": [{"type": "phone", "number": to_number}],
            # Your Vonage number
            "from_": {"type": "phone", "number": "12178020876"},
            "ncco": ncco
        })

        # Extract call UUID from response object
        call_uuid = response.uuid if hasattr(response, 'uuid') else str(response)
        print(f"✅ Voice call placed to {request.phone_number}: {call_uuid}")

        return {
            "status": "success",
            "message": "Voice call placed successfully",
            "call_uuid": call_uuid,
            "to": request.phone_number,
            "type": "voice"
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
            print(f"⚠️  Vonage not configured - mock sending {request.channel} to {request.phone_number}")
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
        to_number = request.phone_number.replace("+", "").replace("-", "").replace(" ", "")
        
        # Build message based on channel
        message_data = {
            "to": to_number,
            "message_type": "text",
            "text": f"🚨 Haven Alert: {request.message}"
        }
        
        # Channel-specific configuration
        if request.channel == "whatsapp":
            message_data["from"] = "14157386102"  # WhatsApp Business number (Vonage sandbox)
            message_data["channel"] = "whatsapp"
        elif request.channel == "messenger":
            message_data["from"] = "107083064136738"  # Facebook Page ID (get from Vonage dashboard)
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
        print(f"⚠️  Vonage Messages API not installed - mock sending {request.channel} to {request.phone_number}")
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
    print(f"📩 Inbound message from {request.get('from')}: {request.get('message', {}).get('content', {}).get('text')}")
    
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
    print(f"📊 Message status update: {request.get('status')} for message {request.get('message_uuid')}")
    
    # TODO: Update alert delivery status in database
    # - delivered
    # - read
    # - failed
    
    return {"status": "received"}


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
    """Get list of all patients (first 47) - LEGACY"""
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

    Args:
        q: Search query string

    Returns:
        List of patients matching the search query
    """
    if not supabase:
        print("⚠️ Supabase not configured - returning empty patient list")
        return []

    try:
        if q:
            # Search by name (case-insensitive)
            print(f"🔍 Searching patients with query: '{q}'")
            response = supabase.table("patients") \
                .select("*") \
                .ilike("name", f"%{q}%") \
                .order("name") \
                .execute()
        else:
            # Return all patients if no search query
            print("📋 Fetching all patients")
            response = supabase.table("patients") \
                .select("*") \
                .order("name") \
                .limit(50) \
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
            return filtered_data
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
    Get alerts from database
    Optionally filter by status and/or severity
    """
    if not supabase:
        # Fallback to in-memory alerts if no database
        return alerts
    
    try:
        query = supabase.table("alerts").select("*")
        
        if status:
            query = query.eq("status", status)
        if severity:
            query = query.eq("severity", severity)
        
        response = query.order("triggered_at", desc=True).limit(limit).execute()
        
        return response.data or []
    except Exception as e:
        print(f"⚠️ Error fetching alerts from database: {e}")
        # Fallback to in-memory
        return alerts


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
        
        return result.data[0] if result.data else {}
    except Exception as e:
        print(f"❌ Error creating alert: {e}")
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
    Get list of patient IDs currently streaming

    Returns:
        {
            "active_streams": ["P-001", "P-003"],
            "count": 2
        }
    """
    active_patient_ids = list(manager.streamers.keys())
    return {
        "active_streams": active_patient_ids,
        "count": len(active_patient_ids)
    }


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
            assignment = supabase.table("patients_room").select("patient_id").eq("room_id", room_id).execute()
            if assignment.data:
                patient_id = assignment.data[0]['patient_id']
        
        # Generate PDF report if requested
        report_generated = False
        if generate_report and patient_id:
            try:
                from app.pdf_generator import generate_patient_discharge_report
                pdf_bytes = await generate_patient_discharge_report(patient_id, room_id)
                # Store PDF or trigger download
                print(f"✅ Generated discharge report for {patient_id} from {room_id}")
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
# Patient Guardian Agent Endpoints
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

    supabase_warning = None
    print(f"🎯 Incoming WebSocket connection for patient {patient_id}")

    # Accept connection immediately so client receives deterministic feedback
    await websocket.accept()
    print(f"✅ WebSocket connection accepted for patient {patient_id}")

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

    # Wait for initial handshake with monitoring conditions
    try:
        print(f"⏳ Waiting for handshake from patient {patient_id}...")
        initial_data = await websocket.receive_json()
        print(f"📨 Received handshake data: {initial_data}")

        monitoring_conditions = initial_data.get("monitoring_conditions", [])
        print(
            f"📋 Registering streamer for patient {patient_id} with conditions: {monitoring_conditions}")

        manager.register_streamer(patient_id, websocket, monitoring_conditions)
        print(f"✅ Streamer registered successfully for patient {patient_id}")
        print(
            f"📊 Total active streamers: {len(manager.streamers)} - {list(manager.streamers.keys())}")

        # Send acknowledgment
        await websocket.send_json({
            "type": "connected",
            "patient_id": patient_id,
            "monitoring_conditions": monitoring_conditions,
            "supabase_verified": supabase_warning is None,
            "warning": supabase_warning
        })
        print(f"📤 Sent acknowledgment to patient {patient_id}")
    except Exception as e:
        print(f"❌ Handshake error for patient {patient_id}: {e}")
        import traceback
        traceback.print_exc()
        manager.register_streamer(patient_id, websocket, [])
        print(f"✅ Registered streamer with empty conditions as fallback")

    try:
        frame_count = 0

        while True:
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
    except Exception as e:
        print(f"❌ Stream error for patient {patient_id}: {e}")
    finally:
        manager.unregister_streamer(patient_id)


@app.websocket("/ws/view")
async def websocket_view(websocket: WebSocket):
    """WebSocket endpoint for dashboard viewing"""
    await websocket.accept()
    manager.viewers.append(websocket)
    print(f"✅ Viewer connected. Total: {len(manager.viewers)}")

    try:
        import asyncio
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Viewer disconnected")
    finally:
        manager.disconnect(websocket)


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
                session_data = supabase.table("chat_sessions").select("title").eq("id", session_id).single().execute()
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
        
        # Build context-aware system prompt
        system_prompt = await build_system_prompt(context)
        
        # Call Anthropic API with tool use capability
        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system_prompt,
            tools=HAVEN_TOOLS,  # Enable tool calling
            messages=anthropic_messages
        )
        
        # Handle tool use
        assistant_response = ""
        tool_results = []
        
        # Check if Claude wants to use tools
        if message.stop_reason == "tool_use":
            # Execute tool calls
            tool_call_log = []
            for content_block in message.content:
                if content_block.type == "text":
                    assistant_response += content_block.text
                elif content_block.type == "tool_use":
                    print(f"\n🔧 Tool call: {content_block.name}")
                    print(f"   Input: {content_block.input}")
                    tool_result = await execute_tool(content_block.name, content_block.input)
                    print(f"   Result: {tool_result}")
                    
                    tool_call_log.append(f"{content_block.name}: {json.dumps(tool_result)}")
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": json.dumps(tool_result)
                    })
            
            print(f"\n📊 Tool execution summary:")
            for log in tool_call_log:
                print(f"   ✓ {log[:100]}...")
            
            # Build fresh system prompt emphasizing tool results are THE TRUTH
            tool_results_system = system_prompt + f"""

**CRITICAL: TOOL RESULTS ARE THE TRUTH**
The tool results above are FRESH from the database RIGHT NOW.
IGNORE any information from earlier in the conversation.
Base your response ONLY on the tool results you just received.
If tool says room is occupied, it IS occupied RIGHT NOW.
If tool says room is empty, it IS empty RIGHT NOW.
Previous tool calls may have changed the state - ONLY trust the latest tool results."""
            
            # Continue conversation with tool results
            anthropic_messages.append({
                "role": "assistant",
                "content": message.content
            })
            anthropic_messages.append({
                "role": "user",
                "content": tool_results
            })
            
            # Get final response with tool results
            final_message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                system=tool_results_system,  # Use modified prompt
                tools=HAVEN_TOOLS,
                messages=anthropic_messages
            )
            
            # Extract final text response
            for content_block in final_message.content:
                if content_block.type == "text":
                    assistant_response += content_block.text
        else:
            # No tool use, just get text response
            for content_block in message.content:
                if content_block.type == "text":
                    assistant_response = content_block.text
        
        # Add assistant response to context
        context.messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # Save updated context
        await write_context(session_id, context)
        
        # Check if any write operations were performed
        invalidate_cache = False
        cache_keys = set()
        
        print(f"\n📊 Checking {len(tool_results)} tool results for cache invalidation...")
        
        for tool_result in tool_results:
            result_data = json.loads(tool_result.get("content", "{}"))
            print(f"   Tool result: {result_data.get('success', False)} - {list(result_data.keys())[:3]}")
            
            if result_data.get("success"):
                invalidate_cache = True
                cache_keys.update(["rooms", "patients", "patients_room", "assignments"])
                print(f"   ✅ Success detected - will invalidate cache: rooms, patients, patients_room")
        
        cache_keys_list = list(cache_keys) if cache_keys else ["rooms", "patients"]
        
        print(f"\n{'='*60}")
        print(f"📤 Returning to frontend:")
        print(f"   invalidate_cache: {invalidate_cache}")
        print(f"   cache_keys: {cache_keys_list}")
        print(f"   tool_calls: {len(tool_results)}")
        print(f"{'='*60}\n")
        
        return {
            "response": assistant_response,
            "model": "claude-haiku-4.5",
            "session_id": session_id,
            "session_title": session_title,
            "tool_calls": len(tool_results) if tool_results else 0,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
