"""
Generate 47 synthetic patients for Haven demo
Run this BEFORE the hackathon to have patient data ready
"""

import json
import random
from pathlib import Path

# Patient names (diverse, realistic)
FIRST_NAMES = [
    "Sarah", "Michael", "Emma", "David", "Linda", "James", "Maria", "Robert",
    "Jennifer", "William", "Patricia", "Richard", "Elizabeth", "Charles", "Barbara",
    "Joseph", "Susan", "Thomas", "Jessica", "Christopher", "Karen", "Daniel",
    "Nancy", "Matthew", "Lisa", "Anthony", "Betty", "Mark", "Margaret", "Donald",
    "Sandra", "Steven", "Ashley", "Paul", "Kimberly", "Andrew", "Emily", "Joshua",
    "Donna", "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George",
    "Melissa"
]

LAST_NAMES = [
    "Chen", "Torres", "Wilson", "Kim", "Wu", "Anderson", "Garcia", "Johnson",
    "Lee", "Brown", "Martinez", "Davis", "Rodriguez", "Miller", "Hernandez",
    "Lopez", "Gonzalez", "Perez", "Taylor", "Moore", "Jackson", "Martin",
    "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres",
    "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall",
    "Rivera", "Campbell"
]


def generate_patient(patient_id: int) -> dict:
    """Generate a single patient profile"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    # Age distribution: mostly 50-80 (MM typically affects older adults)
    age = random.randint(50, 80)

    # Gender distribution: slightly more males (MM is more common in males)
    gender = random.choice(["Male", "Female", "Male"])

    # Ethnicity (diverse for FDA FDORA compliance)
    ethnicities = ["Caucasian", "African American",
                   "Hispanic", "Asian", "Other"]
    # Realistic US distribution
    ethnicity_weights = [0.6, 0.15, 0.15, 0.08, 0.02]
    ethnicity = random.choices(ethnicities, weights=ethnicity_weights)[0]

    # MM Stage (most patients are Stage II or III)
    mm_stage = random.choice(["Stage II", "Stage III", "Stage III"])

    # Number of prior lines of therapy (inclusion criteria: ≥3)
    prior_lines = random.randint(3, 6)

    # ECOG performance status (0-2 for inclusion)
    ecog = random.choice([0, 1, 1, 2])

    # Baseline vitals
    baseline_hr = random.randint(65, 90)
    baseline_rr = random.randint(12, 18)
    baseline_bp_sys = random.randint(110, 140)
    baseline_bp_dia = random.randint(70, 90)

    # CRS risk (0.0-0.5, higher means more likely to develop CRS)
    baseline_crs_risk = round(random.uniform(0.10, 0.40), 2)

    # Enrollment date (spread over 18 months)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    enrollment_date = f"2024-{month:02d}-{day:02d}"

    # Infusion count (1-4, most are early in treatment)
    infusion_count = random.randint(1, 4)

    return {
        "id": patient_id,
        "name": f"{first_name} {last_name}",
        "age": age,
        "gender": gender,
        "ethnicity": ethnicity,
        "condition": f"Multiple Myeloma {mm_stage}",
        "prior_lines": prior_lines,
        "ecog_status": ecog,
        "enrollment_date": enrollment_date,
        "enrollment_status": "active",  # 'active', 'completed', or 'withdrawn'
        "infusion_count": infusion_count,
        "baseline_vitals": {
            "heart_rate": baseline_hr,
            "respiratory_rate": baseline_rr,
            "blood_pressure": f"{baseline_bp_sys}/{baseline_bp_dia}",
            "temperature": 36.8
        },
        "baseline_crs_risk": baseline_crs_risk,
    }


def main():
    """Generate 47 patients and save to JSON"""
    patients = []

    for i in range(1, 48):  # 1-47
        patient = generate_patient(i)
        patients.append(patient)

    # Save to JSON
    output_file = Path(__file__).parent.parent / "data" / "patients.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(patients, f, indent=2)

    print(f"✅ Generated 47 patients")
    print(f"   Saved to: {output_file}")

    # Print demographics summary
    genders = [p["gender"] for p in patients]
    ethnicities = [p["ethnicity"] for p in patients]

    print(f"\n📊 Demographics:")
    print(
        f"   Female: {genders.count('Female')} ({genders.count('Female')/47*100:.1f}%)")
    print(
        f"   Male: {genders.count('Male')} ({genders.count('Male')/47*100:.1f}%)")
    print(
        f"\n   Caucasian: {ethnicities.count('Caucasian')} ({ethnicities.count('Caucasian')/47*100:.1f}%)")
    print(
        f"   African American: {ethnicities.count('African American')} ({ethnicities.count('African American')/47*100:.1f}%)")
    print(
        f"   Hispanic: {ethnicities.count('Hispanic')} ({ethnicities.count('Hispanic')/47*100:.1f}%)")
    print(
        f"   Asian: {ethnicities.count('Asian')} ({ethnicities.count('Asian')/47*100:.1f}%)")


if __name__ == "__main__":
    main()
