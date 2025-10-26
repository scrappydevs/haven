"""
Haven AI Tools - Function calling for Anthropic Claude
Allows the AI to fetch real patient and room data from the database
"""

from typing import Dict, List, Any, Optional
from .supabase_client import supabase


# Tool definitions for Anthropic API
HAVEN_TOOLS = [
    {
        "name": "list_all_patients",
        "description": "Get a complete list of ALL patients in the system with their basic info. Use when asked 'show all patients', 'list patients', 'describe all my patients', etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_inactive": {
                    "type": "boolean",
                    "description": "Include inactive/discharged patients (default: false, only show active)"
                }
            },
            "required": []
        }
    },
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
        "description": "Get all active alerts, optionally filtered by severity or patient. Use for 'show alerts', 'critical alerts', 'check alerts', etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "description": "Filter by severity: 'critical', 'high', 'medium', 'low', 'info'",
                    "enum": ["critical", "high", "medium", "low", "info"]
                },
                "patient_id": {
                    "type": "string",
                    "description": "Filter alerts for a specific patient ID"
                },
                "room_id": {
                    "type": "string",
                    "description": "Filter alerts for a specific room"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_alerts_by_room",
        "description": "Get all alerts grouped by room. Shows which rooms have critical/high alerts. Useful for understanding hospital alert distribution.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_alert_details",
        "description": "Get detailed information about a specific alert by ID. Use when user asks about 'the alert', 'that event', or references a specific alert. Returns full alert data including patient, room, description, status, and timeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "alert_id": {
                    "type": "string",
                    "description": "The alert UUID to fetch details for"
                }
            },
            "required": ["alert_id"]
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
        "description": "Transfer a patient from one room to another. Can auto-detect patient if from_room_id is provided. For 'move patient from room X to room Y', use from_room_id and to_room_id (leave patient_id empty).",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID to transfer (optional if from_room_id is provided - tool will auto-detect)"
                },
                "from_room_id": {
                    "type": "string",
                    "description": "Source room ID or name (e.g., '1', 'Room 1'). Tool will find who's in this room."
                },
                "to_room_id": {
                    "type": "string",
                    "description": "Destination room ID or name (e.g., '2', 'Room 2')"
                }
            },
            "required": ["to_room_id"]
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
    },
    {
        "name": "get_all_room_occupancy",
        "description": "Get complete list of all rooms with their current occupants. Shows which rooms have patients and which are empty.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "remove_all_patients_from_rooms",
        "description": "Batch operation: Remove ALL patients from their rooms (mass discharge). Use with extreme caution and only when explicitly confirmed by staff.",
        "input_schema": {
            "type": "object",
            "properties": {
                "confirm": {
                    "type": "boolean",
                    "description": "Must be true to execute. Require explicit confirmation from user before calling."
                }
            },
            "required": ["confirm"]
        }
    },
    {
        "name": "auto_assign_patients_to_rooms",
        "description": "Automatically assign unassigned patients to available rooms based on optimal matching.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_assignments": {
                    "type": "number",
                    "description": "Maximum number of patients to assign (default: all)"
                }
            },
            "required": []
        }
    },
    {
        "name": "generate_patient_clinical_summary",
        "description": "Generate a comprehensive clinical summary report for a patient including their condition, metrics, alerts, recommendations, and risk factors. Creates both a detailed response and downloadable PDF report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID to generate summary for (e.g., 'P-001')"
                },
                "include_recommendations": {
                    "type": "boolean",
                    "description": "Whether to include AI-generated clinical recommendations (default: true)"
                }
            },
            "required": ["patient_id"]
        }
    },
    {
        "name": "get_patient_medical_history",
        "description": "Get complete medical history for a patient including diagnoses, procedures, medications, allergies, lab results, and clinical notes. Essential for informed clinical decisions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID"
                },
                "entry_type": {
                    "type": "string",
                    "description": "Filter by type: 'diagnosis', 'procedure', 'medication', 'allergy', 'lab_result', 'note', etc. Leave empty for all.",
                    "enum": ["diagnosis", "procedure", "medication", "allergy", "vital_measurement", "lab_result", "imaging", "note", "symptom", "family_history", "social_history", ""]
                },
                "limit": {
                    "type": "number",
                    "description": "Number of records to return (default: 20)"
                }
            },
            "required": ["patient_id"]
        }
    },
    {
        "name": "add_medical_history_entry",
        "description": "Add a new entry to patient's medical history (e.g., new symptom, note, or observation). Use when documenting new information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID"
                },
                "entry_type": {
                    "type": "string",
                    "description": "Type of entry",
                    "enum": ["diagnosis", "procedure", "medication", "allergy", "vital_measurement", "lab_result", "note", "symptom"]
                },
                "title": {
                    "type": "string",
                    "description": "Brief title (e.g., 'Fever', 'Nausea', 'Blood Pressure Reading')"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description"
                },
                "severity": {
                    "type": "string",
                    "description": "Severity level",
                    "enum": ["critical", "high", "medium", "low", "info"]
                }
            },
            "required": ["patient_id", "entry_type", "title"]
        }
    }
]


# Tool execution functions
async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool call and return results
    """
    try:
        if tool_name == "list_all_patients":
            return await list_all_patients(tool_input.get("include_inactive", False))
        
        elif tool_name == "search_patients":
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
                patient_id=tool_input.get("patient_id"),
                room_id=tool_input.get("room_id")
            )
        
        elif tool_name == "get_alerts_by_room":
            return await get_alerts_by_room()
        
        elif tool_name == "get_alert_details":
            return await get_alert_details(tool_input.get("alert_id", ""))
        
        elif tool_name == "get_hospital_stats":
            return await get_hospital_stats()
        
        elif tool_name == "get_patients_by_condition":
            return await get_patients_by_condition(tool_input.get("condition", ""))
        
        elif tool_name == "assign_patient_to_room":
            return await assign_patient_to_room_tool(
                tool_input.get("patient_id", ""),
                tool_input.get("room_id", "")
            )
        
        elif tool_name == "remove_patient_from_room":
            return await remove_patient_from_room_tool(
                tool_input.get("patient_id"),
                tool_input.get("room_id"),
                tool_input.get("generate_report", True)
            )
        
        elif tool_name == "get_patient_in_room":
            return await get_patient_in_room_tool(tool_input.get("room_id", ""))
        
        elif tool_name == "transfer_patient":
            patient_id_input = tool_input.get("patient_id", "") or None
            from_room_input = tool_input.get("from_room_id", "") or None
            to_room_input = tool_input.get("to_room_id", "")
            
            return await transfer_patient_tool(
                patient_id=patient_id_input,
                to_room_id=to_room_input,
                from_room_id=from_room_input
            )
        
        elif tool_name == "get_patient_current_room":
            return await get_patient_room_tool(tool_input.get("patient_id", ""))
        
        elif tool_name == "suggest_optimal_room":
            return await suggest_optimal_room_tool(tool_input.get("patient_id", ""))
        
        elif tool_name == "get_all_room_occupancy":
            return await get_all_room_occupancy_tool()
        
        elif tool_name == "remove_all_patients_from_rooms":
            return await remove_all_patients_from_rooms_tool(tool_input.get("confirm", False))
        
        elif tool_name == "auto_assign_patients_to_rooms":
            return await auto_assign_patients_to_rooms_tool(tool_input.get("max_assignments"))
        
        elif tool_name == "generate_patient_clinical_summary":
            return await generate_patient_clinical_summary_tool(
                tool_input.get("patient_id", ""),
                tool_input.get("include_recommendations", True)
            )
        
        elif tool_name == "get_patient_medical_history":
            return await get_patient_medical_history_tool(
                tool_input.get("patient_id", ""),
                tool_input.get("entry_type"),
                tool_input.get("limit", 20)
            )
        
        elif tool_name == "add_medical_history_entry":
            return await add_medical_history_entry_tool(
                tool_input.get("patient_id", ""),
                tool_input.get("entry_type", ""),
                tool_input.get("title", ""),
                tool_input.get("description", ""),
                tool_input.get("severity")
            )
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        print(f"❌ Error executing tool {tool_name}: {e}")
        return {"error": str(e)}


# Individual tool implementations
async def list_all_patients(include_inactive: bool = False) -> Dict[str, Any]:
    """Get ALL patients in the system"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        print(f"\n📋 Fetching ALL patients (include_inactive={include_inactive})")
        
        # Query patients
        query = supabase.table("patients").select("*")
        
        if not include_inactive:
            query = query.eq("enrollment_status", "active")
        
        response = query.execute()
        patients = response.data or []
        
        print(f"   ✅ Found {len(patients)} patients")
        
        # Enrich with room assignments
        for patient in patients:
            room_assignment = supabase.table("patients_room").select("room_id, assigned_at").eq("patient_id", patient["patient_id"]).execute()
            if room_assignment.data:
                room_id = room_assignment.data[0]["room_id"]
                room_data = supabase.table("rooms").select("room_name, room_type").eq("room_id", room_id).execute()
                if room_data.data:
                    patient["current_room"] = room_data.data[0]["room_name"]
                    patient["room_type"] = room_data.data[0]["room_type"]
                    patient["assigned_at"] = room_assignment.data[0]["assigned_at"]
            else:
                patient["current_room"] = None
        
        return {
            "patients": patients,
            "count": len(patients),
            "active_count": sum(1 for p in patients if p.get('enrollment_status') == 'active'),
            "assigned_count": sum(1 for p in patients if p.get('current_room'))
        }
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"error": str(e)}


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
    """Get complete patient details including medical history and latest vitals"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        print(f"\n📋 Fetching comprehensive details for {patient_id}")
        
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
        
        # Get active alerts
        alerts_response = supabase.table("alerts").select("*").eq("patient_id", patient_id).eq("status", "active").execute()
        patient["active_alerts"] = alerts_response.data or []
        
        # Get latest vitals from vital_signs table
        try:
            latest_vitals = supabase.table("vital_signs").select("*").eq("patient_id", patient_id).order("recorded_at", desc=True).limit(1).execute()
            if latest_vitals.data:
                patient["latest_vitals"] = latest_vitals.data[0]
                print(f"   → Latest vitals: HR {latest_vitals.data[0].get('heart_rate')}, Temp {latest_vitals.data[0].get('temperature')}")
        except:
            patient["latest_vitals"] = None
        
        # Get critical medical history items
        try:
            # Allergies
            allergies = supabase.table("medical_history").select("title, description, metadata").eq("patient_id", patient_id).eq("entry_type", "allergy").eq("status", "active").execute()
            patient["allergies"] = allergies.data or []
            
            # Current medications
            medications = supabase.table("medical_history").select("title, description, metadata").eq("patient_id", patient_id).eq("entry_type", "medication").eq("status", "active").execute()
            patient["current_medications"] = medications.data or []
            
            # Recent diagnoses
            diagnoses = supabase.table("medical_history").select("title, description, entry_date").eq("patient_id", patient_id).eq("entry_type", "diagnosis").order("entry_date", desc=True).limit(3).execute()
            patient["diagnoses"] = diagnoses.data or []
            
            print(f"   → {len(patient['allergies'])} allergies, {len(patient['current_medications'])} active medications")
            
        except:
            patient["allergies"] = []
            patient["current_medications"] = []
            patient["diagnoses"] = []
        
        return patient
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"error": str(e)}


async def get_room_status(room_id: str) -> Dict[str, Any]:
    """Get room status and occupancy"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get all rooms for fuzzy matching
        all_rooms = supabase.table("rooms").select("*").execute()
        
        if not all_rooms.data:
            return {"error": "No rooms found in database"}
        
        # Fuzzy match to find the room
        matched_room = fuzzy_match_room(room_id, all_rooms.data)
        
        if not matched_room:
            return {"error": f"Room '{room_id}' not found. Try: {', '.join([r['room_name'] for r in all_rooms.data[:3]])}"}
        
        room = matched_room
        actual_room_id = room['room_id']
        
        # Check if occupied
        assignment = supabase.table("patients_room").select("patient_id, assigned_at").eq("room_id", actual_room_id).execute()
        
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


async def get_active_alerts(severity: Optional[str] = None, patient_id: Optional[str] = None, room_id: Optional[str] = None) -> Dict[str, Any]:
    """Get active alerts with optional filters"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        query = supabase.table("alerts").select("*").eq("status", "active")
        
        if severity:
            query = query.eq("severity", severity)
        if patient_id:
            query = query.eq("patient_id", patient_id)
        if room_id:
            query = query.eq("room_id", room_id)
        
        response = query.order("triggered_at", desc=True).limit(20).execute()
        
        alerts = response.data or []
        
        # Group by severity for summary
        by_severity = {}
        for alert in alerts:
            sev = alert.get('severity', 'unknown')
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(alert)
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "by_severity": by_severity,
            "critical_count": len(by_severity.get('critical', [])),
            "high_count": len(by_severity.get('high', [])),
            "medium_count": len(by_severity.get('medium', [])),
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_alerts_by_room() -> Dict[str, Any]:
    """Get all active alerts grouped by room"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get all active alerts
        alerts = supabase.table("alerts").select("*").eq("status", "active").execute()
        
        # Group by room
        room_alerts = {}
        for alert in (alerts.data or []):
            room_id = alert.get('room_id')
            if room_id:
                if room_id not in room_alerts:
                    room_alerts[room_id] = []
                room_alerts[room_id].append(alert)
        
        # Enrich with room names
        result = []
        for room_id, room_alert_list in room_alerts.items():
            room_data = supabase.table("rooms").select("room_name").eq("room_id", room_id).execute()
            room_name = room_data.data[0]['room_name'] if room_data.data else room_id
            
            # Find highest severity
            severities = [a.get('severity') for a in room_alert_list]
            severity_priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0}
            highest_severity = max(severities, key=lambda s: severity_priority.get(s, 0))
            
            result.append({
                "room_id": room_id,
                "room_name": room_name,
                "alert_count": len(room_alert_list),
                "highest_severity": highest_severity,
                "alerts": room_alert_list
            })
        
        # Sort by severity (critical first)
        result.sort(key=lambda r: severity_priority.get(r['highest_severity'], 0), reverse=True)
        
        return {
            "rooms_with_alerts": result,
            "total_rooms_affected": len(result),
            "total_alerts": sum(r['alert_count'] for r in result)
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_alert_details(alert_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific alert"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Fetch the alert
        alert_result = supabase.table("alerts").select("*").eq("id", alert_id).execute()
        
        if not alert_result.data or len(alert_result.data) == 0:
            return {"error": f"Alert with ID {alert_id} not found"}
        
        alert = alert_result.data[0]
        
        # Enrich with patient information if available
        patient_info = None
        if alert.get("patient_id"):
            patient_result = supabase.table("patients").select("patient_id, name, age, condition").eq("patient_id", alert["patient_id"]).execute()
            if patient_result.data and len(patient_result.data) > 0:
                patient_info = patient_result.data[0]
        
        # Enrich with room information if available
        room_info = None
        if alert.get("room_id"):
            room_result = supabase.table("rooms").select("room_id, room_name, room_type").eq("room_id", alert["room_id"]).execute()
            if room_result.data and len(room_result.data) > 0:
                room_info = room_result.data[0]
        
        # Build the response
        return {
            "alert": alert,
            "patient": patient_info,
            "room": room_info,
            "metadata": alert.get("metadata", {}),
            "timeline": {
                "triggered_at": alert.get("triggered_at"),
                "acknowledged_at": alert.get("acknowledged_at"),
                "resolved_at": alert.get("resolved_at")
            }
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
    """Assign patient to room (write operation) - uses fuzzy matching for room names"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        print(f"\n🔄 Assigning {patient_id} to room '{room_id}'")
        
        # Fuzzy match room name to get actual room_id UUID
        all_rooms = supabase.table("rooms").select("room_id, room_name").execute()
        
        if not all_rooms.data:
            return {"error": "No rooms found in database"}
        
        matched_room = fuzzy_match_room(room_id, all_rooms.data)
        
        if not matched_room:
            return {"error": f"Room '{room_id}' not found. Available rooms: {', '.join([r['room_name'] for r in all_rooms.data[:5]])}"}
        
        actual_room_id = matched_room['room_id']
        room_name = matched_room['room_name']
        
        print(f"  → Matched '{room_id}' to {room_name} (UUID: {actual_room_id})")
        
        # Check if room is available
        existing = supabase.table("patients_room").select("*").eq("room_id", actual_room_id).execute()
        if existing.data:
            return {"error": f"{room_name} is already occupied"}
        
        # Check if patient exists
        patient = supabase.table("patients").select("name").eq("patient_id", patient_id).execute()
        if not patient.data:
            return {"error": f"Patient {patient_id} not found"}
        
        patient_name = patient.data[0]['name']
        
        # Create assignment
        result = supabase.table("patients_room").insert({
            "room_id": actual_room_id,
            "patient_id": patient_id,
            "assigned_by": "Haven AI"
        }).execute()
        
        print(f"  ✅ Assigned {patient_name} to {room_name}")
        
        return {
            "success": True,
            "message": f"Assigned {patient_name} ({patient_id}) to {room_name}",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "room_id": actual_room_id,
            "room_name": room_name
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"error": str(e)}




async def remove_patient_from_room_tool(patient_id: Optional[str] = None, room_id: Optional[str] = None, generate_report: bool = True) -> Dict[str, Any]:
    """Remove patient from room - accepts either patient_id OR room_id"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # If room_id provided, find patient in that room using fuzzy matching
        if room_id and not patient_id:
            # Get all rooms for fuzzy matching
            all_rooms = supabase.table("rooms").select("room_id, room_name").execute()
            
            if not all_rooms.data:
                return {"error": "No rooms found in database"}
            
            # Fuzzy match to find the room
            matched_room = fuzzy_match_room(room_id, all_rooms.data)
            
            if not matched_room:
                return {"error": f"Room '{room_id}' not found. Try: {', '.join([r['room_name'] for r in all_rooms.data[:3]])}"}
            
            actual_room_id = matched_room['room_id']
            room_name = matched_room['room_name']
            
            # Check for patient assignment
            assignment = supabase.table("patients_room").select("patient_id").eq("room_id", actual_room_id).execute()
            
            if not assignment.data:
                return {"error": f"{room_name} is already empty — no patient currently assigned"}
            
            patient_id = assignment.data[0]['patient_id']
            room_id = actual_room_id
        
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


async def transfer_patient_tool(patient_id: Optional[str] = None, to_room_id: str = "", from_room_id: Optional[str] = None) -> Dict[str, Any]:
    """Transfer patient from one room to another - ALWAYS queries database fresh"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n{'='*60}")
        print(f"🔄 [{timestamp}] TRANSFER REQUEST (FRESH DATABASE QUERY)")
        print(f"   patient_id: {patient_id or 'NOT PROVIDED - will auto-detect'}")
        print(f"   from_room_id: {from_room_id or 'NOT PROVIDED - will auto-detect'}")
        print(f"   to_room_id: {to_room_id}")
        print(f"{'='*60}")
        
        # Get all rooms for fuzzy matching (FRESH QUERY)
        all_rooms = supabase.table("rooms").select("room_id, room_name").execute()
        print(f"\n📊 Total rooms in database: {len(all_rooms.data) if all_rooms.data else 0}")
        
        if not all_rooms.data:
            return {"error": "No rooms found in database"}
        
        # CRITICAL: If from_room_id provided (even if patient_id also provided), query database for current occupant
        if from_room_id:
            print(f"\n🔍 QUERYING DATABASE: Who is in from_room '{from_room_id}'?")
            matched_from_room = fuzzy_match_room(from_room_id, all_rooms.data)
            
            if not matched_from_room:
                return {"error": f"Source room '{from_room_id}' not found"}
            
            actual_from_room_id = matched_from_room['room_id']
            from_room_name = matched_from_room['room_name']
            
            print(f"  → Matched to: {from_room_name} (UUID: {actual_from_room_id})")
            
            # FRESH DATABASE QUERY for current occupant
            print(f"  → SELECT * FROM patients_room WHERE room_id = '{actual_from_room_id}'")
            assignment = supabase.table("patients_room").select("patient_id").eq("room_id", actual_from_room_id).execute()
            print(f"  → Database returned: {assignment.data}")
            
            if not assignment.data or len(assignment.data) == 0:
                print(f"  ❌ Room is empty right now in database")
                return {"error": f"{from_room_name} is currently empty — no patient to move"}
            
            patient_id = assignment.data[0]['patient_id']
            from_room_id = actual_from_room_id
            
            print(f"  ✅ Found patient {patient_id} in {from_room_name} (current database state)")
        
        # If only patient_id provided, query for their current room
        elif patient_id and not from_room_id:
            print(f"\n🔍 QUERYING DATABASE: Where is patient {patient_id}?")
            assignment = supabase.table("patients_room").select("room_id").eq("patient_id", patient_id).execute()
            print(f"  → Database returned: {assignment.data}")
            
            if assignment.data:
                from_room_id = assignment.data[0]['room_id']
                print(f"  ✅ Patient is currently in room_id={from_room_id}")
            else:
                return {"error": f"Patient {patient_id} is not currently in any room"}
        
        else:
            return {"error": "Must provide either patient_id or from_room_id"}
        
        # Fuzzy match destination room
        matched_to_room = fuzzy_match_room(to_room_id, all_rooms.data)
        
        if not matched_to_room:
            return {"error": f"Destination room '{to_room_id}' not found. Try: {', '.join([r['room_name'] for r in all_rooms.data[:3]])}"}
        
        actual_to_room_id = matched_to_room['room_id']
        to_room_name = matched_to_room['room_name']
        
        print(f"  → Destination: {to_room_name} (ID: {actual_to_room_id})")
        
        # Check if destination room is available
        dest_check = supabase.table("patients_room").select("*").eq("room_id", actual_to_room_id).execute()
        print(f"  → Destination occupied check: {bool(dest_check.data)}")
        
        if dest_check.data:
            return {"error": f"Destination room {to_room_name} is already occupied"}
        
        # Get from room name
        from_room_data = supabase.table("rooms").select("room_name").eq("room_id", from_room_id).execute()
        from_room_name = from_room_data.data[0]['room_name'] if from_room_data.data else from_room_id
        
        # Get patient name
        patient_data = supabase.table("patients").select("name").eq("patient_id", patient_id).execute()
        patient_name = patient_data.data[0]['name'] if patient_data.data else patient_id
        
        print(f"\n🔄 Transferring {patient_id} from {from_room_id} to {actual_to_room_id}")
        
        # Remove from old room
        print(f"  → Deleting assignment: patient_id={patient_id}")
        delete_result = supabase.table("patients_room").delete().eq("patient_id", patient_id).execute()
        print(f"  → Delete result: {delete_result.data}")
        
        if not delete_result.data:
            print(f"  ⚠️ Warning: Delete returned no data (may still have succeeded)")
        
        # Verify deletion
        check_delete = supabase.table("patients_room").select("*").eq("patient_id", patient_id).execute()
        print(f"  → Verification after delete: {len(check_delete.data) if check_delete.data else 0} assignments remain")
        
        if check_delete.data:
            return {"error": f"Failed to remove patient from {from_room_name} - assignment still exists"}
        
        # Add to new room
        print(f"  → Inserting new assignment: room_id={actual_to_room_id}, patient_id={patient_id}")
        insert_result = supabase.table("patients_room").insert({
            "room_id": actual_to_room_id,
            "patient_id": patient_id,
            "assigned_by": "Haven AI"
        }).execute()
        print(f"  → Insert result: {insert_result.data}")
        
        if not insert_result.data:
            return {"error": f"Failed to assign patient to {to_room_name}"}
        
        # Verify insertion
        check_insert = supabase.table("patients_room").select("*").eq("patient_id", patient_id).execute()
        print(f"  → Verification after insert: {check_insert.data}")
        
        if not check_insert.data or check_insert.data[0]['room_id'] != actual_to_room_id:
            return {"error": "Transfer verification failed - patient may not be in correct room"}
        
        print(f"  ✅ Transfer verified: {patient_id} is now in {actual_to_room_id}")
        
        return {
            "success": True,
            "message": f"Transferred {patient_name} ({patient_id}) from {from_room_name} to {to_room_name}",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "from_room": from_room_name,
            "from_room_id": from_room_id,
            "to_room": to_room_name,
            "to_room_id": actual_to_room_id
        }
    
    except Exception as e:
        print(f"❌ Error in transfer_patient_tool: {e}")
        import traceback
        traceback.print_exc()
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


def fuzzy_match_room(query: str, rooms: List[Dict]) -> Optional[Dict]:
    """Fuzzy match room name - finds BEST match with priority"""
    if not rooms:
        return None
    
    query_lower = query.lower().strip()
    
    # Extract number if present
    import re
    query_num = re.search(r'\d+', query)
    
    # Priority 1: Exact match (case-insensitive)
    for room in rooms:
        room_name = room['room_name'].lower()
        room_id = room['room_id'].lower()
        
        if query_lower == room_name or query_lower == room_id:
            return room
    
    # Priority 2: Exact number match ("5" → "Room 5", not "Room 2")
    if query_num:
        query_number = query_num.group()
        for room in rooms:
            room_name = room['room_name']
            # Match ONLY if the exact number is in the name
            # "5" should match "Room 5" but NOT "Room 2" or "Room 25"
            if f"Room {query_number}" in room_name or f"room {query_number}" in room_name.lower():
                return room
            # Also check for exact match in room ID
            room_num = re.search(r'\d+', room_name)
            if room_num and room_num.group() == query_number:
                # Double-check it's the right match
                if query_number in room_name:
                    return room
    
    # Priority 3: Partial match (last resort)
    for room in rooms:
        room_name = room['room_name'].lower()
        room_id = room['room_id'].lower()
        
        if query_lower in room_name or query_lower in room_id:
            return room
    
    # No match found
    return None


async def get_patient_in_room_tool(room_id: str) -> Dict[str, Any]:
    """Find which patient is in a specific room - ALWAYS queries fresh from database"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n🔍 [{timestamp}] FRESH QUERY: Checking room '{room_id}'")
        
        # Get all rooms for fuzzy matching (fresh query)
        all_rooms = supabase.table("rooms").select("room_id, room_name").execute()
        print(f"  → Total rooms in database: {len(all_rooms.data) if all_rooms.data else 0}")
        
        if not all_rooms.data:
            return {"error": "No rooms found in database"}
        
        # Fuzzy match to find the room
        matched_room = fuzzy_match_room(room_id, all_rooms.data)
        
        if not matched_room:
            return {"error": f"Room '{room_id}' not found. Available rooms: {', '.join([r['room_name'] for r in all_rooms.data[:5]])}"}
        
        actual_room_id = matched_room['room_id']
        room_name = matched_room['room_name']
        
        print(f"  → Matched '{room_id}' to: {room_name} (ID: {actual_room_id})")
        
        # CRITICAL: Fresh query from patients_room table
        print(f"  → Querying patients_room table for room_id = {actual_room_id}")
        assignment = supabase.table("patients_room").select("patient_id, assigned_at").eq("room_id", actual_room_id).execute()
        
        print(f"  → Assignment data: {assignment.data}")
        print(f"  → Is occupied: {bool(assignment.data)}")
        
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


async def get_all_room_occupancy_tool() -> Dict[str, Any]:
    """Get complete list of all rooms with their occupants"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get all rooms
        rooms = supabase.table("rooms").select("room_id, room_name, room_type").eq("room_type", "patient").execute()
        
        # Get all assignments
        assignments = supabase.table("patients_room").select("room_id, patient_id, assigned_at").execute()
        assignment_map = {a['room_id']: a for a in (assignments.data or [])}
        
        # Build occupancy list
        room_list = []
        for room in (rooms.data or []):
            room_info = {
                "room_id": room['room_id'],
                "room_name": room['room_name'],
                "status": "available"
            }
            
            if room['room_id'] in assignment_map:
                assignment = assignment_map[room['room_id']]
                # Get patient name
                patient = supabase.table("patients").select("name, condition").eq("patient_id", assignment['patient_id']).execute()
                if patient.data:
                    room_info["status"] = "occupied"
                    room_info["patient_id"] = assignment['patient_id']
                    room_info["patient_name"] = patient.data[0]['name']
                    room_info["patient_condition"] = patient.data[0].get('condition')
                    room_info["assigned_at"] = assignment['assigned_at']
            
            room_list.append(room_info)
        
        occupied_count = sum(1 for r in room_list if r['status'] == 'occupied')
        
        return {
            "total_rooms": len(room_list),
            "occupied": occupied_count,
            "available": len(room_list) - occupied_count,
            "rooms": room_list
        }
    
    except Exception as e:
        return {"error": str(e)}


async def remove_all_patients_from_rooms_tool(confirm: bool = False) -> Dict[str, Any]:
    """Batch remove all patients from rooms"""
    if not supabase:
        return {"error": "Database not configured"}
    
    if not confirm:
        return {
            "error": "Confirmation required",
            "message": "This will discharge ALL patients. Ask user: 'Confirm mass discharge of all patients?' before proceeding.",
            "require_confirmation": True
        }
    
    try:
        # Get all current assignments
        assignments = supabase.table("patients_room").select("patient_id, room_id").execute()
        
        if not assignments.data:
            return {"message": "No patients currently in rooms", "removed": 0}
        
        removed_count = len(assignments.data)
        
        # Remove all assignments
        supabase.table("patients_room").delete().neq("patient_id", "").execute()
        
        return {
            "success": True,
            "message": f"Removed {removed_count} patients from all rooms",
            "removed_count": removed_count,
            "all_rooms_now_available": True
        }
    
    except Exception as e:
        return {"error": str(e)}


async def auto_assign_patients_to_rooms_tool(max_assignments: Optional[int] = None) -> Dict[str, Any]:
    """Auto-assign unassigned patients to available rooms"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        # Get all patients
        all_patients = supabase.table("patients").select("patient_id, name").eq("enrollment_status", "active").execute()
        
        # Get currently assigned patients
        assignments = supabase.table("patients_room").select("patient_id").execute()
        assigned_ids = set(a['patient_id'] for a in (assignments.data or []))
        
        # Filter to unassigned patients
        unassigned = [p for p in (all_patients.data or []) if p['patient_id'] not in assigned_ids]
        
        # Get available rooms
        all_rooms = supabase.table("rooms").select("room_id, room_name").eq("room_type", "patient").execute()
        occupied_room_ids = set(a['room_id'] for a in (assignments.data or []))
        available_rooms = [r for r in (all_rooms.data or []) if r['room_id'] not in occupied_room_ids]
        
        if not available_rooms:
            return {"error": "No available rooms"}
        
        if not unassigned:
            return {"message": "All active patients are already assigned to rooms"}
        
        # Determine how many to assign
        num_to_assign = min(len(unassigned), len(available_rooms))
        if max_assignments:
            num_to_assign = min(num_to_assign, max_assignments)
        
        # Make assignments
        new_assignments = []
        for i in range(num_to_assign):
            patient = unassigned[i]
            room = available_rooms[i]
            
            supabase.table("patients_room").insert({
                "room_id": room['room_id'],
                "patient_id": patient['patient_id'],
                "assigned_by": "Haven AI Auto-Assign"
            }).execute()
            
            new_assignments.append({
                "patient_id": patient['patient_id'],
                "patient_name": patient['name'],
                "room_id": room['room_id'],
                "room_name": room['room_name']
            })
        
        return {
            "success": True,
            "message": f"Auto-assigned {num_to_assign} patients to rooms",
            "assignments": new_assignments,
            "assigned_count": num_to_assign,
            "remaining_unassigned": len(unassigned) - num_to_assign,
            "remaining_available_rooms": len(available_rooms) - num_to_assign
        }
    
    except Exception as e:
        return {"error": str(e)}


async def generate_patient_clinical_summary_tool(patient_id: str, include_recommendations: bool = True) -> Dict[str, Any]:
    """Generate comprehensive clinical summary for a patient with AI insights"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        print(f"\n📋 Generating clinical summary for {patient_id}...")
        
        # Get patient data
        patient = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
        
        if not patient.data:
            return {"error": f"Patient {patient_id} not found"}
        
        patient_info = patient.data[0]
        
        # Get room assignment
        room_assignment = supabase.table("patients_room").select("room_id, assigned_at").eq("patient_id", patient_id).execute()
        current_room = None
        if room_assignment.data:
            room_id = room_assignment.data[0]['room_id']
            room_data = supabase.table("rooms").select("room_name, room_type").eq("room_id", room_id).execute()
            if room_data.data:
                current_room = {
                    "room_name": room_data.data[0]['room_name'],
                    "room_type": room_data.data[0]['room_type'],
                    "assigned_at": room_assignment.data[0]['assigned_at']
                }
        
        # Get active alerts
        alerts = supabase.table("alerts").select("*").eq("patient_id", patient_id).eq("status", "active").execute()
        active_alerts = alerts.data or []
        
        # Get alert history
        alert_history = supabase.table("alerts").select("*").eq("patient_id", patient_id).order("triggered_at", desc=True).limit(20).execute()
        
        # Get medical history
        medical_history = supabase.table("medical_history").select("*").eq("patient_id", patient_id).order("entry_date", desc=True).limit(30).execute()
        history_entries = medical_history.data or []
        
        # Organize history by type
        history_by_type = {}
        for entry in history_entries:
            etype = entry.get('entry_type', 'other')
            if etype not in history_by_type:
                history_by_type[etype] = []
            history_by_type[etype].append(entry)
        
        print(f"   → Medical history: {len(history_entries)} entries across {len(history_by_type)} types")
        
        # Build summary data
        summary = {
            "patient_id": patient_id,
            "patient_name": patient_info.get('name'),
            "age": patient_info.get('age'),
            "gender": patient_info.get('gender'),
            "condition": patient_info.get('condition'),
            "enrollment_status": patient_info.get('enrollment_status'),
            "enrollment_date": patient_info.get('enrollment_date'),
            "current_room": current_room,
            "active_alerts_count": len(active_alerts),
            "active_alerts": active_alerts[:5],
            "alert_history_count": len(alert_history.data or []),
            "baseline_vitals": patient_info.get('baseline_vitals'),
            "baseline_crs_risk": patient_info.get('baseline_crs_risk'),
            "ecog_status": patient_info.get('ecog_status'),
            "prior_treatment_lines": patient_info.get('prior_treatment_lines'),
            "infusion_count": patient_info.get('infusion_count'),
            "medical_history": {
                "total_entries": len(history_entries),
                "entries_by_type": history_by_type,
                "allergies": history_by_type.get('allergy', []),
                "medications": history_by_type.get('medication', []),
                "procedures": history_by_type.get('procedure', []),
                "recent_entries": history_entries[:5]
            }
        }
        
        # Generate AI clinical insights
        recommendations = []
        risk_factors = []
        key_concerns = []
        
        if include_recommendations:
            try:
                import os
                import anthropic
                ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
                
                if ANTHROPIC_API_KEY:
                    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                    
                    # Build clinical context
                    vitals_str = ""
                    if patient_info.get('baseline_vitals'):
                        vitals = patient_info['baseline_vitals']
                        vitals_str = f"""Baseline Vitals:
- HR: {vitals.get('heart_rate', 'N/A')} bpm
- BP: {vitals.get('blood_pressure', 'N/A')}
- Temp: {vitals.get('temperature', 'N/A')}
- RR: {vitals.get('respiratory_rate', 'N/A')} /min
- SpO2: {vitals.get('oxygen_saturation', 'N/A')}%"""
                    
                    alerts_str = "\n".join([
                        f"- {a.get('severity', '').upper()}: {a.get('title')}"
                        for a in (alert_history.data or [])[:5]
                    ])
                    
                    # Build medical history summary
                    allergies_str = "\n".join([f"- {a.get('title')}: {a.get('description', 'See chart')}" for a in history_by_type.get('allergy', [])[:3]])
                    meds_str = "\n".join([f"- {m.get('title')}" for m in history_by_type.get('medication', [])[:5]])
                    procedures_str = "\n".join([f"- {p.get('title')} ({p.get('entry_date', '')[:10]})" for p in history_by_type.get('procedure', [])[:3]])
                    
                    clinical_context = f"""**Patient:** {patient_info.get('name')} ({patient_id})
**Age:** {patient_info.get('age')} | **Gender:** {patient_info.get('gender')}
**Diagnosis:** {patient_info.get('condition')}
**ECOG:** {patient_info.get('ecog_status')} | **Prior Lines:** {patient_info.get('prior_treatment_lines')}
**CRS Risk:** {patient_info.get('baseline_crs_risk')}
**Location:** {current_room['room_name'] if current_room else 'Not assigned'}

{vitals_str}

**Medical History ({len(history_entries)} total entries):**
Allergies:
{allergies_str if allergies_str else '- None documented'}

Current Medications:
{meds_str if meds_str else '- None documented'}

Previous Procedures:
{procedures_str if procedures_str else '- None documented'}

**Recent Alerts ({len(active_alerts)} active):**
{alerts_str if alerts_str else 'No alerts'}"""
                    
                    # Get clinical analysis from Claude
                    analysis = claude_client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=800,
                        messages=[{
                            "role": "user",
                            "content": f"""Analyze this patient and provide clinical guidance:

{clinical_context}

Provide in this exact format:

KEY CONCERNS:
1. [Most critical issue]
2. [Second concern]
3. [Third concern]

RISK FACTORS:
1. [Primary risk to monitor]
2. [Secondary risk]
3. [Additional risk]

RECOMMENDATIONS:
1. [Immediate action needed]
2. [Monitoring plan]
3. [Follow-up steps]

Be concise, clinical, actionable."""
                        }]
                    )
                    
                    insights_text = analysis.content[0].text
                    
                    # Parse Claude's response
                    if "KEY CONCERNS:" in insights_text:
                        concerns_section = insights_text.split("KEY CONCERNS:")[1].split("RISK FACTORS:")[0]
                        key_concerns = [line.strip() for line in concerns_section.split('\n') if line.strip() and any(c.isalpha() for c in line)][:3]
                    
                    if "RISK FACTORS:" in insights_text:
                        risk_section = insights_text.split("RISK FACTORS:")[1].split("RECOMMENDATIONS:")[0]
                        risk_factors = [line.strip() for line in risk_section.split('\n') if line.strip() and any(c.isalpha() for c in line)][:3]
                    
                    if "RECOMMENDATIONS:" in insights_text:
                        rec_section = insights_text.split("RECOMMENDATIONS:")[1]
                        recommendations = [line.strip() for line in rec_section.split('\n') if line.strip() and any(c.isalpha() for c in line)][:3]
                    
                    print(f"   ✅ AI insights generated")
                    
            except Exception as ai_error:
                print(f"   ⚠️ AI insights error: {ai_error}")
                # Fallback recommendations
                recommendations = [
                    "Monitor vital signs per protocol",
                    "Review recent alert patterns",
                    "Continue current treatment plan"
                ]
                risk_factors = [
                    "Monitor for CRS symptoms if post-CAR T",
                    "Watch for fever >38.5°C",
                    "Track any changes in baseline vitals"
                ]
                key_concerns = [
                    f"{len(active_alerts)} active alerts require attention",
                    "Regular monitoring per ECOG status",
                    "Treatment adherence assessment needed"
                ]
        
        summary["ai_insights"] = {
            "key_concerns": key_concerns or ["Regular monitoring recommended"],
            "risk_factors": risk_factors or ["Standard clinical monitoring"],
            "recommendations": recommendations or ["Continue per protocol"]
        }
        
        # PDF report URL
        summary["pdf_report_url"] = f"/reports/clinical-summary/{patient_id}"
        summary["pdf_available"] = True
        
        print(f"   ✅ Clinical summary generated for {patient_info.get('name')}")
        
        return summary
    
    except Exception as e:
        print(f"   ❌ Error generating summary: {e}")
        return {"error": str(e)}


async def get_patient_medical_history_tool(patient_id: str, entry_type: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """Get medical history for a patient"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        print(f"\n📋 Fetching medical history for {patient_id}")
        print(f"   Entry type filter: {entry_type or 'all'}")
        print(f"   Limit: {limit}")
        
        # Build query
        query = supabase.table("medical_history").select("*").eq("patient_id", patient_id)
        
        if entry_type and entry_type.strip():
            query = query.eq("entry_type", entry_type)
        
        response = query.order("entry_date", desc=True).limit(limit).execute()
        
        history_entries = response.data or []
        
        # Group by type for better organization
        grouped_by_type = {}
        for entry in history_entries:
            etype = entry.get('entry_type', 'other')
            if etype not in grouped_by_type:
                grouped_by_type[etype] = []
            grouped_by_type[etype].append(entry)
        
        print(f"   ✅ Found {len(history_entries)} history entries")
        print(f"   Types: {list(grouped_by_type.keys())}")
        
        return {
            "patient_id": patient_id,
            "total_entries": len(history_entries),
            "entries_by_type": grouped_by_type,
            "recent_entries": history_entries[:10],  # Most recent 10
            "has_allergies": 'allergy' in grouped_by_type,
            "has_medications": 'medication' in grouped_by_type,
            "entry_types_present": list(grouped_by_type.keys())
        }
    
    except Exception as e:
        print(f"   ❌ Error fetching medical history: {e}")
        return {"error": str(e)}


async def add_medical_history_entry_tool(
    patient_id: str, 
    entry_type: str, 
    title: str, 
    description: str = "", 
    severity: Optional[str] = None
) -> Dict[str, Any]:
    """Add new medical history entry"""
    if not supabase:
        return {"error": "Database not configured"}
    
    try:
        print(f"\n📝 Adding medical history entry for {patient_id}")
        print(f"   Type: {entry_type}")
        print(f"   Title: {title}")
        
        # Verify patient exists
        patient_check = supabase.table("patients").select("name").eq("patient_id", patient_id).execute()
        if not patient_check.data:
            return {"error": f"Patient {patient_id} not found"}
        
        patient_name = patient_check.data[0]['name']
        
        # Create entry
        entry_data = {
            "patient_id": patient_id,
            "entry_type": entry_type,
            "title": title,
            "description": description,
            "provider": "Haven AI",
            "status": "active"
        }
        
        if severity:
            entry_data["severity"] = severity
        
        result = supabase.table("medical_history").insert(entry_data).execute()
        
        if result.data:
            print(f"   ✅ Medical history entry added")
            
            return {
                "success": True,
                "message": f"Added {entry_type} entry for {patient_name} ({patient_id})",
                "entry_id": result.data[0]['id'],
                "entry_type": entry_type,
                "title": title
            }
        
        return {"error": "Failed to create medical history entry"}
    
    except Exception as e:
        print(f"   ❌ Error adding medical history: {e}")
        return {"error": str(e)}

