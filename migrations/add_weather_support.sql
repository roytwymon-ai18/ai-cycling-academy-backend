-- Add weather support to database

-- Add location fields to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS location_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS location_lat DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS location_lon DECIMAL(11, 8),
ADD COLUMN IF NOT EXISTS weather_notifications BOOLEAN DEFAULT TRUE;

-- Create weather_forecasts table
CREATE TABLE IF NOT EXISTS weather_forecasts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    location_lat DECIMAL(10, 8) NOT NULL,
    location_lon DECIMAL(11, 8) NOT NULL,
    forecast_date DATE NOT NULL,
    temp_high INTEGER,
    temp_low INTEGER,
    temp_avg INTEGER,
    conditions VARCHAR(50),
    conditions_emoji VARCHAR(10),
    precipitation_chance INTEGER,
    precipitation_amount DECIMAL(4, 2),
    wind_speed INTEGER,
    wind_direction VARCHAR(10),
    humidity INTEGER,
    is_good_for_outdoor BOOLEAN DEFAULT TRUE,
    fetched_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, forecast_date)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_weather_forecasts_user_date 
ON weather_forecasts(user_id, forecast_date);

-- Create weather_insights table for tracking weather-based adjustments
CREATE TABLE IF NOT EXISTS weather_insights (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workout_id INTEGER REFERENCES planned_workouts(id) ON DELETE CASCADE,
    insight_date DATE NOT NULL,
    insight_type VARCHAR(50),  -- 'rain_warning', 'heat_advisory', 'wind_alert', 'perfect_conditions'
    message TEXT,
    action_taken VARCHAR(100),  -- 'moved_indoor', 'rescheduled', 'intensity_reduced', 'none'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_insights_user 
ON weather_insights(user_id, insight_date);
