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
        self.api_key = None
        self.api_secret = None
        self.application_id = None
        self.private_key = None
        self.from_number = "12178020876"  # Same as existing system
        self.emergency_number = "+13854019951"
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
            print(f"⚠️ Voice Call Service disabled - Missing Vonage credentials")
    
    def make_emergency_call(
        self, 
        patient_id: str, 
        event_type: str,
        details: str = ""
    ) -> Optional[dict]:
        """
        Make an emergency voice call
        
        Args:
            patient_id: Patient ID
            event_type: Type of emergency (seizure, fall, agitation)
            details: Additional details
            
        Returns:
            Call response or None if failed
        """
        # Load credentials on first call
        self._load_credentials()
        
        if not self.enabled:
            print(f"📞 [DEMO MODE] Would call {self.emergency_number}: {event_type.upper()} for {patient_id}")
            return None
        
        try:
            # Import Vonage client (v4+ API) - same as existing /alerts/call
            from vonage import Auth, Vonage
            
            # Create TTS message
            event_msg = {
                "seizure": "SEIZURE DETECTED",
                "fall": "FALL DETECTED", 
                "extreme_agitation": "EXTREME AGITATION DETECTED"
            }.get(event_type, "EMERGENCY ALERT")
            
            tts_text = f"Haven Health Alert. {event_msg}. Patient ID {patient_id}. Medical assistance needed immediately."
            
            print(f"📞 CALLING {self.emergency_number}: {event_msg} for {patient_id}")
            
            # Convert escaped newlines to actual newlines in private key
            private_key_formatted = self.private_key.replace("\\n", "\n")
            
            # Create auth with application credentials for Voice API
            auth = Auth(
                api_key=self.api_key,
                api_secret=self.api_secret,
                application_id=self.application_id,
                private_key=private_key_formatted
            )
            client = Vonage(auth=auth)
            
            # Clean phone number
            to_number = self.emergency_number.replace("+", "").replace("-", "").replace(" ", "")
            
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
            
            # Make the call
            response = client.voice.create_call({
                "to": [{"type": "phone", "number": to_number}],
                "from_": {"type": "phone", "number": self.from_number},
                "ncco": ncco
            })
            
            call_uuid = response.uuid if hasattr(response, 'uuid') else str(response)
            print(f"✅ Voice call placed - UUID: {call_uuid}")
            return {"uuid": call_uuid, "to": self.emergency_number, "event": event_msg}
            
        except Exception as e:
            print(f"❌ Voice call failed: {e}")
            return None

# Global instance
voice_service = VoiceCallService()

