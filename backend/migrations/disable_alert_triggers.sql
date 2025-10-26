-- Disable alert triggers that require the 'net' schema
-- Run this if you're getting "schema net does not exist" errors

-- Disable the critical alert triggers
DROP TRIGGER IF EXISTS on_critical_alert_created ON alerts;
DROP TRIGGER IF EXISTS trigger_critical_alert_call ON alerts;

-- Optionally: Drop the function if you want to recreate it later
-- DROP FUNCTION IF EXISTS notify_critical_alert();

-- Verify triggers are removed
SELECT
  trigger_name,
  event_manipulation,
  event_object_table
FROM information_schema.triggers
WHERE event_object_table = 'alerts';
