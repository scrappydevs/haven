-- Update Dheeraj Vislawath to Seizure Patient
-- Run this in Supabase SQL Editor

-- Update patient record
UPDATE public.patients
SET 
  age = 20,
  date_of_birth = '2004-03-15',
  condition = 'Epilepsy - Seizure Disorder Monitoring',
  enrollment_date = '2025-10-22',
  ecog_status = 1,
  prior_treatment_lines = 0,
  infusion_count = 0,
  baseline_vitals = '{
    "heart_rate": 68,
    "respiratory_rate": 14,
    "temperature": 36.6,
    "oxygen_saturation": 99,
    "blood_pressure": "112/72",
    "blood_pressure_systolic": 112,
    "blood_pressure_diastolic": 72,
    "weight_kg": 72,
    "height_cm": 178,
    "bmi": 22.7
  }'::jsonb,
  baseline_crs_risk = 0.25,
  notes = 'Admitted for seizure monitoring and medication adjustment. History of generalized tonic-clonic seizures. Last seizure 3 days ago. On video EEG monitoring. Adjusting antiepileptic medications. Patient is computer science student. Family history of epilepsy. Compliant with medication regimen.',
  updated_at = NOW()
WHERE patient_id = 'P-DHE-001';

-- Clear old medical history for Dheeraj
DELETE FROM public.medical_history WHERE patient_id = 'P-DHE-001';

-- Add seizure-specific medical history
INSERT INTO public.medical_history (patient_id, entry_type, entry_date, title, description, severity, status, provider, metadata) VALUES
  ('P-DHE-001', 'diagnosis', '2020-05-15', 'Epilepsy - Generalized Tonic-Clonic Seizures', 'Diagnosed at age 16 following two witnessed generalized seizures. EEG showed generalized spike-wave activity.', 'high', 'chronic', 'Dr. Sarah Mitchell', '{"seizure_type": "generalized_tonic_clonic", "age_at_diagnosis": 16, "eeg_findings": "generalized_spike_wave"}'),
  
  ('P-DHE-001', 'procedure', '2025-10-22', 'Video EEG Monitoring Initiated', '24-hour continuous video EEG monitoring for seizure characterization and medication adjustment.', 'medium', 'active', 'Neurology Team', '{"monitoring_duration": "72_hours", "electrodes": 21, "video_recording": true}'),
  
  ('P-DHE-001', 'medication', '2020-06-01', 'Levetiracetam 1000mg BID', 'Primary antiepileptic. Well-tolerated. Dose increased from 500mg due to breakthrough seizures.', 'high', 'active', 'Dr. Mitchell', '{"dosage": "1000mg", "frequency": "BID", "route": "PO", "therapeutic_level": "monitored", "years_on_medication": 5}'),
  
  ('P-DHE-001', 'medication', '2025-10-22', 'Lacosamide 200mg BID', 'Added as adjunctive therapy due to inadequate seizure control on monotherapy.', 'high', 'active', 'Dr. Mitchell', '{"dosage": "200mg", "frequency": "BID", "route": "PO", "indication": "adjunctive_therapy", "start_date": "2025-10-22"}'),
  
  ('P-DHE-001', 'symptom', '2025-10-22', 'Seizure Event - 3 Days Ago', 'Witnessed generalized tonic-clonic seizure at home. Duration ~90 seconds. Post-ictal confusion for 20 minutes. No injury.', 'critical', 'historical', 'Dr. Mitchell', '{"seizure_duration_sec": 90, "postictal_period_min": 20, "witnessed": true, "injury": false, "trigger": "sleep_deprivation"}'),
  
  ('P-DHE-001', 'symptom', '2025-10-21', 'Aura Symptoms', 'Patient reports visual auras (flashing lights) preceding recent seizure. Typical prodrome for him.', 'medium', 'active', 'Nurse Rodriguez', '{"aura_type": "visual", "description": "flashing_lights", "duration_sec": 10, "predictive": true}'),
  
  ('P-DHE-001', 'vital_measurement', '2025-10-23', 'Post-Seizure Vitals', 'Vitals taken 2 hours after witnessed seizure event', 'medium', 'historical', 'Nurse Johnson', '{"heart_rate": 92, "blood_pressure": "128/82", "temperature": 37.2, "respiratory_rate": 18, "oxygen_saturation": 98, "consciousness": "alert_oriented", "postictal_state": "resolved"}'),
  
  ('P-DHE-001', 'vital_measurement', '2025-10-25', 'Current Vitals', 'Baseline vitals, no seizure activity for 48h', 'low', 'active', 'Nurse Chen', '{"heart_rate": 68, "blood_pressure": "112/72", "temperature": 36.6, "respiratory_rate": 14, "oxygen_saturation": 99, "seizure_free_hours": 72}'),
  
  ('P-DHE-001', 'lab_result', '2025-10-23', 'Antiepileptic Drug Levels', 'Levetiracetam level therapeutic. Lacosamide pending.', 'info', 'active', 'Lab', '{"levetiracetam_level": 25, "levetiracetam_therapeutic_range": "12-46 mcg/mL", "lacosamide_level": "pending"}'),
  
  ('P-DHE-001', 'note', '2025-10-24', 'Neurology Consult Note', 'Breakthrough seizures despite levetiracetam monotherapy. Added lacosamide. Continue video EEG. Counsel on seizure precautions. Avoid driving until seizure-free for 6 months per state law.', 'high', 'active', 'Dr. Mitchell', '{"med_adjustment": "added_lacosamide", "driving_restriction": true, "follow_up_weeks": 2}'),
  
  ('P-DHE-001', 'family_history', '2020-05-15', 'Maternal Grandmother: Epilepsy', 'Family history of seizure disorder on maternal side. Grandmother had late-onset epilepsy.', 'info', 'active', 'Dr. Mitchell', '{"relative": "maternal_grandmother", "condition": "epilepsy", "onset_age": "late"}'),
  
  ('P-DHE-001', 'social_history', '2025-10-22', 'Computer Science Student', 'College student. Reports stress and sleep deprivation as potential triggers. Uses computer/screens extensively. Good medication compliance.', 'info', 'active', 'Social Work', '{"occupation": "student", "major": "computer_science", "triggers": ["stress", "sleep_deprivation", "screen_time"], "compliance": "good"}');

-- Add seizure-specific alerts
DELETE FROM public.alerts WHERE patient_id = 'P-DHE-001';

INSERT INTO public.alerts (
  patient_id,
  alert_type,
  severity,
  title,
  description,
  status,
  triggered_by,
  triggered_at,
  acknowledged_by,
  acknowledged_at,
  metadata
) VALUES 
  (
    'P-DHE-001',
    'vital_sign',
    'critical',
    'Seizure Activity Detected',
    'Video EEG detected generalized seizure activity. Duration 90 seconds. Patient protected from injury. Post-ictal monitoring initiated.',
    'resolved',
    'EEG Monitoring System',
    NOW() - INTERVAL '3 days',
    'Dr. Mitchell',
    NOW() - INTERVAL '3 days',
    '{"seizure_duration_sec": 90, "seizure_type": "generalized_tonic_clonic", "eeg_confirmed": true, "injury": false, "intervention": "protected_airway"}'::jsonb
  ),
  (
    'P-DHE-001',
    'medication',
    'high',
    'New Antiepileptic Started',
    'Lacosamide 200mg BID initiated. Monitor for dizziness, diplopia. Check drug level in 3 days.',
    'active',
    'Pharmacy System',
    NOW() - INTERVAL '3 days',
    'Nurse Rodriguez',
    NOW() - INTERVAL '3 days',
    '{"medication": "lacosamide", "dosage": "200mg BID", "monitoring": ["dizziness", "diplopia", "drug_level"], "level_check_date": "2025-10-28"}'::jsonb
  ),
  (
    'P-DHE-001',
    'protocol',
    'high',
    'Seizure Precautions Active',
    'Patient on seizure precautions: Padded bed rails, no bathing alone, assistance with ambulation, pulse ox monitoring.',
    'active',
    'Nursing Protocol',
    NOW() - INTERVAL '3 days',
    NULL,
    NULL,
    '{"precautions": ["padded_rails", "bathroom_supervision", "assisted_ambulation"], "monitoring": "continuous", "fall_risk": "high"}'::jsonb
  );

-- Add seizure-specific vital signs pattern
-- Clear old vitals for Dheeraj
DELETE FROM public.vital_signs WHERE patient_id = 'P-DHE-001';

-- Add vitals showing post-seizure recovery
DO $$
DECLARE
  hour_offset INTEGER;
  base_hr NUMERIC := 68;
  base_temp NUMERIC := 36.6;
  base_rr NUMERIC := 14;
BEGIN
  FOR hour_offset IN 0..11 LOOP
    INSERT INTO public.vital_signs (
      patient_id,
      recorded_at,
      heart_rate,
      respiratory_rate,
      temperature,
      oxygen_saturation,
      blood_pressure_systolic,
      blood_pressure_diastolic,
      crs_score,
      crs_grade,
      pain_level,
      consciousness_level,
      measurement_type,
      recorded_by,
      location,
      notes
    ) VALUES (
      'P-DHE-001',
      NOW() - (hour_offset * 4 || ' hours')::INTERVAL,
      -- Post-seizure tachycardia that resolves
      CASE 
        WHEN hour_offset >= 10 THEN base_hr + 24 + (RANDOM() * 8)  -- Post-seizure: 92-100 bpm
        WHEN hour_offset >= 8 THEN base_hr + 12 + (RANDOM() * 6)   -- Recovering: 80-86 bpm
        ELSE base_hr + (RANDOM() * 6 - 3)  -- Normal: 65-71 bpm
      END,
      base_rr + (RANDOM() * 2 - 1),
      base_temp + (RANDOM() * 0.3 - 0.15),
      98 + (RANDOM() * 2),
      110 + (RANDOM() * 10 - 5),
      70 + (RANDOM() * 8 - 4),
      0.0,  -- No CRS for seizure patient
      0,
      (RANDOM() * 2)::INTEGER,
      CASE 
        WHEN hour_offset >= 10 THEN 'confused'  -- Post-ictal
        ELSE 'alert'
      END,
      CASE 
        WHEN hour_offset >= 10 THEN 'alert_triggered'
        ELSE 'routine'
      END,
      CASE WHEN hour_offset % 2 = 0 THEN 'Nurse Johnson' ELSE 'Nurse Chen' END,
      'Neuro ICU',
      CASE 
        WHEN hour_offset >= 10 THEN '⚠️ POST-SEIZURE: Patient in post-ictal state. Protecting airway. Vitals stable. Monitoring for additional seizure activity.'
        WHEN hour_offset >= 8 THEN 'Post-ictal confusion resolving. Patient becoming more alert. Vitals normalizing. No further seizure activity.'
        WHEN hour_offset = 0 THEN 'Patient fully alert and oriented. Seizure-free for 48h. Video EEG monitoring continues. Medication levels therapeutic.'
        ELSE 'Routine neuro checks. Patient alert. No seizure activity. Compliance with medications. Family visiting.'
      END
    );
  END LOOP;
END $$;

-- Verify updates
SELECT 
  patient_id,
  name,
  age,
  condition,
  notes
FROM public.patients
WHERE patient_id IN ('P-DHE-001', 'P-DAV-001');

SELECT 
  patient_id,
  entry_type,
  title,
  severity,
  entry_date
FROM public.medical_history
WHERE patient_id = 'P-DHE-001'
ORDER BY entry_date DESC;

SELECT 
  patient_id,
  severity,
  title,
  status
FROM public.alerts
WHERE patient_id = 'P-DHE-001';

SELECT 
  'Dheeraj Updated to Seizure Patient' as status,
  (SELECT COUNT(*) FROM public.medical_history WHERE patient_id = 'P-DHE-001') as medical_history_entries,
  (SELECT COUNT(*) FROM public.vital_signs WHERE patient_id = 'P-DHE-001') as vital_measurements,
  (SELECT COUNT(*) FROM public.alerts WHERE patient_id = 'P-DHE-001') as active_alerts;

