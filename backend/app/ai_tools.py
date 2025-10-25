"""
Haven AI Tools - Function calling for Anthropic Claude
Allows the AI to fetch real patient and room data from the database
"""

from typing import Dict, List, Any, Optional
from .supabase_client import supabase


# Tool definitions for Anthropic API
HAVEN_TOOLS = [
    {
        "name": "search_patients",
        "description": "Search for patients by name or patient ID. Returns patient details including name, age, condition, and room assignment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Patient name or patient ID to search for (e.g., 'Emily Martinez' or 'PT-042')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_patient_details",
        "description": "Get complete details for a specific patient including vitals, condition, room assignment, and active alerts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "The patient ID (e.g., 'PT-042')"
                }
            },
            "required": ["patient_id"]
        }
    },
    {
        "name": "get_room_status",
        "description": "Get status of a specific room including occupancy, assigned patient, and equipment status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "room_id": {
                    "type": "string",
                    "description": "The room identifier (e.g., 'Room 1' or 'room-1')"
                }
            },
            "required": ["room_id"]
        }
    },
    {
        "name": "list_occupied_rooms",
        "description": "List all currently occupied rooms with patient assignments.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_available_rooms",
        "description": "List all empty/available rooms ready for patient admission.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_active_alerts",
        "description": "Get all active alerts, optionally filtered by severity or patient.",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "description": "Filter by severity: 'critical', 'high', 'medium', 'low'",
                    "enum": ["critical", "high", "medium", "low"]
                },
                "patient_id": {
                    "type": "string",
                    "description": "Filter alerts for a specific patient ID"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_hospital_stats",
        "description": "Get overall hospital statistics including total patients, room occupancy, alert counts, and monitoring status.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_patients_by_condition",
        "description": "Find all patients with a specific medical condition or treatment status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "condition": {
                    "type": "string",
                    "description": "Medical condition or treatment (e.g., 'CAR-T', 'CRS', 'post-operative')"
                }
            },
            "required": ["condition"]
        }
    },
    {
        "name": "assign_patient_to_room",
        "description": "Assign a patient to a specific room. Use only when explicitly requested by clinical staff.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID to assign"
                },
                "room_id": {
                    "type": "string",
                    "description": "Room ID to assign to"
                }
            },
            "required": ["patient_id", "room_id"]
        }
    },
    {
        "name": "get_crs_monitoring_protocol",
        "description": "Get the Cytokine Release Syndrome (CRS) monitoring protocol with grade-specific guidelines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "grade": {
                    "type": "string",
                    "description": "CRS grade (1, 2, 3, or 4)",
                    "enum": ["1", "2", "3", "4"]
                }
            },
            "required": []
        }
    }
]


# Tool execution functions
async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool call and return results
    """
    try:
        if tool_name == "search_patients":
            return await search_patients(tool_input.get("query", ""))
        
        elif tool_name == "get_patient_details":
            return await get_patient_details(tool_input.get("patient_id", ""))
        
        elif tool_name == "get_room_status":
            return await get_room_status(tool_input.get("room_id", ""))
        
        elif tool_name == "list_occupied_rooms":
            return await list_occupied_rooms()
        
        elif tool_name == "list_available_rooms":
            return await list_available_rooms()
        
        elif tool_name == "get_active_alerts":
            return await get_active_alerts(
                severity=tool_input.get("severity"),
                patient_id=tool_input.get("patient_id")
            )
        
        elif tool_name == "get_hospital_stats":
            return await get_hospital_stats()
        
        elif tool_name == "get_patients_by_condition":
            return await get_patients_by_condition(tool_input.get("condition", ""))
        
        elif tool_name == "assign_patient_to_room":
            return await assign_patient_to_room_tool(
                tool_input.get("patient_id", ""),
                tool_input.get("room_id", "")
            )
        
        elif tool_name == "get_crs_monitoring_protocol":
            return await get_crs_monitoring_protocol(tool_input.get("grade"))
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        print(f"❌ Error executing tool {tool_name}: {e}")
        return {"error": str(e)}


# Individual tool implementations
async def search_patients(query: str) -> Dict[str, Any]:
    """Search for patients by name or ID"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Search by patient_id or name
        response = supabase.table("patients").select("*").or_(
            f"patient_id.ilike.%{query}%,name.ilike.%{query}%"
        ).limit(5).execute()
        
        patients = response.data or []
        
        # Enrich with room assignments
        for patient in patients:
            room_assignment = supabase.table("patients_room").select("room_id").eq("patient_id", patient["patient_id"]).execute()
            if room_assignment.data:
                room_id = room_assignment.data[0]["room_id"]
                room_data = supabase.table("rooms").select("room_name").eq("room_id", room_id).execute()
                if room_data.data:
                    patient["current_room"] = room_data.data[0]["room_name"]
        
        return {
            "patients": patients,
            "count": len(patients)
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_patient_details(patient_id: str) -> Dict[str, Any]:
    """Get complete patient details"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get patient info
        patient_response = supabase.table("patients").select("*").eq("patient_id", patient_id).single().execute()
        
        if not patient_response.data:
            return {"error": f"Patient {patient_id} not found"}
        
        patient = patient_response.data
        
        # Get room assignment
        room_assignment = supabase.table("patients_room").select("room_id, assigned_at").eq("patient_id", patient_id).execute()
        if room_assignment.data:
            room_id = room_assignment.data[0]["room_id"]
            room_data = supabase.table("rooms").select("room_name, room_type").eq("room_id", room_id).execute()
            if room_data.data:
                patient["current_room"] = room_data.data[0]
                patient["assigned_at"] = room_assignment.data[0]["assigned_at"]
        
        # Get active alerts for this patient
        alerts_response = supabase.table("alerts").select("*").eq("patient_id", patient_id).eq("status", "active").execute()
        patient["active_alerts"] = alerts_response.data or []
        
        return patient
    
    except Exception as e:
        return {"error": str(e)}


async def get_room_status(room_id: str) -> Dict[str, Any]:
    """Get room status and occupancy"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get room info
        room_response = supabase.table("rooms").select("*").eq("room_id", room_id).execute()
        
        if not room_response.data:
            return {"error": f"Room {room_id} not found"}
        
        room = room_response.data[0]
        
        # Check if occupied
        assignment = supabase.table("patients_room").select("patient_id, assigned_at").eq("room_id", room_id).execute()
        
        if assignment.data:
            patient_id = assignment.data[0]["patient_id"]
            patient_data = supabase.table("patients").select("name, age, condition").eq("patient_id", patient_id).execute()
            if patient_data.data:
                room["assigned_patient"] = patient_data.data[0]
                room["assigned_at"] = assignment.data[0]["assigned_at"]
                room["status"] = "occupied"
        else:
            room["status"] = "available"
        
        return room
    
    except Exception as e:
        return {"error": str(e)}


async def list_occupied_rooms() -> Dict[str, Any]:
    """List all occupied rooms"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get all room assignments
        assignments = supabase.table("patients_room").select("room_id, patient_id, assigned_at").execute()
        
        occupied_rooms = []
        for assignment in (assignments.data or []):
            # Get room details
            room_data = supabase.table("rooms").select("room_name, room_type").eq("room_id", assignment["room_id"]).execute()
            # Get patient details
            patient_data = supabase.table("patients").select("name, condition").eq("patient_id", assignment["patient_id"]).execute()
            
            if room_data.data and patient_data.data:
                occupied_rooms.append({
                    "room_id": assignment["room_id"],
                    "room_name": room_data.data[0]["room_name"],
                    "patient_name": patient_data.data[0]["name"],
                    "patient_id": assignment["patient_id"],
                    "condition": patient_data.data[0]["condition"],
                    "assigned_at": assignment["assigned_at"]
                })
        
        return {
            "occupied_rooms": occupied_rooms,
            "count": len(occupied_rooms)
        }
    
    except Exception as e:
        return {"error": str(e)}


async def list_available_rooms() -> Dict[str, Any]:
    """List all available rooms"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get all patient rooms
        all_rooms = supabase.table("rooms").select("room_id, room_name, room_type").eq("room_type", "patient").execute()
        
        # Get occupied room IDs
        assignments = supabase.table("patients_room").select("room_id").execute()
        occupied_ids = set(a["room_id"] for a in (assignments.data or []))
        
        # Filter to only available rooms
        available_rooms = [
            room for room in (all_rooms.data or [])
            if room["room_id"] not in occupied_ids
        ]
        
        return {
            "available_rooms": available_rooms,
            "count": len(available_rooms)
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_active_alerts(severity: Optional[str] = None, patient_id: Optional[str] = None) -> Dict[str, Any]:
    """Get active alerts with optional filters"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        query = supabase.table("alerts").select("*").eq("status", "active")
        
        if severity:
            query = query.eq("severity", severity)
        if patient_id:
            query = query.eq("patient_id", patient_id)
        
        response = query.order("triggered_at", desc=True).limit(10).execute()
        
        return {
            "alerts": response.data or [],
            "count": len(response.data or [])
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_hospital_stats() -> Dict[str, Any]:
    """Get overall hospital statistics"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Count total patients
        patients = supabase.table("patients").select("id", count='exact').eq("enrollment_status", "active").execute()
        total_patients = patients.count if patients.count else 0
        
        # Count total rooms
        rooms = supabase.table("rooms").select("id", count='exact').eq("room_type", "patient").execute()
        total_rooms = rooms.count if rooms.count else 0
        
        # Count occupied rooms
        assignments = supabase.table("patients_room").select("room_id", count='exact').execute()
        occupied_rooms = assignments.count if assignments.count else 0
        
        # Count active alerts by severity
        alerts = supabase.table("alerts").select("severity").eq("status", "active").execute()
        alert_counts = {}
        for alert in (alerts.data or []):
            sev = alert.get("severity", "unknown")
            alert_counts[sev] = alert_counts.get(sev, 0) + 1
        
        return {
            "total_patients": total_patients,
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "available_rooms": total_rooms - occupied_rooms,
            "occupancy_rate": round((occupied_rooms / total_rooms * 100), 1) if total_rooms > 0 else 0,
            "alerts": alert_counts,
            "total_alerts": sum(alert_counts.values())
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_patients_by_condition(condition: str) -> Dict[str, Any]:
    """Find patients by condition"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        response = supabase.table("patients").select("*").ilike("condition", f"%{condition}%").limit(10).execute()
        
        patients = response.data or []
        
        # Enrich with room info
        for patient in patients:
            room_assignment = supabase.table("patients_room").select("room_id").eq("patient_id", patient["patient_id"]).execute()
            if room_assignment.data:
                room_id = room_assignment.data[0]["room_id"]
                room_data = supabase.table("rooms").select("room_name").eq("room_id", room_id).execute()
                if room_data.data:
                    patient["current_room"] = room_data.data[0]["room_name"]
        
        return {
            "patients": patients,
            "condition_searched": condition,
            "count": len(patients)
        }
    
    except Exception as e:
        return {"error": str(e)}


async def assign_patient_to_room_tool(patient_id: str, room_id: str) -> Dict[str, Any]:
    """Assign patient to room (write operation)"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Check if room is available
        existing = supabase.table("patients_room").select("*").eq("room_id", room_id).execute()
        if existing.data:
            return {"error": f"Room {room_id} is already occupied"}
        
        # Check if patient exists
        patient = supabase.table("patients").select("name").eq("patient_id", patient_id).execute()
        if not patient.data:
            return {"error": f"Patient {patient_id} not found"}
        
        # Create assignment
        result = supabase.table("patients_room").insert({
            "room_id": room_id,
            "patient_id": patient_id,
            "assigned_by": "Haven AI"
        }).execute()
        
        return {
            "success": True,
            "message": f"Assigned {patient_id} to {room_id}",
            "patient_id": patient_id,
            "room_id": room_id
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_crs_monitoring_protocol(grade: Optional[str] = None) -> Dict[str, Any]:
    """Get CRS monitoring protocol"""
    
    protocol = {
        "overview": "Cytokine Release Syndrome (CRS) monitoring protocol for CAR-T therapy patients",
        "grades": {
            "1-2": {
                "vitals": "q4h monitoring",
                "labs": "q24h (CBC, CMP, LDH, ferritin)",
                "interventions": ["Acetaminophen for fever", "Aggressive fluid management", "Close observation"]
            },
            "3-4": {
                "vitals": "Continuous monitoring",
                "location": "ICU transfer required",
                "labs": "q6h labs + coagulation panel",
                "interventions": ["Tocilizumab ± steroids", "Vasopressor support", "Mechanical ventilation standby"]
            }
        },
        "key_triggers": [
            "Fever >38.5°C",
            "Hypotension",
            "Tachycardia",
            "Respiratory distress",
            "Altered mental status"
        ],
        "discharge_criteria": [
            "Afebrile × 24h",
            "Stable vitals",
            "Improving labs",
            "No active interventions"
        ]
    }
    
    if grade:
        if grade in ["1", "2"]:
            return {"grade": "1-2", "protocol": protocol["grades"]["1-2"], "triggers": protocol["key_triggers"]}
        elif grade in ["3", "4"]:
            return {"grade": "3-4", "protocol": protocol["grades"]["3-4"], "triggers": protocol["key_triggers"]}
    
    return protocol

