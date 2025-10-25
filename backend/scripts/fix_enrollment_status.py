"""
Fix enrollment_status for all patients in Supabase
This script updates all patients to have enrollment_status = 'active'
"""

from app.supabase_client import get_supabase_client
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Update all patients to have enrollment_status = 'active'"""
    supabase = get_supabase_client()

    if not supabase:
        print("❌ Supabase not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
        return

    try:
        # First, check current state
        print("📊 Checking current patient enrollment status...")
        response = supabase.table("patients").select("*").execute()

        if not response.data:
            print("⚠️ No patients found in database")
            return

        total_patients = len(response.data)
        active_count = sum(1 for p in response.data if p.get(
            'enrollment_status') == 'active')
        missing_count = sum(
            1 for p in response.data if not p.get('enrollment_status'))

        print(f"\n📈 Current Status:")
        print(f"   Total patients: {total_patients}")
        print(f"   Already active: {active_count}")
        print(f"   Missing enrollment_status: {missing_count}")
        print(
            f"   Other statuses: {total_patients - active_count - missing_count}")

        if active_count == total_patients:
            print("\n✅ All patients already have enrollment_status = 'active'")
            return

        # Update all patients to active
        print(f"\n🔄 Updating patients to enrollment_status = 'active'...")

        # Get all patient IDs that need updating
        patients_to_update = [
            p for p in response.data
            if p.get('enrollment_status') != 'active'
        ]

        updated_count = 0
        for patient in patients_to_update:
            try:
                supabase.table("patients") \
                    .update({"enrollment_status": "active"}) \
                    .eq("id", patient['id']) \
                    .execute()
                updated_count += 1
                print(
                    f"   ✓ Updated {patient.get('name', 'Unknown')} (ID: {patient.get('patient_id', 'N/A')})")
            except Exception as e:
                print(
                    f"   ✗ Failed to update {patient.get('name', 'Unknown')}: {e}")

        print(f"\n✅ Successfully updated {updated_count} patients")
        print(f"   All patients now have enrollment_status = 'active'")

        # Verify
        print("\n🔍 Verifying changes...")
        verify_response = supabase.table("patients") \
            .select("*") \
            .eq("enrollment_status", "active") \
            .execute()

        if verify_response.data:
            print(
                f"✅ Confirmed: {len(verify_response.data)} patients with enrollment_status = 'active'")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
