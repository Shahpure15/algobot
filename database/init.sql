-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    hashed_password VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- User API credentials table
CREATE TABLE IF NOT EXISTS user_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    credential_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used TIMESTAMPTZ,
    UNIQUE(user_id, provider, credential_name),  -- Unique name per user per provider
    UNIQUE(api_key, provider)  -- Ensure API keys are unique per provider
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(4) NOT NULL,
    quantity NUMERIC(16,8) NOT NULL,
    price NUMERIC(16,8) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    delta_order_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS connection_status (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    is_connected BOOLEAN DEFAULT FALSE,
    last_check TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create a partial index to handle uniqueness with NULL user_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_connection_status_unique 
ON connection_status (provider, COALESCE(user_id, -1));

-- Insert initial connection status for system-wide connections
INSERT INTO connection_status (provider, is_connected, user_id) 
VALUES ('delta_exchange', FALSE, NULL) 
ON CONFLICT DO NOTHING;

-- Insert default user
INSERT INTO users (username, email, full_name, hashed_password, is_active) 
VALUES ('testuser', 'test@example.com', 'Test User', 'hashed_password', TRUE) 
ON CONFLICT (username) DO NOTHING;

-- Insert default credentials for testuser (update with actual credentials)
INSERT INTO user_credentials (user_id, provider, api_key, api_secret)
SELECT 
    u.id,
    'delta_exchange',
    'your_delta_api_key_here',
    'your_delta_api_secret_here'
FROM users u 
WHERE u.username = 'testuser'
ON CONFLICT (user_id, provider) DO UPDATE SET
    api_key = EXCLUDED.api_key,
    api_secret = EXCLUDED.api_secret;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE INDEX IF NOT EXISTS idx_user_credentials_user_id ON user_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credentials_provider ON user_credentials(provider);

CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_delta_order_id ON trades(delta_order_id);

CREATE INDEX IF NOT EXISTS idx_connection_status_user_id ON connection_status(user_id);

-- Insert default admin user
INSERT INTO users (username, email, full_name, hashed_password) 
VALUES ('admin', 'admin@example.com', 'Administrator', 'hashed_admin123') 
ON CONFLICT (username) DO NOTHING;

-- Insert default test user
INSERT INTO users (username, email, full_name, hashed_password) 
VALUES ('trader', 'trader@example.com', 'Test Trader', 'hashed_trader123') 
ON CONFLICT (username) DO NOTHING;

-- Migration: Add credential_name column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_credentials' 
                   AND column_name = 'credential_name') THEN
        ALTER TABLE user_credentials ADD COLUMN credential_name VARCHAR(100);
        
        -- Update existing records to have a default name
        UPDATE user_credentials 
        SET credential_name = 'Default API Key' 
        WHERE credential_name IS NULL;
        
        -- Now make the column NOT NULL
        ALTER TABLE user_credentials ALTER COLUMN credential_name SET NOT NULL;
        
        -- Drop the old unique constraint and add the new one
        ALTER TABLE user_credentials DROP CONSTRAINT IF EXISTS user_credentials_user_id_provider_key;
        ALTER TABLE user_credentials ADD CONSTRAINT user_credentials_user_id_provider_name_key 
            UNIQUE (user_id, provider, credential_name);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_connection_status_provider ON connection_status(provider);