-- Fix the notify_critical_alert function to handle the http extension properly
-- or replace it with a simpler version that doesn't make HTTP calls

-- Option 1: Drop and recreate the function with proper error handling
CREATE OR REPLACE FUNCTION notify_critical_alert()
RETURNS TRIGGER AS $$
BEGIN
  -- Only proceed if the alert is critical
  IF NEW.severity = 'critical' THEN
    -- Try to make HTTP call, but don't fail if net schema doesn't exist
    BEGIN
      -- This requires the 'http' extension to be enabled
      -- If it fails, the trigger will just skip the notification
      PERFORM http_post(
        'http://your-backend-url/api/alerts/notify',
        jsonb_build_object(
          'alert_id', NEW.id,
          'patient_id', NEW.patient_id,
          'room_id', NEW.room_id,
          'severity', NEW.severity,
          'title', NEW.title,
          'description', NEW.description,
          'triggered_at', NEW.triggered_at
        )::text,
        'application/json'
      );
    EXCEPTION
      WHEN OTHERS THEN
        -- Log the error but don't fail the insert
        RAISE NOTICE 'Failed to send HTTP notification: %', SQLERRM;
    END;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate the triggers
DROP TRIGGER IF EXISTS on_critical_alert_created ON alerts;
DROP TRIGGER IF EXISTS trigger_critical_alert_call ON alerts;

CREATE TRIGGER on_critical_alert_created
  AFTER INSERT ON alerts
  FOR EACH ROW
  EXECUTE FUNCTION notify_critical_alert();
