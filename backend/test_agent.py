"""
Quick script to test the Patient Guardian Agent
"""
import requests
import time

API_URL = "http://localhost:8000"

def test_agent():
    print("=" * 60)
    print("🧪 Patient Guardian Agent Test")
    print("=" * 60)

    # Test 1: Set baseline for a patient
    print("\n1. Setting baseline for P-001...")
    baseline_response = requests.post(f"{API_URL}/agent/set-baseline", json={
        "patient_id": "P-001",
        "heart_rate": 75,
        "respiratory_rate": 14,
        "crs_score": 0.0
    })
    print(f"   Response: {baseline_response.json()}")

    # Test 2: Check monitoring config (should be BASELINE initially)
    print("\n2. Checking monitoring config...")
    config_response = requests.get(f"{API_URL}/monitoring/config/P-001")
    config = config_response.json()
    print(f"   Current level: {config['level']}")
    print(f"   Enabled metrics: {config['enabled_metrics']}")

    # Test 3: Simulate enhanced monitoring activation
    print("\n3. Testing manual enhanced monitoring activation...")
    enhanced_response = requests.post(
        f"{API_URL}/monitoring/enhanced/P-001",
        params={
            "duration_minutes": 5,
            "reason": "Manual test - simulating agent decision"
        }
    )
    print(f"   Response: {enhanced_response.json()}")

    # Test 4: Check config after enhancement
    print("\n4. Verifying enhanced monitoring is active...")
    time.sleep(1)
    config_response = requests.get(f"{API_URL}/monitoring/config/P-001")
    config = config_response.json()
    print(f"   Current level: {config['level']}")
    print(f"   Enabled metrics: {config['enabled_metrics']}")
    print(f"   Expires at: {config['expires_at']}")

    # Test 5: Check alert history
    print("\n5. Checking agent alert history...")
    history_response = requests.get(f"{API_URL}/agent/alert-history/P-001")
    history = history_response.json()
    print(f"   Total alerts: {history['count']}")

    # Test 6: Return to baseline
    print("\n6. Returning to baseline monitoring...")
    baseline_response = requests.post(
        f"{API_URL}/monitoring/baseline/P-001",
        params={"reason": "Test completed"}
    )
    print(f"   Response: {baseline_response.json()}")

    print("\n" + "=" * 60)
    print("✅ Agent test completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start a patient stream from the Stream page")
    print("2. Assign the stream to a box in Dashboard")
    print("3. Watch for agent decisions in real-time as metrics change")
    print("4. Look for:")
    print("   - Monitoring level badges (📊 BASELINE, ⚡ ENHANCED, 🚨 CRITICAL)")
    print("   - Agent alert toasts in top-right corner")
    print("   - Agent decision logs in activity feed")

if __name__ == "__main__":
    test_agent()
