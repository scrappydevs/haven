-- Migration: Create intake_reports table
-- Run this in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS intake_reports (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Patient identification
    patient_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    livekit_room_name VARCHAR(100),

    -- Interview data
    transcript JSONB NOT NULL DEFAULT '[]'::jsonb,
    chief_complaint TEXT,
    symptoms TEXT[],
    duration VARCHAR(100),
    severity INTEGER CHECK (severity >= 1 AND severity <= 10),
    medications TEXT,
    allergies TEXT,
    prior_episodes TEXT,

    -- Vitals collected during intake
    vitals JSONB DEFAULT '{}'::jsonb,

    -- AI analysis
    urgency_level VARCHAR(20) NOT NULL DEFAULT 'low' CHECK (urgency_level IN ('low', 'medium', 'high')),
    ai_summary TEXT,
    extracted_info JSONB DEFAULT '{}'::jsonb,

    -- Workflow tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'in_review', 'reviewed', 'assigned', 'cancelled')),
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,
    assigned_room VARCHAR(50),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    interview_duration_seconds INTEGER,

    -- Foreign key (optional - depends on your schema)
    CONSTRAINT fk_patient FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_intake_reports_patient_id ON intake_reports(patient_id);
CREATE INDEX IF NOT EXISTS idx_intake_reports_status ON intake_reports(status);
CREATE INDEX IF NOT EXISTS idx_intake_reports_urgency ON intake_reports(urgency_level);
CREATE INDEX IF NOT EXISTS idx_intake_reports_created_at ON intake_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_intake_reports_session_id ON intake_reports(session_id);

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_intake_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_intake_reports_updated_at
    BEFORE UPDATE ON intake_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_intake_reports_updated_at();

-- Row Level Security (RLS) - adjust based on your auth setup
ALTER TABLE intake_reports ENABLE ROW LEVEL SECURITY;

-- Example policy (adjust to your auth requirements)
CREATE POLICY "Healthcare providers can view all intake reports"
    ON intake_reports FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "System can insert intake reports"
    ON intake_reports FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Healthcare providers can update intake reports"
    ON intake_reports FOR UPDATE
    TO authenticated
    USING (true);

-- Comments for documentation
COMMENT ON TABLE intake_reports IS 'Stores patient intake interview data collected by AI agent';
COMMENT ON COLUMN intake_reports.transcript IS 'Array of Q&A pairs from the intake interview';
COMMENT ON COLUMN intake_reports.vitals IS 'Vitals collected during interview (HR, RR, etc.)';
COMMENT ON COLUMN intake_reports.urgency_level IS 'AI-assessed urgency: low, medium, high';
COMMENT ON COLUMN intake_reports.extracted_info IS 'Structured data extracted from conversation';
