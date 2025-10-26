-- Migration: Add form reference columns to alerts table
-- This allows alerts to track which handoff forms have been generated for them

-- Add form_id column to reference the handoff_forms table
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS form_id UUID NULL REFERENCES handoff_forms(id) ON DELETE SET NULL;

-- Add pdf_path column to directly store the PDF file path
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS pdf_path TEXT NULL;

-- Add index for faster lookups of alerts by form_id
CREATE INDEX IF NOT EXISTS idx_alerts_form_id ON alerts(form_id);

-- Add comment to document the columns
COMMENT ON COLUMN alerts.form_id IS 'Reference to the generated handoff form in handoff_forms table';
COMMENT ON COLUMN alerts.pdf_path IS 'Path to the generated PDF file for this alert';

-- Example query to find all alerts with generated forms:
-- SELECT * FROM alerts WHERE form_id IS NOT NULL;

-- Example query to find all alerts without forms:
-- SELECT * FROM alerts WHERE form_id IS NULL AND status = 'active';
