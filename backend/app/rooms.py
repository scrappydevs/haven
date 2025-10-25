"""
Room Management for Hospital Floor Plan
Handles room assignments for patients and nurses
Uses Supabase for persistence with in-memory fallback
"""

from typing import List, Optional, Dict
from pydantic import BaseModel
from app.supabase_client import supabase

class RoomAssignment(BaseModel):
    room_id: str
    room_name: str
    room_type: str  # 'patient' | 'nurse_station' | 'other'
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    nurse_ids: List[str] = []

class AssignPatientRequest(BaseModel):
    room_id: str
    patient_id: str

class AssignNurseRequest(BaseModel):
    room_id: str
    nurse_id: str

# In-memory fallback - EMPTY by default, rooms should come from Supabase
_fallback_assignments: Dict[str, RoomAssignment] = {}

def get_all_assignments() -> List[RoomAssignment]:
    """
    Get all room assignments from Supabase
    
    DATABASE REFERENCE: public.room_assignments
    - Fetches all rows from room_assignments table
    - Returns list of RoomAssignment objects
    - Falls back to empty list if Supabase unavailable
    """
    if supabase:
        try:
            response = supabase.table("room_assignments").select("*").execute()
            print(f"✅ Fetched {len(response.data)} room assignments from Supabase")
            return [RoomAssignment(**row) for row in response.data]
        except Exception as e:
            print(f"⚠️ Supabase error: {e}")
            print(f"⚠️ Make sure room_assignments table exists in Supabase")
    else:
        print("⚠️ Supabase not configured - no room data available")
    
    return list(_fallback_assignments.values())

def assign_patient_to_room(room_id: str, patient_id: str, patient_name: str) -> RoomAssignment:
    """
    Assign a patient to a room
    
    DATABASE REFERENCE: public.room_assignments
    - Updates patient_id and patient_name columns
    - WHERE room_id = :room_id
    - Returns updated RoomAssignment
    """
    if supabase:
        try:
            response = supabase.table("room_assignments") \
                .update({"patient_id": patient_id, "patient_name": patient_name}) \
                .eq("room_id", room_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                print(f"✅ Assigned {patient_id} to {room_id}")
                return RoomAssignment(**response.data[0])
            else:
                # Room doesn't exist, create it
                response = supabase.table("room_assignments") \
                    .insert({
                        "room_id": room_id,
                        "room_name": room_id.replace('-', ' ').title(),
                        "room_type": "patient",
                        "patient_id": patient_id,
                        "patient_name": patient_name
                    }) \
                    .execute()
                print(f"✅ Created room {room_id} and assigned {patient_id}")
                return RoomAssignment(**response.data[0])
        except Exception as e:
            print(f"⚠️ Supabase error: {e}")
            raise ValueError(f"Failed to assign patient: {e}")
    
    raise ValueError("Supabase not configured")

def unassign_patient_from_room(room_id: str) -> RoomAssignment:
    """
    Remove patient from a room
    
    DATABASE REFERENCE: public.room_assignments
    - Sets patient_id and patient_name to NULL
    - WHERE room_id = :room_id
    - Returns updated RoomAssignment
    """
    if supabase:
        try:
            response = supabase.table("room_assignments") \
                .update({"patient_id": None, "patient_name": None}) \
                .eq("room_id", room_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                print(f"✅ Removed patient from {room_id}")
                return RoomAssignment(**response.data[0])
        except Exception as e:
            print(f"⚠️ Supabase error: {e}")
            raise ValueError(f"Failed to unassign patient: {e}")
    
    raise ValueError("Supabase not configured")

def assign_nurse_to_station(room_id: str, nurse_id: str) -> RoomAssignment:
    """Assign a nurse to a station"""
    if supabase:
        try:
            # Get current nurse_ids
            current = supabase.table("room_assignments") \
                .select("nurse_ids") \
                .eq("room_id", room_id) \
                .single() \
                .execute()
            
            nurse_ids = current.data.get("nurse_ids", []) if current.data else []
            if nurse_id not in nurse_ids:
                nurse_ids.append(nurse_id)
            
            response = supabase.table("room_assignments") \
                .update({"nurse_ids": nurse_ids}) \
                .eq("room_id", room_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                return RoomAssignment(**response.data[0])
        except Exception as e:
            print(f"⚠️ Supabase error, using in-memory fallback: {e}")
    
    # Fallback
    if room_id not in _fallback_assignments:
        raise ValueError(f"Room {room_id} not found")
    
    if nurse_id not in _fallback_assignments[room_id].nurse_ids:
        _fallback_assignments[room_id].nurse_ids.append(nurse_id)
    
    return _fallback_assignments[room_id]

def unassign_nurse_from_station(room_id: str, nurse_id: str) -> RoomAssignment:
    """Remove nurse from a station"""
    if supabase:
        try:
            # Get current nurse_ids
            current = supabase.table("room_assignments") \
                .select("nurse_ids") \
                .eq("room_id", room_id) \
                .single() \
                .execute()
            
            nurse_ids = current.data.get("nurse_ids", []) if current.data else []
            if nurse_id in nurse_ids:
                nurse_ids.remove(nurse_id)
            
            response = supabase.table("room_assignments") \
                .update({"nurse_ids": nurse_ids}) \
                .eq("room_id", room_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                return RoomAssignment(**response.data[0])
        except Exception as e:
            print(f"⚠️ Supabase error, using in-memory fallback: {e}")
    
    # Fallback
    if room_id not in _fallback_assignments:
        raise ValueError(f"Room {room_id} not found")
    
    if nurse_id in _fallback_assignments[room_id].nurse_ids:
        _fallback_assignments[room_id].nurse_ids.remove(nurse_id)
    
    return _fallback_assignments[room_id]

