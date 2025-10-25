-- Update Dheeraj and David to both be 20 years old
-- Run this in Supabase SQL Editor

UPDATE public.patients
SET 
  age = 20,
  date_of_birth = '2004-03-15',
  updated_at = NOW()
WHERE patient_id = 'P-DHE-001';

UPDATE public.patients
SET 
  age = 20,
  date_of_birth = '2004-07-22',
  updated_at = NOW()
WHERE patient_id = 'P-DAV-001';

-- Verify the changes
SELECT 
  patient_id,
  name,
  age,
  date_of_birth,
  condition
FROM public.patients
WHERE patient_id IN ('P-DHE-001', 'P-DAV-001');

