"""
TrialSentinel AI - Backend API
FastAPI application serving pre-computed CV results and trial data
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from pathlib import Path
import os
from app.websocket import manager, process_frame_fast, process_frame_metrics
from app.supabase_client import supabase, SUPABASE_URL
from app.monitoring_protocols import get_all_protocols, recommend_protocols as keyword_recommend
from app.infisical_config import get_secret, secret_manager
from app.monitoring_control import monitoring_manager, MonitoringLevel
from app.patient_guardian_agent import patient_guardian

# Try to import anthropic for LLM recommendations
try:
    import anthropic
    ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except ImportError:
    anthropic_client = None

app = FastAPI(
    title="TrialSentinel AI",
    description="Real-time computer vision monitoring for clinical trial safety",
    version="1.0.0"
)

# CORS for frontend - allows browser WebSocket connections from production and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://use-haven.vercel.app",  # Production frontend
        "http://localhost:3000",          # Local development
        "http://localhost:3001",          # Alternative local port
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

# Load trial protocol
trial_protocol = {}
protocol_file = DATA_DIR / "nct04649359.json"
if protocol_file.exists():
    with open(protocol_file, "r") as f:
        trial_protocol = json.load(f)

# Print secret manager status after all imports
@app.on_event("startup")
async def startup_event():
    """Print configuration status on startup"""
    secret_manager.print_status()
    
    # Print service status
    print("🚀 TrialSentinel Backend Services:")
    print(f"   • Supabase: {'✅ Connected' if supabase else '❌ Not configured'}")
    if supabase and SUPABASE_URL:
        print(f"     └─ {SUPABASE_URL}")
    print(f"   • Anthropic AI: {'✅ Enabled' if anthropic_client else '⚠️  Disabled (using keyword matching)'}")
    print(f"   • CV Data: {'✅ Loaded' if cv_results else '⚠️  Not loaded'}")
    print(f"   • Patients: {'✅ Loaded (' + str(len(patients)) + ')' if patients else '⚠️  Not loaded'}")
    print(f"   • Trial Protocol: {'✅ Loaded' if trial_protocol else '⚠️  Not loaded'}")
    print("\n✅ Backend ready!\n")

# In-memory alert storage
alerts = []


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "TrialSentinel AI",
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
                .eq("enrollment_status", "active") \
                .order("name") \
                .execute()
        else:
            # Return all active patients if no search query
            print("📋 Fetching all active patients")
            response = supabase.table("patients") \
                .select("*") \
                .eq("enrollment_status", "active") \
                .order("name") \
                .limit(50) \
                .execute()

        result_count = len(response.data) if response.data else 0
        print(f"✅ Found {result_count} patients")
        return response.data if response.data else []
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
        all_response = supabase.table("patients").select("*").limit(10).execute()

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
        closest_time = min(available_times, key=lambda t: abs(t - timestamp_float))
        closest_time_str = str(closest_time) if closest_time == int(closest_time) else f"{closest_time:.1f}"

        data = patient_data.get(closest_time_str, patient_data.get(str(int(closest_time))))

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
async def get_alerts():
    """Get all active alerts"""
    return alerts


@app.delete("/alerts")
async def clear_alerts():
    """Clear all alerts"""
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
    """Calculate ROI metrics for TrialSentinel"""
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
                model="claude-3-5-sonnet-20241022",
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
            print(f"LLM recommendation error: {e}, falling back to keyword matching")
            # Fall through to keyword matching

    # Keyword-based fallback
    recommended = keyword_recommend(request.condition)
    return {
        "recommended": recommended,
        "reasoning": f"Keyword matching detected relevant terms in patient condition: {request.condition}",
        "method": "keyword"
    }


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
    config = monitoring_manager.set_enhanced_monitoring(patient_id, duration_minutes, reason)

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

    # Verify patient exists in Supabase before accepting connection
    if supabase:
        try:
            patient = supabase.table("patients") \
                .select("*") \
                .eq("patient_id", patient_id) \
                .single() \
                .execute()

            if not patient.data:
                await websocket.close(code=1008, reason=f"Patient {patient_id} not found")
                print(f"❌ Connection rejected: Patient {patient_id} not found")
                return
        except Exception as e:
            await websocket.close(code=1011, reason="Database error")
            print(f"❌ Database error verifying patient {patient_id}: {e}")
            return

    # Check if patient is already streaming
    if patient_id in manager.streamers:
        await websocket.close(code=1008, reason=f"Patient {patient_id} is already streaming")
        print(f"❌ Connection rejected: Patient {patient_id} already has an active stream")
        return

    # Accept connection and register streamer
    await websocket.accept()

    # Wait for initial handshake with monitoring conditions
    try:
        initial_data = await websocket.receive_json()
        monitoring_conditions = initial_data.get("monitoring_conditions", [])
        manager.register_streamer(patient_id, websocket, monitoring_conditions)
        print(f"📋 Patient {patient_id} monitoring conditions: {monitoring_conditions}")

        # Send acknowledgment
        await websocket.send_json({
            "type": "connected",
            "patient_id": patient_id,
            "monitoring_conditions": monitoring_conditions
        })
    except Exception as e:
        print(f"❌ Handshake error for patient {patient_id}: {e}")
        manager.register_streamer(patient_id, websocket, [])

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
                # Queue every 2nd frame (15 FPS) to avoid overwhelming the worker
                if frame_count % 2 == 0:
                    manager.queue_frame_for_processing(patient_id, raw_frame, frame_count)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
