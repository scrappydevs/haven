"""
Room Management for Hospital Floor Plan
Handles room definitions and patient-room assignments
Uses Supabase with normalized tables: rooms + patients_room
"""

from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
from app.supabase_client import supabase

class Floor(BaseModel):
    floor_id: str
    name: str
    smplr_space_id: str
    level_index: int = 0
    building: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict = {}

class Room(BaseModel):
    room_id: str
    room_name: str
    room_type: str  # 'patient' | 'nurse_station' | 'other'
    floor_id: str
    capacity: int = 1
    metadata: Dict = {}

class PatientRoomAssignment(BaseModel):
    room_id: str
    patient_id: str
    assigned_at: Optional[datetime] = None
    assigned_by: Optional[str] = None
    notes: Optional[str] = None

class RoomWithPatient(BaseModel):
    """Room with optional patient assignment info"""
    room_id: str
    room_name: str
    room_type: str
    floor_id: str
    capacity: int = 1
    metadata: Dict = {}
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    assigned_at: Optional[datetime] = None

class AssignPatientRequest(BaseModel):
    room_id: str
    patient_id: str
    notes: Optional[str] = None

class UnassignPatientRequest(BaseModel):
    room_id: str
    patient_id: str

# In-memory fallback - EMPTY by default
_fallback_rooms: Dict[str, Room] = {}

def get_all_floors() -> List[Floor]:
    """Get all floor definitions from database"""
    if supabase:
        try:
            response = supabase.table("floors").select("*").execute()
            floors = [Floor(**floor) for floor in response.data]
            print(f"✅ Fetched {len(floors)} floors from Supabase")
            return floors
        except Exception as e:
            print(f"⚠️ Supabase error: {e}")
            return []
    return []

def get_all_rooms_with_patients(floor_id: str = None) -> List[RoomWithPatient]:
    """
    Get all rooms with their current patient assignments
    Optionally filter by floor_id
    
    DATABASE REFERENCE: 
    - public.rooms - room definitions
    - public.patients_room - patient assignments
    - public.patients - patient details
    
    Args:
        floor_id: Optional floor ID to filter rooms
    
    Returns list of rooms with optional patient info
    """
    if supabase:
        try:
            # Get rooms (optionally filtered by floor)
            query = supabase.table("rooms").select("*")
            if floor_id:
                query = query.eq("floor_id", floor_id)
            rooms_response = query.execute()
            
            # Get all current assignments with patient info
            assignments_response = supabase.table("patients_room") \
                .select("room_id, patient_id, assigned_at, patients(name)") \
                .execute()
            
            # Create a map of room_id -> patient assignment
            assignment_map = {}
            for assignment in assignments_response.data:
                assignment_map[assignment['room_id']] = {
                    'patient_id': assignment['patient_id'],
                    'patient_name': assignment['patients']['name'] if assignment.get('patients') else None,
                    'assigned_at': assignment.get('assigned_at')
                }
            
            # Combine rooms with their assignments
            rooms_with_patients = []
            for room in rooms_response.data:
                room_data = {
                    'room_id': room['room_id'],
                    'room_name': room['room_name'],
                    'room_type': room['room_type'],
                    'floor_id': room.get('floor_id', 'floor-1'),
                    'capacity': room.get('capacity', 1),
                    'metadata': room.get('metadata', {}),  # ✅ Include metadata
                }
                
                # Add patient info if assigned
                if room['room_id'] in assignment_map:
                    assignment = assignment_map[room['room_id']]
                    room_data.update({
                        'patient_id': assignment['patient_id'],
                        'patient_name': assignment['patient_name'],
                        'assigned_at': assignment['assigned_at']
                    })
                
                rooms_with_patients.append(RoomWithPatient(**room_data))
            
            print(f"✅ Fetched {len(rooms_with_patients)} rooms from Supabase")
            return rooms_with_patients
            
        except Exception as e:
            print(f"⚠️ Supabase error: {e}")
            print(f"⚠️ Make sure rooms and patients_room tables exist in Supabase")
    else:
        print("⚠️ Supabase not configured - no room data available")
    
    return []

def assign_patient_to_room(room_id: str, patient_id: str, notes: Optional[str] = None, assigned_by: Optional[str] = None) -> PatientRoomAssignment:
    """
    Assign a patient to a room
    
    DATABASE REFERENCE: public.patients_room
    - Inserts new patient-room assignment
    - Enforces UNIQUE constraint on (room_id, patient_id)
    - Returns the assignment record
    """
    if supabase:
        try:
            # First check if room exists
            room_check = supabase.table("rooms").select("room_id").eq("room_id", room_id).execute()
            if not room_check.data:
                raise ValueError(f"Room {room_id} does not exist")
            
            # Check if patient is already assigned to this room
            existing = supabase.table("patients_room") \
                .select("*") \
                .eq("room_id", room_id) \
                .eq("patient_id", patient_id) \
                .execute()
            
            if existing.data:
                print(f"⚠️ Patient {patient_id} already assigned to {room_id}")
                return PatientRoomAssignment(**existing.data[0])
            
            # Check if patient is assigned to another room (optional, depending on business logic)
            patient_rooms = supabase.table("patients_room") \
                .select("room_id") \
                .eq("patient_id", patient_id) \
                .execute()
            
            if patient_rooms.data:
                # Patient already in another room - unassign first
                old_room = patient_rooms.data[0]['room_id']
                print(f"⚠️ Patient {patient_id} was in {old_room}, removing...")
                supabase.table("patients_room") \
                    .delete() \
                    .eq("patient_id", patient_id) \
                    .execute()
            
            # Insert new assignment
            response = supabase.table("patients_room") \
                .insert({
                    "room_id": room_id,
                    "patient_id": patient_id,
                    "notes": notes,
                    "assigned_by": assigned_by
                }) \
                .execute()
            
            print(f"✅ Assigned {patient_id} to {room_id}")
            return PatientRoomAssignment(**response.data[0])
            
        except Exception as e:
            print(f"⚠️ Supabase error: {e}")
            raise ValueError(f"Failed to assign patient: {e}")
    
    raise ValueError("Supabase not configured")

def unassign_patient_from_room(room_id: str, patient_id: Optional[str] = None) -> Dict:
    """
    Remove patient from a room
    
    DATABASE REFERENCE: public.patients_room
    - Deletes assignment record
    - WHERE room_id = :room_id (and optionally patient_id)
    - Returns success message
    """
    if supabase:
        try:
            query = supabase.table("patients_room").delete().eq("room_id", room_id)
            
            # If specific patient_id provided, only remove that patient
            if patient_id:
                query = query.eq("patient_id", patient_id)
            
            response = query.execute()
            
            print(f"✅ Removed patient(s) from {room_id}")
            return {"success": True, "message": f"Patient removed from {room_id}"}
            
        except Exception as e:
            print(f"⚠️ Supabase error: {e}")
            raise ValueError(f"Failed to unassign patient: {e}")
    
    raise ValueError("Supabase not configured")

def sync_room_from_smplrspace(room_data: Dict, floor_id: str = 'floor-1') -> Room:
    """
    Sync a room from Smplrspace automatic room detection
    Creates or updates room based on room polygon from walls
    
    Args:
        room_data: Room object from smplrClient.getRoomsOnLevel()
          {
            id: 'room-1',
            name: 'Room 1',
            levelIndex: 0,
            position: { x: 10.5, z: 20.3 },
            polygon: [{ levelIndex: 0, x: ..., z: ... }, ...],
            holes: []
          }
        floor_id: Floor identifier (defaults to 'floor-1')
    
    Returns:
        Room object
    """
    if not supabase:
        raise ValueError("Supabase not configured")
    
    try:
        room_id = room_data.get('id')
        room_name = room_data.get('name', room_id)
        
        # Use room_type from frontend if provided, otherwise determine from name
        room_type = room_data.get('room_type', 'patient')  # default to patient
        if not room_data.get('room_type'):
            # Fallback: determine room type from name if not provided
            name_lower = room_name.lower()
            if 'nurse' in name_lower or 'station' in name_lower:
                room_type = 'nurse_station'
            elif 'icu' in name_lower:
                room_type = 'icu'
            elif 'surgery' in name_lower or 'operating' in name_lower:
                room_type = 'surgery'
            elif 'lab' in name_lower:
                room_type = 'lab'
        
        # Store full room data including polygon boundaries
        metadata = {
            'smplrspace_data': room_data,
            'polygon': room_data.get('polygon', []),
            'holes': room_data.get('holes', []),
            'synced_at': datetime.now().isoformat()
        }
        
        # Upsert (insert or update) room
        response = supabase.table("rooms") \
            .upsert({
                'room_id': room_id,
                'room_name': room_name,
                'room_type': room_type,
                'floor_id': floor_id,
                'capacity': 1,
                'metadata': metadata
            }, on_conflict='room_id') \
            .execute()
        
        print(f"✅ Synced room {room_id} to floor {floor_id}")
        return Room(**response.data[0])
        
    except Exception as e:
        print(f"⚠️ Error syncing room: {e}")
        raise ValueError(f"Failed to sync room: {e}")


def get_patient_current_room(patient_id: str) -> Optional[RoomWithPatient]:
    """
    Get the current room assignment for a patient
    
    Returns None if patient is not assigned to any room
    """
    if supabase:
        try:
            response = supabase.table("patients_room") \
                .select("room_id, rooms(room_name, room_type, floor), assigned_at") \
                .eq("patient_id", patient_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                assignment = response.data[0]
                room_info = assignment.get('rooms', {})
                return RoomWithPatient(
                    room_id=assignment['room_id'],
                    room_name=room_info.get('room_name', ''),
                    room_type=room_info.get('room_type', 'patient'),
                    floor=room_info.get('floor', 1),
                    patient_id=patient_id,
                    assigned_at=assignment.get('assigned_at')
                )
        except Exception as e:
            print(f"⚠️ Error getting patient room: {e}")
    
    return None

