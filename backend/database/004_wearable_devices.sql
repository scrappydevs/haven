-- Migration: Add wearable devices table
-- This table manages device pairing and connection status

CREATE TABLE IF NOT EXISTS wearable_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR,
    device_type VARCHAR NOT NULL DEFAULT 'apple_watch',
    device_id VARCHAR UNIQUE NOT NULL,
    device_name VARCHAR,  -- e.g., "John's Apple Watch"

    -- Pairing information
    pairing_code VARCHAR(6),  -- 6-digit numeric code
    pairing_status VARCHAR DEFAULT 'pending',  -- pending, active, disconnected, unpaired
    paired_at TIMESTAMPTZ,
    unpaired_at TIMESTAMPTZ,

    -- Connection status
    last_sync_at TIMESTAMPTZ,
    is_online BOOLEAN DEFAULT false,

    -- Device metadata
    os_version VARCHAR,  -- e.g., "watchOS 10.1"
    model VARCHAR,  -- e.g., "Apple Watch Series 9"

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_wearable_devices_patient ON wearable_devices(patient_id);
CREATE INDEX idx_wearable_devices_status ON wearable_devices(pairing_status);
CREATE UNIQUE INDEX idx_wearable_devices_code ON wearable_devices(pairing_code)
    WHERE pairing_status = 'pending' AND pairing_code IS NOT NULL;

-- Pairing code expiration check (codes expire after 5 minutes)
CREATE OR REPLACE FUNCTION check_pairing_code_expiry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.pairing_status = 'pending' AND
       NEW.created_at < NOW() - INTERVAL '5 minutes' THEN
        NEW.pairing_status := 'expired';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pairing_code_expiry_check
    BEFORE UPDATE ON wearable_devices
    FOR EACH ROW
    EXECUTE FUNCTION check_pairing_code_expiry();

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION update_wearable_devices_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_wearable_devices_timestamp
    BEFORE UPDATE ON wearable_devices
    FOR EACH ROW
    EXECUTE FUNCTION update_wearable_devices_timestamp();

-- Comments
COMMENT ON TABLE wearable_devices IS 'Manages wearable device registration, pairing, and connection status';
COMMENT ON COLUMN wearable_devices.pairing_code IS '6-digit code for device pairing, expires after 5 minutes';
COMMENT ON COLUMN wearable_devices.pairing_status IS 'pending: awaiting pairing, active: paired and usable, disconnected: temporarily offline, unpaired: manually unpaired';
