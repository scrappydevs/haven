"""
Alert Monitor - Automatic Nurse Calling on Critical Alerts
Listens for critical alerts and makes phone calls using Vonage Voice API
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any
from app.supabase_client import get_supabase_client
from app.infisical_config import get_secret

# Try to import Vonage Voice
try:
    import vonage
    VONAGE_API_KEY = get_secret("VONAGE_API_KEY") or os.getenv("VONAGE_API_KEY")
    VONAGE_API_SECRET = get_secret("VONAGE_API_SECRET") or os.getenv("VONAGE_API_SECRET")
    
    if VONAGE_API_KEY and VONAGE_API_SECRET:
        vonage_client = vonage.Client(
            key=VONAGE_API_KEY,
            secret=VONAGE_API_SECRET
        )
        voice = vonage.Voice(vonage_client)
        print(f"✅ Vonage Voice initialized for alert calling")
    else:
        voice = None
        print("⚠️  Vonage Voice not configured - calls will be mocked")
except ImportError:
    voice = None
    print("⚠️  Vonage library not installed - calls will be mocked")

# Nurse phone number
NURSE_PHONE_NUMBER = get_secret("NURSE_PHONE_NUMBER") or os.getenv("NURSE_PHONE_NUMBER") or "+14155170250"
HAVEN_PHONE_NUMBER = os.getenv("VONAGE_FROM_NUMBER") or "12178020876"  # Your Vonage number

supabase = get_supabase_client()


async def monitor_critical_alerts():
    """
    Poll database for new critical alerts and make phone calls
    """
    print(f"🚨 Alert Monitor Started")
    print(f"   Nurse Phone: {NURSE_PHONE_NUMBER}")
    print(f"   Polling every 5 seconds...")
    
    last_check = datetime.now()
    
    while True:
        try:
            # Check for new critical alerts since last check
            response = supabase.table("alerts") \
                .select("*") \
                .eq("severity", "critical") \
                .eq("status", "active") \
                .gt("triggered_at", last_check.isoformat()) \
                .execute()
            
            for alert in (response.data or []):
                await handle_critical_alert(alert)
            
            last_check = datetime.now()
            
        except Exception as e:
            print(f"❌ Error monitoring alerts: {e}")
        
        # Wait 5 seconds before next check
        await asyncio.sleep(5)


async def handle_critical_alert(alert: Dict[str, Any]):
    """
    Handle a critical alert - make phone call to nurse
    """
    alert_id = alert['id']
    patient_id = alert['patient_id']
    room_id = alert['room_id']
    message = alert['message']
    
    print(f"\n🚨 CRITICAL ALERT DETECTED: {alert_id}")
    print(f"   Patient: {patient_id}")
    print(f"   Room: {room_id}")
    print(f"   Message: {message}")
    
    # Fetch patient and room details
    try:
        patient_data = supabase.table("patients") \
            .select("name, condition") \
            .eq("patient_id", patient_id) \
            .single() \
            .execute()
        
        room_data = supabase.table("rooms") \
            .select("room_name") \
            .eq("room_id", room_id) \
            .single() \
            .execute()
        
        patient_name = patient_data.data['name'] if patient_data.data else patient_id
        room_name = room_data.data['room_name'] if room_data.data else 'Unknown Room'
        
    except Exception as e:
        print(f"⚠️  Error fetching details: {e}")
        patient_name = patient_id
        room_name = "Unknown Room"
    
    # Build call message
    call_message = (
        f"Critical alert at Haven Hospital. "
        f"{room_name}, patient {patient_name}. "
        f"{message}. "
        f"Please respond immediately."
    )
    
    print(f"📞 Calling nurse at {NURSE_PHONE_NUMBER}")
    print(f"   Message: {call_message}")
    
    # Make the call
    call_result = await make_voice_call(
        to=NURSE_PHONE_NUMBER,
        message=call_message,
        alert_id=alert_id
    )
    
    # Update alert metadata with call information
    try:
        # Get current metadata
        alert_data = supabase.table("alerts").select("metadata").eq("id", alert_id).single().execute()
        current_metadata = alert_data.data.get('metadata', {}) if alert_data.data else {}
        
        # Add call info to metadata
        current_metadata['call'] = {
            "phone_number": NURSE_PHONE_NUMBER,
            "call_status": call_result['status'],
            "call_id": call_result.get('call_id'),
            "message": call_message,
            "initiated_at": datetime.now().isoformat()
        }
        
        # Update alert
        supabase.table("alerts").update({
            "metadata": current_metadata
        }).eq("id", alert_id).execute()
        
        print(f"✅ Call info added to alert metadata")
    except Exception as e:
        print(f"⚠️  Failed to update alert metadata: {e}")


async def make_voice_call(to: str, message: str, alert_id: str) -> Dict[str, Any]:
    """
    Make an outbound voice call using Vonage Voice API
    """
    if not voice:
        # Mock mode
        print(f"⚠️  MOCK CALL (Vonage not configured)")
        return {
            "status": "mock",
            "call_id": f"mock-{alert_id}",
            "message": "Call would be placed in production"
        }
    
    try:
        # Remove '+' from phone numbers for Voice API
        to_number = to.replace("+", "").replace(" ", "").replace("-", "")
        from_number = HAVEN_PHONE_NUMBER.replace("+", "").replace(" ", "").replace("-", "")
        
        # Make Vonage Voice call with text-to-speech
        response = voice.create_call({
            "to": [{"type": "phone", "number": to_number}],
            "from": {"type": "phone", "number": from_number},
            "ncco": [
                {
                    "action": "talk",
                    "text": message,
                    "voiceName": "Amy",  # Professional female voice
                    "level": 0.9
                },
                {
                    "action": "talk",
                    "text": f"Press 1 to acknowledge this alert, or hang up to continue.",
                    "voiceName": "Amy",
                    "bargeIn": True
                },
                {
                    "action": "input",
                    "type": ["dtmf"],
                    "dtmf": {
                        "maxDigits": 1,
                        "timeOut": 10
                    },
                    "eventUrl": [f"{os.getenv('BACKEND_URL')}/api/alerts/call-response"]
                }
            ]
        })
        
        call_uuid = response['uuid']
        print(f"✅ Call initiated: {call_uuid}")
        
        return {
            "status": "initiated",
            "call_id": call_uuid,
            "message": "Call successfully placed"
        }
        
    except Exception as e:
        print(f"❌ Failed to make call: {e}")
        return {
            "status": "failed",
            "call_id": None,
            "message": str(e)
        }


# Standalone script entry point
if __name__ == "__main__":
    print("🚀 Starting Alert Monitor...")
    asyncio.run(monitor_critical_alerts())

