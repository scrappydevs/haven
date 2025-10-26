-- Mock data for alerts table
-- This creates realistic test alerts with various severities and types
-- Note: alert_type must be one of: vital_sign, crs, medication, fall_risk, equipment, protocol, other

-- Clear existing test data (optional - comment out if you want to keep existing data)
-- DELETE FROM alerts WHERE patient_id = 'P-DHE-001';

-- Insert mock alerts
INSERT INTO alerts (alert_type, severity, patient_id, room_id, title, description, status, triggered_at, metadata)
VALUES
  -- Critical alerts
  (
    'vital_sign',
    'critical',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Critical Heart Rate Spike',
    'Patient heart rate elevated to 145 bpm. Sustained tachycardia for 5+ minutes.',
    'active',
    NOW() - INTERVAL '2 minutes',
    '{"heart_rate": 145, "baseline": 72, "duration_minutes": 5}'::jsonb
  ),
  (
    'medication',
    'critical',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Medication Allergy Alert',
    'Attempted to administer Penicillin. Patient has documented severe allergy.',
    'active',
    NOW() - INTERVAL '5 minutes',
    '{"medication": "Penicillin", "allergy_severity": "severe", "reaction_type": "anaphylaxis"}'::jsonb
  ),

  -- High severity alerts
  (
    'crs',
    'high',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Critical Lab Values - Potassium',
    'Potassium level at 6.2 mEq/L (critical high). Immediate intervention required.',
    'active',
    NOW() - INTERVAL '15 minutes',
    '{"test": "Potassium", "value": 6.2, "unit": "mEq/L", "normal_range": "3.5-5.0"}'::jsonb
  ),
  (
    'fall_risk',
    'high',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'High Fall Risk - Mobility Change',
    'Patient attempted to ambulate without assistance. Recent mobility assessment shows high fall risk.',
    'active',
    NOW() - INTERVAL '20 minutes',
    '{"fall_risk_score": 8, "previous_falls": 1, "assistance_required": true}'::jsonb
  ),
  (
    'vital_sign',
    'high',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Blood Pressure Elevated',
    'BP reading 168/102 mmHg. Patient has history of hypertension.',
    'active',
    NOW() - INTERVAL '10 minutes',
    '{"systolic": 168, "diastolic": 102, "baseline_systolic": 130, "baseline_diastolic": 85}'::jsonb
  ),

  -- Medium severity alerts
  (
    'medication',
    'medium',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Medication Overdue',
    'Pain medication due 30 minutes ago. Patient requesting pain relief.',
    'active',
    NOW() - INTERVAL '30 minutes',
    '{"medication": "Morphine 5mg", "scheduled_time": "14:00", "patient_pain_level": 7}'::jsonb
  ),
  (
    'vital_sign',
    'medium',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Temperature Elevated',
    'Patient temperature 101.2°F. Monitoring for infection.',
    'active',
    NOW() - INTERVAL '45 minutes',
    '{"temperature": 101.2, "unit": "F", "baseline": 98.6, "trend": "increasing"}'::jsonb
  ),
  (
    'other',
    'medium',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Patient Call - Pain Management',
    'Patient reports pain level 6/10. Requesting assessment.',
    'active',
    NOW() - INTERVAL '8 minutes',
    '{"pain_level": 6, "location": "surgical site", "last_medication": "2 hours ago"}'::jsonb
  ),

  -- Low severity alerts
  (
    'vital_sign',
    'low',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Routine Vital Signs Due',
    'Scheduled vital signs check due in next 15 minutes.',
    'active',
    NOW() - INTERVAL '5 minutes',
    '{"check_type": "routine", "frequency": "q4h", "last_check": "4 hours ago"}'::jsonb
  ),
  (
    'crs',
    'low',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Lab Results Available',
    'Complete Blood Count results available for review.',
    'active',
    NOW() - INTERVAL '12 minutes',
    '{"test_type": "CBC", "ordered_by": "Dr. Smith", "status": "final"}'::jsonb
  ),

  -- Info alerts
  (
    'other',
    'info',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'New Patient Admission',
    'Patient admitted for observation. Initial assessment pending.',
    'active',
    NOW() - INTERVAL '3 minutes',
    '{"admission_type": "observation", "diagnosis": "chest pain", "attending": "Dr. Johnson"}'::jsonb
  ),
  (
    'protocol',
    'info',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Discharge Orders Ready',
    'Patient cleared for discharge. Awaiting family pickup.',
    'active',
    NOW() - INTERVAL '25 minutes',
    '{"discharge_time": "16:00", "transportation": "family", "prescriptions_ready": true}'::jsonb
  ),

  -- Some acknowledged alerts (won't show in active list)
  (
    'vital_sign',
    'medium',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'Blood Sugar Elevated',
    'Blood glucose 245 mg/dL. Insulin administered as per protocol.',
    'acknowledged',
    NOW() - INTERVAL '1 hour',
    '{"glucose": 245, "unit": "mg/dL", "insulin_given": "4 units", "recheck_due": "1 hour"}'::jsonb
  ),
  (
    'medication',
    'low',
    'P-DHE-001',
    '9289ef5b-7822-49f2-accd-d790aeb58e7a',
    'PRN Medication Administered',
    'Tylenol 650mg given for headache. Patient comfortable.',
    'acknowledged',
    NOW() - INTERVAL '2 hours',
    '{"medication": "Acetaminophen", "dose": "650mg", "reason": "headache", "effectiveness": "good"}'::jsonb
  );

-- Display summary of inserted data
SELECT
  severity,
  status,
  COUNT(*) as count
FROM alerts
WHERE patient_id = 'P-DHE-001'
GROUP BY severity, status
ORDER BY
  CASE severity
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
    WHEN 'info' THEN 5
  END,
  status;
