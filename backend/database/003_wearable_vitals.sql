-- Migration: Add wearable vitals table
-- This table stores health data collected from Apple Watch and other wearable devices

CREATE TABLE IF NOT EXISTS wearable_vitals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR NOT NULL,
    device_id VARCHAR NOT NULL,
    device_type VARCHAR NOT NULL DEFAULT 'apple_watch',

    -- Vitals data
    heart_rate INTEGER,
    heart_rate_variability FLOAT,  -- HRV in milliseconds
    spo2 INTEGER,  -- Blood oxygen percentage
    respiratory_rate INTEGER,
    body_temperature FLOAT,  -- Celsius

    -- Metadata
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence FLOAT DEFAULT 1.0,  -- Data quality indicator (0.0-1.0)
    battery_level INTEGER,  -- Device battery percentage
    is_active BOOLEAN DEFAULT true,  -- Currently worn/active

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_heart_rate CHECK (heart_rate BETWEEN 30 AND 220),
    CONSTRAINT valid_spo2 CHECK (spo2 BETWEEN 70 AND 100),
    CONSTRAINT valid_temp CHECK (body_temperature BETWEEN 35.0 AND 42.0),
    CONSTRAINT valid_respiratory_rate CHECK (respiratory_rate BETWEEN 5 AND 60),
    CONSTRAINT valid_hrv CHECK (heart_rate_variability >= 0 AND heart_rate_variability <= 300),
    CONSTRAINT valid_battery CHECK (battery_level BETWEEN 0 AND 100),
    CONSTRAINT valid_confidence CHECK (confidence BETWEEN 0.0 AND 1.0)
);

-- Indexes for fast queries
CREATE INDEX idx_wearable_vitals_patient ON wearable_vitals(patient_id);
CREATE INDEX idx_wearable_vitals_device ON wearable_vitals(device_id);
CREATE INDEX idx_wearable_vitals_timestamp ON wearable_vitals(timestamp DESC);
CREATE INDEX idx_wearable_vitals_patient_timestamp ON wearable_vitals(patient_id, timestamp DESC);

-- Comment for documentation
COMMENT ON TABLE wearable_vitals IS 'Stores real-time health vitals from wearable devices (Apple Watch, etc.)';
COMMENT ON COLUMN wearable_vitals.heart_rate_variability IS 'Heart Rate Variability in milliseconds - indicator of stress/recovery';
COMMENT ON COLUMN wearable_vitals.confidence IS 'Data quality score from 0.0 (low) to 1.0 (high)';
