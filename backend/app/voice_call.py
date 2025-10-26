"""
Vonage Voice Call Integration for Emergency Alerts
"""
import os
from datetime import datetime
from typing import Optional
from app.infisical_config import get_secret

class VoiceCallService:
    """Handle emergency voice calls using Vonage"""
    
    def __init__(self):
        # Credentials loaded lazily on first call
        self._credentials_loaded = False
        self._client = None  # Cache Vonage client for speed
        self.api_key = None
        self.api_secret = None
        self.application_id = None
        self.private_key = None
        self.from_number = "12178020876"  # Vonage number
        self.emergency_number = "+14155170250"  # Primary nurse contact
        self.enabled = False
    
    def _load_credentials(self):
        """Load credentials from Infisical (lazy loading)"""
        if self._credentials_loaded:
            return
        
        self._credentials_loaded = True
        
        # Get credentials from Infisical (same as existing /alerts/call endpoint)
        self.api_key = get_secret("VONAGE_API_KEY")
        self.api_secret = get_secret("VONAGE_API_SECRET")
        self.application_id = get_secret("VONAGE_APPLICATION_ID")
        self.private_key = get_secret("VONAGE_PRIVATE_KEY")
        
        self.enabled = bool(self.api_key and self.api_secret and self.application_id and self.private_key)
        
        if self.enabled:
            print(f"✅ Voice Call Service enabled - Emergency: {self.emergency_number}")
        else:
            missing = []
            if not self.api_key: missing.append("VONAGE_API_KEY")
            if not self.api_secret: missing.append("VONAGE_API_SECRET")
            if not self.application_id: missing.append("VONAGE_APPLICATION_ID")
            if not self.private_key: missing.append("VONAGE_PRIVATE_KEY")
            print(f"⚠️ Voice Call Service disabled - Missing: {', '.join(missing)}")
            print(f"   Set these in Render environment variables or Infisical")
    
    def make_emergency_call(
        self, 
        patient_id: str, 
        event_type: str,
        details: str = "",
        to_number: Optional[str] = None
    ) -> Optional[dict]:
        """
        Make an emergency voice call
        
        Args:
            patient_id: Patient ID
            event_type: Type of emergency (seizure, fall, agitation, urgent_alert)
            details: Additional details
            to_number: Optional override for phone number (defaults to emergency_number)
            
        Returns:
            Call response or None if failed
        """
        # Load credentials on first call
        self._load_credentials()
        
        # Use provided number or default emergency number
        target_number = to_number or self.emergency_number
        
        if not self.enabled:
            print(f"📞 [DEMO MODE] Would call {target_number}: {event_type.upper()} for {patient_id}")
            print(f"   ⚠️  Vonage not configured - check Render environment variables")
            print(f"   Required: VONAGE_API_KEY, VONAGE_API_SECRET, VONAGE_APPLICATION_ID, VONAGE_PRIVATE_KEY")
            return None
        
        try:
            # Create TTS message
            event_msg = {
                "seizure": "SEIZURE DETECTED",
                "fall": "FALL DETECTED", 
                "extreme_agitation": "EXTREME AGITATION DETECTED"
            }.get(event_type, "EMERGENCY ALERT")
            
            # Build message based on type
            if event_type == "urgent_alert":
                # Manual alert from dashboard
                tts_text = f"Haven Health Alert. {details}. Please respond immediately."
            else:
                # Automatic alert (seizure, fall, etc)
                tts_text = f"Haven Health Alert. {event_msg}. Patient ID {patient_id}. Medical assistance needed immediately."
            
            print(f"📞 CALLING {target_number}: {event_type.upper()} for {patient_id}")
            
            # Initialize Vonage client once and cache it (JWT signing is slow!)
            if self._client is None:
                print(f"🔄 Initializing Vonage client (first call)...")
                from vonage import Auth, Vonage
                
                # Convert escaped newlines to actual newlines in private key
                private_key_formatted = self.private_key.replace("\\n", "\n")
                
                # Create auth with application credentials for Voice API
                auth = Auth(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    application_id=self.application_id,
                    private_key=private_key_formatted
                )
                self._client = Vonage(auth=auth)
                print(f"✅ Client initialized and cached")
            
            client = self._client
            
            # Clean phone number
            to_number_clean = target_number.replace("+", "").replace("-", "").replace(" ", "")
            
            # Create NCCO (Nexmo Call Control Objects)
            ncco = [
                {
                    "action": "talk",
                    "text": tts_text,
                    "voiceName": "Amy",
                    "bargeIn": False
                },
                {
                    "action": "talk",
                    "text": f"I repeat. {tts_text}",
                    "voiceName": "Amy",
                    "bargeIn": False
                }
            ]
            
            # Make the call asynchronously (fire-and-forget for speed)
            import threading
            import time
            
            call_start_time = time.time()
            call_result = {"uuid": None, "error": None}
            
            def make_call_async():
                try:
                    response = client.voice.create_call({
                        "to": [{"type": "phone", "number": to_number_clean}],
                        "from_": {"type": "phone", "number": self.from_number},
                        "ncco": ncco
                    })
                    call_uuid = response.uuid if hasattr(response, 'uuid') else str(response)
                    call_result["uuid"] = call_uuid
                    elapsed = time.time() - call_start_time
                    print(f"✅ Call placed - UUID: {call_uuid} → {target_number} ({elapsed:.1f}s)")
                except Exception as e:
                    call_result["error"] = str(e)
                    print(f"❌ Call failed: {e}")
            
            # Start call in background thread (don't wait for Vonage response)
            thread = threading.Thread(target=make_call_async, daemon=True)
            thread.start()
            
            # Return immediately with pending status
            return {
                "uuid": "pending",  # Will be updated in logs when call completes
                "to": target_number, 
                "event": event_msg if event_type != "urgent_alert" else "urgent_alert",
                "status": "placing_call"
            }
            
        except Exception as e:
            print(f"❌ Voice call failed: {e}")
            return None

# Global instance
voice_service = VoiceCallService()

# Pre-warm the client on module import for instant calls
def _prewarm_client():
    """Initialize Vonage client in background to avoid first-call delay"""
    import threading
    def init():
        try:
            voice_service._load_credentials()
            if voice_service.enabled and voice_service._client is None:
                from vonage import Auth, Vonage
                private_key = voice_service.private_key.replace("\\n", "\n")
                auth = Auth(
                    api_key=voice_service.api_key,
                    api_secret=voice_service.api_secret,
                    application_id=voice_service.application_id,
                    private_key=private_key
                )
                voice_service._client = Vonage(auth=auth)
                print(f"⚡ Vonage client pre-warmed - calls will be instant!")
        except Exception as e:
            print(f"⚠️ Client pre-warm failed: {e}")
    
    threading.Thread(target=init, daemon=True).start()

# Start pre-warming immediately
_prewarm_client()

