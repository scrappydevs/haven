"""
TrialSentinel AI - Backend API
FastAPI application serving pre-computed CV results and trial data
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from pathlib import Path
from app.websocket import manager, process_frame

app = FastAPI(
    title="TrialSentinel AI",
    description="Real-time computer vision monitoring for clinical trial safety",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://trialsentinel.vercel.app"]
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
    """Get list of all patients (first 47)"""
    return patients[:47]


@app.get("/patient/{patient_id}")
async def get_patient(patient_id: int):
    """Get single patient details"""
    for patient in patients:
        if patient["id"] == patient_id:
            return patient
    return {"error": "Patient not found"}


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


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for computers streaming webcam
    Receives frames, processes with CV, broadcasts to viewers
    """
    await manager.connect_streamer(websocket)
    frame_count = 0
    try:
        while True:
            # Receive frame from streamer
            data = await websocket.receive_json()
            
            frame_count += 1
            if frame_count % 30 == 0:  # Log every 30th frame
                print(f"📦 Received frame #{frame_count} from streamer")

            if data.get("type") == "frame":
                # Process frame with computer vision
                result = process_frame(data.get("frame"))
                
                if frame_count % 30 == 0:
                    print(f"✨ Processed frame, CRS: {result.get('crs_score', 0)}, broadcasting to {len(manager.viewers)} viewers")

                # Broadcast to all dashboard viewers
                await manager.broadcast_frame({
                    "type": "live_frame",
                    "patient_id": "live-1",
                    "data": result
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Streamer disconnected")
    except Exception as e:
        print(f"❌ Error in stream endpoint: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/view")
async def websocket_view(websocket: WebSocket):
    """
    WebSocket endpoint for dashboards viewing live stream
    Receives processed frames from backend
    """
    await manager.connect_viewer(websocket)
    try:
        # Keep connection alive - just wait forever
        # Frames are sent via broadcast_frame(), not through this loop
        import asyncio
        while True:
            await asyncio.sleep(1)  # Keep alive, don't wait for messages
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Viewer disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
