"""
Chat context management for Haven AI
Handles session persistence and context-aware conversations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .supabase_client import supabase


class ChatContext:
    """
    Manages conversation context including:
    - Full message history
    - User/session state
    - Tagged items (patients, rooms, alerts)
    """
    
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.kv_store: Dict[str, Any] = {}
        self.state: Dict[str, Any] = {}
    
    def serialize(self) -> Dict:
        """Convert context to dict for JSON storage"""
        return {
            "messages": self.messages,
            "kv_store": self.kv_store,
            "state": self.state
        }
    
    @classmethod
    def deserialize(cls, data: Dict) -> 'ChatContext':
        """Restore context from stored dict"""
        context = cls()
        context.messages = data.get("messages", [])
        context.kv_store = data.get("kv_store", {})
        context.state = data.get("state", {})
        return context


async def create_session(user_id: str, title: str) -> Dict[str, str]:
    """
    Create a new chat session
    
    Returns:
        Dict with id and title
    """
    if not supabase:
        raise ValueError("Supabase not configured")
    
    context = ChatContext()
    
    result = supabase.table("chat_sessions").insert({
        "user_id": user_id,
        "title": title[:100],  # Truncate long titles
        "context": context.serialize()
    }).execute()
    
    if result.data:
        return {
            "id": result.data[0]["id"],
            "title": result.data[0]["title"]
        }
    
    raise Exception("Failed to create chat session")


async def read_context(session_id: str) -> ChatContext:
    """
    Load context from database
    """
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("chat_sessions").select("context").eq("id", session_id).single().execute()
    
    if result.data and result.data.get("context"):
        return ChatContext.deserialize(result.data["context"])
    
    raise Exception(f"Could not find context for session {session_id}")


async def write_context(session_id: str, context: ChatContext):
    """
    Save context to database
    """
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("chat_sessions").update({
        "context": context.serialize(),
        "updated_at": datetime.now().isoformat()
    }).eq("id", session_id).execute()
    
    if not result.data:
        raise Exception(f"Failed to update session {session_id}")


async def get_user_sessions(user_id: str) -> List[Dict]:
    """
    Get all chat sessions for a user
    """
    if not supabase:
        return []
    
    result = supabase.table("chat_sessions").select("id, title, created_at, updated_at").eq("user_id", user_id).order("updated_at", desc=True).execute()
    
    return result.data or []


async def get_page_context_data(state: Dict[str, Any]) -> str:
    """
    Fetch actual data based on current page context
    """
    if not supabase:
        return ""
    
    context_data = []
    page = state.get("current_page", "")
    
    try:
        if "floorplan" in page:
            # Fetch room occupancy data
            rooms_response = supabase.table("rooms").select("room_name, room_type").execute()
            assignments_response = supabase.table("patients_room").select("room_id, patient_id").execute()
            
            occupied_count = len(assignments_response.data) if assignments_response.data else 0
            total_rooms = len([r for r in (rooms_response.data or []) if r['room_type'] == 'patient'])
            
            context_data.append(f"**Floor Plan Data:**\n- {occupied_count}/{total_rooms} rooms occupied\n- {total_rooms - occupied_count} rooms available")
        
        elif "dashboard" in page:
            # Fetch recent alerts (if table exists)
            try:
                alerts_response = supabase.table("alerts").select("*").order("triggered_at", desc=True).limit(5).execute()
                if alerts_response.data:
                    alert_count = len(alerts_response.data)
                    active_alerts = [a for a in alerts_response.data if a.get('status') == 'active']
                    context_data.append(f"**Dashboard Data:**\n- {len(active_alerts)} active alerts ({alert_count} total recent)")
            except Exception as alert_err:
                # Alerts table might not exist yet
                print(f"⚠️ Alerts table not available: {alert_err}")
                context_data.append(f"**Dashboard Data:**\n- Monitoring active")
    
    except Exception as e:
        print(f"⚠️ Error fetching context data: {e}")
    
    return "\n".join(context_data) if context_data else ""


async def build_system_prompt(context: ChatContext) -> str:
    """
    Build a context-aware system prompt based on current state
    """
    base_prompt = """You are Haven AI, a clinical decision support assistant for hospital staff in a professional medical environment.

**CRITICAL: Content Moderation**
If the user sends inappropriate, offensive, or non-clinical content:
1. Do NOT engage with the content
2. Respond with a brief, professional redirect
3. Offer specific clinical help options
4. Keep response under 3 lines

Example response to inappropriate input:
"I'm here to support clinical operations. How can I help?

• Patient information
• Room assignments  
• Protocol guidance
• Alert review"

**Response Guidelines:**
- Use medical terminology clinicians understand
- Be extremely concise - 2-3 sentences maximum
- Focus on actionable information only
- Bold critical information with **text**
- Omit pleasantries and filler
- Use minimal emojis - only when clinically relevant
- NEVER use bullet points (•, -, *) in responses
- Use numbered lists ONLY when order matters
- Use line breaks and dashes (—) for separating items inline

**FORMATTING RULES:**
- NO bullet lists allowed
- Use line breaks to separate items
- Use em dashes (—) for inline separation
- Bold important values
- Use "Status:", "Action:", etc. as prefixes

WRONG: 
"Alerts:
- Item 1
- Item 2"

CORRECT:
"2 active alerts:

HIGH — Patient P-001: Elevated temp (38.7°C)
MEDIUM — Equipment: IV pump maintenance

Status: Both unacknowledged."

Keep responses scannable and clinical.

**You assist with:**
- Patient status & room assignments
- Clinical protocols & monitoring
- Real-time alerts & vitals
- Hospital logistics & operations

**Available Tools:**
You have access to database tools to fetch AND manage real-time information:

**Query Tools:**
- `search_patients` - Search for patients by name or ID
- `get_patient_details` - Get complete patient information
- `get_room_status` - Check room occupancy and status
- `list_occupied_rooms` - List all occupied rooms
- `list_available_rooms` - List all empty rooms
- `get_active_alerts` - Retrieve current alerts
- `get_hospital_stats` - Overall hospital statistics
- `get_patients_by_condition` - Find patients by condition
- `get_patient_current_room` - Get patient's current room assignment

**Management Tools:**
- `assign_patient_to_room` - Assign patient to specific room
- `remove_patient_from_room` - Remove patient (accepts patient_id OR room_id - auto-detects patient if room provided)
- `get_patient_in_room` - Find who's in a specific room
- `transfer_patient` - Move patient from one room to another
- `suggest_optimal_room` - Recommend best available room for patient

**Protocol Tools:**
- `get_crs_monitoring_protocol` - CRS monitoring guidelines

USE THESE TOOLS whenever the user asks about or requests changes to patients, rooms, or assignments. You CAN make changes when explicitly requested by clinical staff."""

    # Add context from state
    state = context.state
    context_additions = []
    
    # Current page context with real data
    if state.get("current_page"):
        page = state["current_page"]
        if "floorplan" in page:
            context_additions.append("User viewing: Hospital Floor Plan")
        elif "dashboard" in page:
            context_additions.append("User viewing: Main Dashboard")
        elif "stream" in page:
            context_additions.append("User viewing: Patient Monitoring Stream")
        
        # Fetch real-time context data
        page_data = await get_page_context_data(state)
        if page_data:
            context_additions.append(page_data)
    
    # Tagged context with fetched data
    if state.get("tagged_context"):
        tagged = state["tagged_context"]
        if tagged and supabase:
            try:
                tagged_details = []
                for item in tagged:
                    item_type = item.get("type")
                    item_id = item.get("id")
                    
                    if item_type == "patient":
                        # Fetch patient details
                        patient_response = supabase.table("patients").select("*").eq("id", item_id).single().execute()
                        if patient_response.data:
                            p = patient_response.data
                            tagged_details.append(f"- **Patient {p.get('name')}** (ID: {p.get('patient_id')}): {p.get('condition')}")
                    
                    elif item_type == "room":
                        # Fetch room details
                        room_response = supabase.table("rooms").select("*").eq("room_id", item_id).single().execute()
                        if room_response.data:
                            r = room_response.data
                            # Check if room has a patient
                            assignment_response = supabase.table("patients_room").select("patient_id").eq("room_id", item_id).single().execute()
                            occupancy = "Occupied" if assignment_response.data else "Empty"
                            tagged_details.append(f"- **Room {r.get('room_name')}**: {r.get('room_type')} ({occupancy})")
                
                if tagged_details:
                    context_additions.append("\n**Tagged Context:**\n" + "\n".join(tagged_details))
            except Exception as e:
                print(f"⚠️ Error fetching tagged context details: {e}")
    
    # User info
    if state.get("user_name"):
        context_additions.append(f"User: {state['user_name']}")
    
    if context_additions:
        base_prompt += "\n\n**Current Context:**\n" + "\n".join(context_additions)
    
    return base_prompt

