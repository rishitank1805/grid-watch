-- TimescaleDB schema for smart meter data quality monitoring

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Validated readings table
CREATE TABLE validated_readings (
    time TIMESTAMPTZ NOT NULL,
    meter_id TEXT NOT NULL,
    consumption_kwh DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (time, meter_id)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('validated_readings', 'time');

-- Create index on meter_id for efficient queries
CREATE INDEX idx_validated_readings_meter_id ON validated_readings (meter_id, time DESC);

-- Gap alerts table
CREATE TABLE gap_alerts (
    time TIMESTAMPTZ NOT NULL,
    meter_id TEXT NOT NULL,
    missing_from TIMESTAMPTZ NOT NULL,
    missing_to TIMESTAMPTZ NOT NULL,
    gap_minutes INTEGER NOT NULL,
    PRIMARY KEY (time, meter_id, missing_from)
);

-- Convert to hypertable
SELECT create_hypertable('gap_alerts', 'time');

-- Create index on meter_id
CREATE INDEX idx_gap_alerts_meter_id ON gap_alerts (meter_id, time DESC);

-- Late events table
CREATE TABLE late_events (
    time TIMESTAMPTZ NOT NULL,
    meter_id TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    consumption_kwh DOUBLE PRECISION NOT NULL,
    delay_seconds INTEGER NOT NULL,
    PRIMARY KEY (time, meter_id, event_timestamp)
);

-- Convert to hypertable
SELECT create_hypertable('late_events', 'time');

-- Create index on meter_id
CREATE INDEX idx_late_events_meter_id ON late_events (meter_id, time DESC);

-- Metrics table for aggregated metrics
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_type TEXT NOT NULL,
    meter_id TEXT,
    value DOUBLE PRECISION NOT NULL,
    tags JSONB,
    PRIMARY KEY (time, metric_type, meter_id)
);

-- Convert to hypertable
SELECT create_hypertable('metrics', 'time');

-- Create indexes
CREATE INDEX idx_metrics_type ON metrics (metric_type, time DESC);
CREATE INDEX idx_metrics_meter_id ON metrics (meter_id, time DESC) WHERE meter_id IS NOT NULL;

-- Continuous aggregates for common queries

-- Hourly gap summary
CREATE MATERIALIZED VIEW gap_summary_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    meter_id,
    COUNT(*) AS gap_count,
    SUM(gap_minutes) AS total_gap_minutes,
    AVG(gap_minutes) AS avg_gap_minutes
FROM gap_alerts
GROUP BY hour, meter_id;

-- Add refresh policy (refresh every hour)
SELECT add_continuous_aggregate_policy('gap_summary_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Hourly late events summary
CREATE MATERIALIZED VIEW late_events_summary_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    meter_id,
    COUNT(*) AS late_count,
    AVG(delay_seconds) AS avg_delay_seconds,
    MAX(delay_seconds) AS max_delay_seconds
FROM late_events
GROUP BY hour, meter_id;

-- Add refresh policy
SELECT add_continuous_aggregate_policy('late_events_summary_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- System metrics summary
CREATE MATERIALIZED VIEW metrics_summary_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    metric_type,
    COUNT(*) AS event_count,
    SUM(value) AS total_value,
    AVG(value) AS avg_value
FROM metrics
GROUP BY hour, metric_type;

-- Add refresh policy
SELECT add_continuous_aggregate_policy('metrics_summary_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Helper function to get active meters
CREATE OR REPLACE FUNCTION get_active_meters(hours_back INTEGER DEFAULT 24)
RETURNS TABLE (meter_id TEXT, last_seen TIMESTAMPTZ, reading_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        vr.meter_id,
        MAX(vr.time) AS last_seen,
        COUNT(*) AS reading_count
    FROM validated_readings vr
    WHERE vr.time >= NOW() - (hours_back || ' hours')::INTERVAL
    GROUP BY vr.meter_id
    ORDER BY last_seen DESC;
END;
$$ LANGUAGE plpgsql;

