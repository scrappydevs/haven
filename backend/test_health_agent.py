#!/usr/bin/env python3
"""
Quick test script to verify Health Agent integration
Run: python test_health_agent.py
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.health_agent import health_agent

async def test_health_agent():
    """Test the health agent with sample data"""
    print("=" * 60)
    print("🏥 TESTING HAVEN HEALTH AGENT")
    print("=" * 60)
    
    # Check status
    print("\n1. Checking agent status...")
    status = health_agent.get_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Claude Available: {status['claude_available']}")
    print(f"   Patients: {status['patients_monitored']}")
    print(f"   Alerts: {status['active_alerts']}")
    
    # Test with sample patient data
    print("\n2. Testing with sample patient (P-TEST-001)...")
    
    # Normal vitals
    normal_vitals = {
        "heart_rate": 75,
        "temperature": 37.0,
        "blood_pressure": "120/80",
        "spo2": 98
    }
    normal_cv = {
        "distress_score": 2,
        "movement_score": 3,
        "posture_alert": False
    }
    
    result = await health_agent.analyze_patient("P-TEST-001", normal_vitals, normal_cv)
    print(f"   Severity: {result['severity']}")
    print(f"   Concerns: {result['concerns']}")
    print(f"   Confidence: {result['confidence']}")
    
    # Critical vitals
    print("\n3. Testing with critical patient (P-TEST-002)...")
    critical_vitals = {
        "heart_rate": 145,
        "temperature": 39.8,
        "blood_pressure": "90/60",
        "spo2": 88
    }
    critical_cv = {
        "distress_score": 9,
        "movement_score": 8,
        "posture_alert": True
    }
    
    result = await health_agent.analyze_patient("P-TEST-002", critical_vitals, critical_cv)
    print(f"   Severity: {result['severity']}")
    print(f"   Concerns: {result['concerns']}")
    print(f"   Action: {result['recommended_action']}")
    
    # Check alerts
    print("\n4. Checking active alerts...")
    alerts = health_agent.get_active_alerts()
    print(f"   Active Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"   - {alert['patient_id']}: {alert['severity']}")
    
    # Check patients
    print("\n5. Checking monitored patients...")
    patients = health_agent.get_all_patients()
    print(f"   Total Patients: {len(patients)}")
    for pid in patients.keys():
        print(f"   - {pid}")
    
    print("\n" + "=" * 60)
    print("✅ HEALTH AGENT TEST COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start backend: python main.py")
    print("2. Check API: curl http://localhost:8000/health-agent/status")
    print("3. Start video stream in dashboard")
    print("4. Watch alerts in real-time!")

if __name__ == "__main__":
    asyncio.run(test_health_agent())

