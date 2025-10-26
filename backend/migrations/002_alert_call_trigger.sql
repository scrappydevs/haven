-- Migration: Automatic Alert Call Trigger
-- Triggers Python backend endpoint when critical alert is inserted

-- Function to call backend API when critical alert is created
CREATE OR REPLACE FUNCTION notify_critical_alert()
RETURNS TRIGGER AS $$
DECLARE
  backend_url TEXT;
  request_id BIGINT;
BEGIN
  -- Only trigger for critical alerts
  IF NEW.severity = 'critical' AND NEW.status = 'active' THEN
    
    -- Get backend URL from environment (set via Supabase dashboard)
    -- Default to localhost for development
    backend_url := current_setting('app.backend_url', true);
    IF backend_url IS NULL OR backend_url = '' THEN
      backend_url := 'http://localhost:8000';
    END IF;
    
    -- Call backend endpoint asynchronously using pg_net
    -- This requires pg_net extension (built-in to Supabase)
    SELECT net.http_post(
      url := backend_url || '/api/alerts/call-nurse',
      headers := jsonb_build_object(
        'Content-Type', 'application/json'
      ),
      body := jsonb_build_object(
        'alert_id', NEW.id,
        'patient_id', NEW.patient_id,
        'room_id', NEW.room_id,
        'severity', NEW.severity,
        'title', NEW.title,
        'description', NEW.description,
        'triggered_at', NEW.triggered_at
      )
    ) INTO request_id;
    
    RAISE NOTICE 'Critical alert webhook triggered: alert_id=%, request_id=%', NEW.id, request_id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger that fires AFTER INSERT on alerts table
DROP TRIGGER IF EXISTS trigger_critical_alert_call ON alerts;

CREATE TRIGGER trigger_critical_alert_call
  AFTER INSERT ON alerts
  FOR EACH ROW
  EXECUTE FUNCTION notify_critical_alert();

-- Set backend URL (update this for production)
-- For local development:
-- ALTER DATABASE postgres SET app.backend_url = 'http://localhost:8000';

-- For production (example):
-- ALTER DATABASE postgres SET app.backend_url = 'https://your-backend-url.com';

COMMENT ON FUNCTION notify_critical_alert() IS 'Triggers Python backend to make phone call when critical alert is inserted';
COMMENT ON TRIGGER trigger_critical_alert_call ON alerts IS 'Automatically calls backend API for critical alerts';

