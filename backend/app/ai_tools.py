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
    },
    {
        "name": "remove_patient_from_room",
        "description": "Remove a patient from a room. Can use either patient_id OR room_id - will auto-detect patient if only room is provided.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID to remove (e.g., 'P-001'). Optional if room_id is provided."
                },
                "room_id": {
                    "type": "string",
                    "description": "Room to empty (e.g., 'room-1' or 'Room 1'). AI will find who's in this room."
                },
                "generate_report": {
                    "type": "boolean",
                    "description": "Whether to generate discharge report PDF (default: true)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_patient_in_room",
        "description": "Find out which patient is currently assigned to a specific room.",
        "input_schema": {
            "type": "object",
            "properties": {
                "room_id": {
                    "type": "string",
                    "description": "Room identifier (e.g., 'room-1' or 'Room 1')"
                }
            },
            "required": ["room_id"]
        }
    },
    {
        "name": "transfer_patient",
        "description": "Transfer a patient from one room to another. Use when staff requests to move a patient to a different room.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID to transfer"
                },
                "from_room_id": {
                    "type": "string",
                    "description": "Current room ID (optional - will auto-detect if not provided)"
                },
                "to_room_id": {
                    "type": "string",
                    "description": "Destination room ID"
                }
            },
            "required": ["patient_id", "to_room_id"]
        }
    },
    {
        "name": "get_patient_current_room",
        "description": "Get the current room assignment for a specific patient.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID to look up"
                }
            },
            "required": ["patient_id"]
        }
    },
    {
        "name": "suggest_optimal_room",
        "description": "Suggest the best available room for a patient based on their condition and current room availability.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID needing room assignment"
                }
            },
            "required": ["patient_id"]
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
        
        elif tool_name == "remove_patient_from_room":
            return await remove_patient_from_room_tool(
                tool_input.get("patient_id"),
                tool_input.get("room_id"),
                tool_input.get("generate_report", True)
            )
        
        elif tool_name == "get_patient_in_room":
            return await get_patient_in_room_tool(tool_input.get("room_id", ""))
        
        elif tool_name == "transfer_patient":
            return await transfer_patient_tool(
                tool_input.get("patient_id", ""),
                tool_input.get("to_room_id", ""),
                tool_input.get("from_room_id")
            )
        
        elif tool_name == "get_patient_current_room":
            return await get_patient_room_tool(tool_input.get("patient_id", ""))
        
        elif tool_name == "suggest_optimal_room":
            return await suggest_optimal_room_tool(tool_input.get("patient_id", ""))
        
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


async def remove_patient_from_room_tool(patient_id: Optional[str] = None, room_id: Optional[str] = None, generate_report: bool = True) -> Dict[str, Any]:
    """Remove patient from room - accepts either patient_id OR room_id"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # If room_id provided, find patient in that room
        if room_id and not patient_id:
            # Search by room_name or room_id
            room_search = supabase.table("rooms").select("room_id").or_(f"room_id.eq.{room_id},room_name.ilike.%{room_id}%").execute()
            
            if room_search.data:
                actual_room_id = room_search.data[0]['room_id']
                assignment = supabase.table("patients_room").select("patient_id").eq("room_id", actual_room_id).execute()
                
                if not assignment.data:
                    room_name_data = supabase.table("rooms").select("room_name").eq("room_id", actual_room_id).execute()
                    room_name = room_name_data.data[0]['room_name'] if room_name_data.data else room_id
                    return {"error": f"{room_name} is already empty — no patient currently assigned"}
                
                patient_id = assignment.data[0]['patient_id']
                room_id = actual_room_id
            else:
                return {"error": f"Room '{room_id}' not found"}
        
        # If patient_id provided, find their current room
        elif patient_id and not room_id:
            assignment = supabase.table("patients_room").select("room_id").eq("patient_id", patient_id).execute()
            
            if not assignment.data:
                return {"error": f"Patient {patient_id} is not currently in any room"}
            
            room_id = assignment.data[0]['room_id']
        
        elif not patient_id and not room_id:
            return {"error": "Must provide either patient_id or room_id"}
        
        # Get patient and room names for response
        patient_data = supabase.table("patients").select("name").eq("patient_id", patient_id).execute()
        patient_name = patient_data.data[0]['name'] if patient_data.data else patient_id
        
        room_data = supabase.table("rooms").select("room_name").eq("room_id", room_id).execute()
        room_name = room_data.data[0]['room_name'] if room_data.data else room_id
        
        # Remove assignment
        supabase.table("patients_room").delete().eq("patient_id", patient_id).execute()
        
        result = {
            "success": True,
            "message": f"Removed {patient_name} ({patient_id}) from {room_name}",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "room_id": room_id,
            "room_name": room_name
        }
        
        if generate_report:
            result["report_available"] = True
            result["report_url"] = f"/reports/discharge/{patient_id}/{room_id}"
            result["report_message"] = "Discharge report generated and ready for download"
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


async def transfer_patient_tool(patient_id: str, to_room_id: str, from_room_id: Optional[str] = None) -> Dict[str, Any]:
    """Transfer patient from one room to another"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Auto-detect current room if not provided
        if not from_room_id:
            assignment = supabase.table("patients_room").select("room_id").eq("patient_id", patient_id).execute()
            if assignment.data:
                from_room_id = assignment.data[0]['room_id']
            else:
                return {"error": f"Patient {patient_id} is not currently in any room"}
        
        # Check if destination room is available
        dest_check = supabase.table("patients_room").select("*").eq("room_id", to_room_id).execute()
        if dest_check.data:
            return {"error": f"Destination room {to_room_id} is already occupied"}
        
        # Get room names
        from_room_data = supabase.table("rooms").select("room_name").eq("room_id", from_room_id).execute()
        to_room_data = supabase.table("rooms").select("room_name").eq("room_id", to_room_id).execute()
        
        from_room_name = from_room_data.data[0]['room_name'] if from_room_data.data else from_room_id
        to_room_name = to_room_data.data[0]['room_name'] if to_room_data.data else to_room_id
        
        # Remove from old room
        supabase.table("patients_room").delete().eq("patient_id", patient_id).execute()
        
        # Add to new room
        supabase.table("patients_room").insert({
            "room_id": to_room_id,
            "patient_id": patient_id,
            "assigned_by": "Haven AI"
        }).execute()
        
        return {
            "success": True,
            "message": f"Transferred patient {patient_id} from {from_room_name} to {to_room_name}",
            "patient_id": patient_id,
            "from_room": from_room_name,
            "to_room": to_room_name
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_patient_room_tool(patient_id: str) -> Dict[str, Any]:
    """Get patient's current room"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        assignment = supabase.table("patients_room").select("room_id, assigned_at").eq("patient_id", patient_id).execute()
        
        if not assignment.data:
            return {
                "patient_id": patient_id,
                "in_room": False,
                "message": f"Patient {patient_id} is not currently assigned to any room"
            }
        
        room_id = assignment.data[0]['room_id']
        room_data = supabase.table("rooms").select("*").eq("room_id", room_id).execute()
        
        if room_data.data:
            return {
                "patient_id": patient_id,
                "in_room": True,
                "room_id": room_id,
                "room_name": room_data.data[0]['room_name'],
                "room_type": room_data.data[0]['room_type'],
                "assigned_at": assignment.data[0]['assigned_at']
            }
        
        return {"error": "Room data not found"}
    
    except Exception as e:
        return {"error": str(e)}


async def get_patient_in_room_tool(room_id: str) -> Dict[str, Any]:
    """Find which patient is in a specific room"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Search for room by name or ID
        room_search = supabase.table("rooms").select("room_id, room_name").or_(f"room_id.eq.{room_id},room_name.ilike.%{room_id}%").execute()
        
        if not room_search.data:
            return {"error": f"Room '{room_id}' not found"}
        
        actual_room_id = room_search.data[0]['room_id']
        room_name = room_search.data[0]['room_name']
        
        # Check for patient assignment
        assignment = supabase.table("patients_room").select("patient_id, assigned_at").eq("room_id", actual_room_id).execute()
        
        if not assignment.data:
            return {
                "room_id": actual_room_id,
                "room_name": room_name,
                "occupied": False,
                "message": f"{room_name} is currently empty"
            }
        
        patient_id = assignment.data[0]['patient_id']
        
        # Get patient details
        patient = supabase.table("patients").select("name, age, condition").eq("patient_id", patient_id).execute()
        
        if patient.data:
            return {
                "room_id": actual_room_id,
                "room_name": room_name,
                "occupied": True,
                "patient_id": patient_id,
                "patient_name": patient.data[0]['name'],
                "patient_age": patient.data[0]['age'],
                "patient_condition": patient.data[0]['condition'],
                "assigned_at": assignment.data[0]['assigned_at']
            }
        
        return {"error": "Patient data not found"}
    
    except Exception as e:
        return {"error": str(e)}


async def suggest_optimal_room_tool(patient_id: str) -> Dict[str, Any]:
    """Suggest best available room for patient"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get patient info
        patient = supabase.table("patients").select("condition").eq("patient_id", patient_id).execute()
        if not patient.data:
            return {"error": f"Patient {patient_id} not found"}
        
        condition = patient.data[0].get('condition', '').lower()
        
        # Get all patient rooms
        all_rooms = supabase.table("rooms").select("room_id, room_name, room_type").eq("room_type", "patient").execute()
        
        # Get occupied room IDs
        assignments = supabase.table("patients_room").select("room_id").execute()
        occupied_ids = set(a["room_id"] for a in (assignments.data or []))
        
        # Filter to available rooms
        available_rooms = [
            room for room in (all_rooms.data or [])
            if room["room_id"] not in occupied_ids
        ]
        
        if not available_rooms:
            return {"error": "No available rooms", "suggestion": "All patient rooms are currently occupied"}
        
        # Simple suggestion logic - could be enhanced with more criteria
        suggested_room = available_rooms[0]  # For now, just suggest first available
        
        return {
            "patient_id": patient_id,
            "patient_condition": patient.data[0].get('condition'),
            "suggested_room": suggested_room['room_name'],
            "suggested_room_id": suggested_room['room_id'],
            "reason": "Next available patient room",
            "total_available": len(available_rooms),
            "other_options": [r['room_name'] for r in available_rooms[1:3]]  # Show 2 alternatives
        }
    
    except Exception as e:
        return {"error": str(e)}

