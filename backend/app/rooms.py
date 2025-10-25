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

# In-memory fallback if Supabase not available
_fallback_assignments: Dict[str, RoomAssignment] = {
    'room-101': RoomAssignment(room_id='room-101', room_name='Room 101', room_type='patient'),
    'room-102': RoomAssignment(room_id='room-102', room_name='Room 102', room_type='patient'),
    'room-103': RoomAssignment(room_id='room-103', room_name='Room 103', room_type='patient'),
    'room-104': RoomAssignment(room_id='room-104', room_name='Room 104', room_type='patient'),
    'room-105': RoomAssignment(room_id='room-105', room_name='Room 105', room_type='patient'),
    'room-106': RoomAssignment(room_id='room-106', room_name='Room 106', room_type='patient'),
    'nurse-station-1': RoomAssignment(room_id='nurse-station-1', room_name='Nurse Station A', room_type='nurse_station'),
}

def get_all_assignments() -> List[RoomAssignment]:
    """Get all room assignments"""
    if supabase:
        try:
            response = supabase.table("room_assignments").select("*").execute()
            return [RoomAssignment(**row) for row in response.data]
        except Exception as e:
            print(f"⚠️ Supabase error, using in-memory fallback: {e}")
    
    return list(_fallback_assignments.values())

def assign_patient_to_room(room_id: str, patient_id: str, patient_name: str) -> RoomAssignment:
    """Assign a patient to a room"""
    if supabase:
        try:
            response = supabase.table("room_assignments") \
                .update({"patient_id": patient_id, "patient_name": patient_name}) \
                .eq("room_id", room_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                return RoomAssignment(**response.data[0])
        except Exception as e:
            print(f"⚠️ Supabase error, using in-memory fallback: {e}")
    
    # Fallback
    if room_id not in _fallback_assignments:
        raise ValueError(f"Room {room_id} not found")
    
    _fallback_assignments[room_id].patient_id = patient_id
    _fallback_assignments[room_id].patient_name = patient_name
    return _fallback_assignments[room_id]

def unassign_patient_from_room(room_id: str) -> RoomAssignment:
    """Remove patient from a room"""
    if supabase:
        try:
            response = supabase.table("room_assignments") \
                .update({"patient_id": None, "patient_name": None}) \
                .eq("room_id", room_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                return RoomAssignment(**response.data[0])
        except Exception as e:
            print(f"⚠️ Supabase error, using in-memory fallback: {e}")
    
    # Fallback
    if room_id not in _fallback_assignments:
        raise ValueError(f"Room {room_id} not found")
    
    _fallback_assignments[room_id].patient_id = None
    _fallback_assignments[room_id].patient_name = None
    return _fallback_assignments[room_id]

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

